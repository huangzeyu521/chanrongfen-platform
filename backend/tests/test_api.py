"""
Automated integration tests for the 产融分 Platform API.
conftest.py sets DATABASE_URL env var before these imports.
"""
import pytest
import asyncio
import warnings
import os
import uuid
warnings.filterwarnings("ignore")

from httpx import AsyncClient, ASGITransport

from app.main import app
from app.core.database import init_db, engine, Base, AsyncSessionLocal
from app.core.security import get_password_hash
from app.models.user import User


# ── Test DB setup ─────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
async def setup_db():
    """Initialize test DB and seed admin user."""
    await init_db()
    # Manually seed admin
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select
        existing = (await db.execute(
            select(User).where(User.username == "admin")
        )).scalar_one_or_none()
        if not existing:
            admin = User(
                id=str(uuid.uuid4()),
                username="admin",
                password_hash=get_password_hash("Admin@123"),
                role="admin",
                real_name="超级管理员",
                status=1
            )
            db.add(admin)
            await db.commit()
    yield
    # Teardown
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()
    db_file = "./test_crf.db"
    if os.path.exists(db_file):
        os.remove(db_file)


@pytest.fixture(scope="session")
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as c:
        yield c


@pytest.fixture(scope="session")
async def admin_token(client):
    resp = await client.post("/api/v1/auth/login", json={
        "username": "admin", "password": "Admin@123"
    })
    assert resp.status_code == 200, f"Admin login failed: {resp.text}"
    return resp.json()["access_token"]


# ── Health Check ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_health_check(client):
    resp = await client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    print(f"\n  ✓ Health check OK: {data}")


