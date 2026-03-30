from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import logging
import os

from .core.config import settings
from .core.database import init_db
from .api.routes import auth, users, enterprises, experts, regions, members, dockings, vouchers, dashboard

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing database...")
    await init_db()
    # Seed admin user if not exists
    await seed_admin()
    logger.info("Application started successfully")
    yield
    logger.info("Application shutdown")


async def seed_admin():
    from .core.database import AsyncSessionLocal
    from .core.security import get_password_hash
    from .models.user import User
    from sqlalchemy import select
    import uuid

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.username == "admin"))
        if not result.scalar_one_or_none():
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
            logger.info("Admin user created: admin / Admin@123")


app = FastAPI(
    title=settings.APP_NAME,
    description="商协会数字化产融对接平台API服务",
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global error handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"code": 500, "message": "服务器内部错误，请联系技术支持"}
    )

# Unified response wrapper middleware
@app.middleware("http")
async def response_wrapper(request: Request, call_next):
    response = await call_next(request)
    return response

# Register routers
prefix = "/api/v1"
app.include_router(auth.router, prefix=prefix)
app.include_router(users.router, prefix=prefix)
app.include_router(enterprises.router, prefix=prefix)
app.include_router(experts.router, prefix=prefix)
app.include_router(regions.router, prefix=prefix)
app.include_router(members.router, prefix=prefix)
app.include_router(dockings.router, prefix=prefix)
app.include_router(vouchers.router, prefix=prefix)
app.include_router(dashboard.router, prefix=prefix)


@app.get("/api/health", tags=["系统"])
async def health_check():
    return {"status": "healthy", "version": settings.APP_VERSION, "name": settings.APP_NAME}


# ── Serve React frontend static files ─────────────────────────────────────
_THIS_DIR = os.path.dirname(os.path.realpath(__file__))  # .../backend/app
_DIST = os.path.abspath(os.path.join(_THIS_DIR, "..", "..", "frontend", "dist"))

if os.path.isdir(_DIST):
    # Serve static assets (JS/CSS/images)
    app.mount("/assets", StaticFiles(directory=os.path.join(_DIST, "assets")), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        """Catch-all: serve index.html for SPA routing."""
        file_path = os.path.join(_DIST, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(_DIST, "index.html"))
else:
    logger.warning(f"Frontend dist not found at {_DIST}, skipping static file serving")