# ── Authentication Tests ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_login_success(client):
    resp = await client.post("/api/v1/auth/login", json={
        "username": "admin", "password": "Admin@123"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["role"] == "admin"
    print("\n  ✓ Login success")


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    resp = await client.post("/api/v1/auth/login", json={
        "username": "admin", "password": "wrongpass"
    })
    assert resp.status_code == 401
    print("\n  ✓ Wrong password rejected (401)")


@pytest.mark.asyncio
async def test_token_refresh(client):
    resp = await client.post("/api/v1/auth/login", json={
        "username": "admin", "password": "Admin@123"
    })
    refresh_token = resp.json()["refresh_token"]
    resp2 = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert resp2.status_code == 200
    assert "access_token" in resp2.json()
    print("\n  ✓ Token refresh OK")


@pytest.mark.asyncio
async def test_no_auth_rejected(client):
    resp = await client.get("/api/v1/users/me")
    assert resp.status_code in (401, 403)
    print("\n  ✓ Unauthenticated request rejected")


# ── User Management ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_me(client, admin_token):
    resp = await client.get("/api/v1/users/me",
                            headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    assert resp.json()["username"] == "admin"
    print("\n  ✓ Get /me OK")


@pytest.mark.asyncio
async def test_create_user(client, admin_token):
    resp = await client.post("/api/v1/users",
        json={"username": "entuser01", "password": "Test@12345",
              "role": "enterprise", "real_name": "企业用户01"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert resp.status_code == 201
    assert resp.json()["role"] == "enterprise"
    print("\n  ✓ Create user OK")


@pytest.mark.asyncio
async def test_create_duplicate_user(client, admin_token):
    # First create
    await client.post("/api/v1/users",
        json={"username": "dup_user", "password": "xx", "role": "enterprise"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    # Second create same username → 409
    resp = await client.post("/api/v1/users",
        json={"username": "dup_user", "password": "xx", "role": "enterprise"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert resp.status_code == 409
    print("\n  ✓ Duplicate user → 409 Conflict")


@pytest.mark.asyncio
async def test_list_users(client, admin_token):
    resp = await client.get("/api/v1/users",
                            headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    print(f"\n  ✓ List users: {data['total']} found")


# ── Enterprise Tests ─────────────────────────────────────────────────────

@pytest.fixture(scope="session")
async def ent_id(client, admin_token):
    resp = await client.post("/api/v1/enterprises",
        json={"name": "测试新能源有限公司", "unified_code": "91110000ABCDE12345",
              "industry": "新能源", "province": "广东省", "city": "深圳市",
              "employee_count": 300},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert resp.status_code == 201
    return resp.json()["id"]


@pytest.mark.asyncio
async def test_create_enterprise(client, admin_token):
    resp = await client.post("/api/v1/enterprises",
        json={"name": "智能制造科技公司", "industry": "智能制造",
              "province": "江苏省", "employee_count": 100},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert resp.status_code == 201
    assert resp.json()["total_score"] == 0.0
    print("\n  ✓ Create enterprise OK")


@pytest.mark.asyncio
async def test_list_enterprises(client, admin_token):
    resp = await client.get("/api/v1/enterprises",
                            headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    assert "total" in resp.json()
    print(f"\n  ✓ List enterprises: {resp.json()['total']} found")


@pytest.mark.asyncio
async def test_enterprise_score_update(client, admin_token, ent_id):
    resp = await client.post(f"/api/v1/enterprises/{ent_id}/score",
        json={"operation_score": 300.0, "innovation_score": 200.0,
              "credit_score": 150.0, "growth_score": 80.0},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert resp.status_code == 200
    assert resp.json()["total_score"] == 730.0
    print(f"\n  ✓ Enterprise score: 730.0 pts")


@pytest.mark.asyncio
async def test_enterprise_score_get(client, admin_token, ent_id):
    resp = await client.get(f"/api/v1/enterprises/{ent_id}/score",
                            headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_score"] == 730.0
    assert data["grade"] == "A"
    print(f"\n  ✓ Enterprise score grade: {data['grade']}")


@pytest.mark.asyncio
async def test_enterprise_score_range_validation(client, admin_token, ent_id):
    resp = await client.post(f"/api/v1/enterprises/{ent_id}/score",
        json={"operation_score": 999.0},  # Max is 400
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert resp.status_code == 422
    print("\n  ✓ Score out-of-range → 422")


@pytest.mark.asyncio
async def test_enterprise_not_found(client, admin_token):
    resp = await client.get("/api/v1/enterprises/nonexistent-id",
                            headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 404
    print("\n  ✓ Enterprise not found → 404")


# ── Expert Tests ─────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
async def expert_id(client, admin_token):
    resp = await client.post("/api/v1/experts",
        json={"name": "李院士", "title": "中科院院士",
              "domain": "新能源", "institution": "中科院"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert resp.status_code == 201
    return resp.json()["id"]


@pytest.mark.asyncio
async def test_create_expert(client, admin_token):
    resp = await client.post("/api/v1/experts",
        json={"name": "王教授", "domain": "智能制造"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert resp.status_code == 201
    print("\n  ✓ Create expert OK")


@pytest.mark.asyncio
async def test_expert_score(client, admin_token, expert_id):
    resp = await client.post(f"/api/v1/experts/{expert_id}/score",
        json={"capability_score": 420.0, "adaptability_score": 240.0,
              "willingness_score": 160.0},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_score"] == 820.0
    assert data["grade"] == "S"
    print(f"\n  ✓ Expert score: {data['total_score']} grade={data['grade']}")


@pytest.mark.asyncio
async def test_list_experts(client, admin_token):
    resp = await client.get("/api/v1/experts",
                            headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    print(f"\n  ✓ List experts: {resp.json()['total']} found")


# ── Region Tests ─────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
async def region_id(client, admin_token):
    resp = await client.post("/api/v1/regions",
        json={"name": "深圳新能源产业基地", "province": "广东省",
              "city": "深圳市", "industry_focus": '["新能源","智能制造"]',
              "credit_require": 100.0, "finance_scale": "5000万-5亿"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert resp.status_code == 201
    return resp.json()["id"]


@pytest.mark.asyncio
async def test_create_region(client, admin_token):
    resp = await client.post("/api/v1/regions",
        json={"name": "苏州智能制造园", "province": "江苏省"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert resp.status_code == 201
    print("\n  ✓ Create region OK")


@pytest.mark.asyncio
async def test_region_match(client, admin_token, region_id, ent_id):
    resp = await client.get(f"/api/v1/regions/{region_id}/match",
        params={"enterprise_id": ent_id},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert 0 <= data["match_score"] <= 100
    assert data["match_grade"] in ("S", "A", "B", "C", "D")
    print(f"\n  ✓ Region match: {data['match_score']} grade={data['match_grade']}")


@pytest.mark.asyncio
async def test_region_top_enterprises(client, admin_token, region_id):
    resp = await client.get(f"/api/v1/regions/{region_id}/top-enterprises",
        params={"top_n": 5},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
    print(f"\n  ✓ Top enterprises for region: {len(resp.json())} results")


# ── Member Contribution Tests ────────────────────────────────────────────

@pytest.mark.asyncio
async def test_record_contribution(client, admin_token, ent_id):
    resp = await client.post("/api/v1/members/contribution/record",
        json={"enterprise_id": ent_id, "action_type": "fee_paid",
              "action_detail": "2026年度会费", "score_earned": 20.0,
              "action_date": "2026-01-15"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert resp.status_code == 200
    assert "id" in resp.json()
    print("\n  ✓ Record contribution OK")


@pytest.mark.asyncio
async def test_get_contribution_score(client, admin_token, ent_id):
    resp = await client.get(f"/api/v1/members/{ent_id}/contribution",
                            headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_contribution_score"] >= 20.0
    assert data["grade"] in ("S", "A", "B", "C")
    assert "rights" in data
    print(f"\n  ✓ Contribution score: {data['total_contribution_score']} grade={data['grade']}")


@pytest.mark.asyncio
async def test_contribution_leaderboard(client, admin_token):
    resp = await client.get("/api/v1/members/contribution/leaderboard",
        params={"top_n": 5},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
    print(f"\n  ✓ Leaderboard: {len(resp.json())} entries")


# ── Docking Tests ────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
async def docking_id(client, admin_token, ent_id, region_id):
    resp = await client.post("/api/v1/dockings",
        json={"type": "ENT_GOV", "initiator_id": ent_id,
              "target_id": region_id, "title": "新能源产融对接申请",
              "match_score": 85.0, "apply_date": "2026-03-01"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert resp.status_code == 201
    return resp.json()["id"]


@pytest.mark.asyncio
async def test_create_docking(client, admin_token, ent_id, region_id):
    resp = await client.post("/api/v1/dockings",
        json={"type": "ENT_GOV", "initiator_id": ent_id,
              "target_id": region_id, "title": "测试对接"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert resp.status_code == 201
    assert resp.json()["status"] == "draft"
    print("\n  ✓ Create docking OK")


@pytest.mark.asyncio
async def test_invalid_docking_type(client, admin_token):
    resp = await client.post("/api/v1/dockings",
        json={"type": "BAD_TYPE", "initiator_id": "x",
              "target_id": "y", "title": "test"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert resp.status_code == 422
    print("\n  ✓ Invalid docking type → 422")


@pytest.mark.asyncio
async def test_update_docking_status(client, admin_token, docking_id):
    resp = await client.patch(f"/api/v1/dockings/{docking_id}/status",
        json={"status": "submitted", "remark": "已提交"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "submitted"
    print("\n  ✓ Docking status update OK")


@pytest.mark.asyncio
async def test_complete_docking(client, admin_token, docking_id):
    resp = await client.patch(f"/api/v1/dockings/{docking_id}/status",
        json={"status": "completed", "result": "对接成功，达成合作意向"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "completed"
    print("\n  ✓ Docking completed OK")


@pytest.mark.asyncio
async def test_list_dockings(client, admin_token):
    resp = await client.get("/api/v1/dockings",
                            headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    print(f"\n  ✓ List dockings: {data['total']} found")


# ── Dashboard Tests ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_dashboard_overview(client, admin_token):
    resp = await client.get("/api/v1/dashboard/overview",
                            headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    data = resp.json()
    required_keys = ["total_enterprises", "total_experts", "total_dockings",
                     "docking_success_rate", "avg_enterprise_score"]
    for k in required_keys:
        assert k in data, f"Missing key: {k}"
    print(f"\n  ✓ Dashboard overview: {data}")


@pytest.mark.asyncio
async def test_score_distribution(client, admin_token):
    resp = await client.get("/api/v1/dashboard/score-distribution",
                            headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 5
    total = sum(d["count"] for d in data)
    assert total >= 0
    print(f"\n  ✓ Score distribution: {data}")


@pytest.mark.asyncio
async def test_docking_trends(client, admin_token):
    resp = await client.get("/api/v1/dashboard/docking-trends",
                            headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
    print(f"\n  ✓ Docking trends: {len(resp.json())} months")


@pytest.mark.asyncio
async def test_top_enterprises_dashboard(client, admin_token):
    resp = await client.get("/api/v1/dashboard/top-enterprises",
                            headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    if len(data) > 0:
        assert "rank" in data[0]
        assert "total_score" in data[0]
    print(f"\n  ✓ Top enterprises: {len(data)} returned")
