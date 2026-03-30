-- ============================================================
-- 商协会数字化产融对接平台（产融分）数据库初始化脚本
-- 适用数据库：PostgreSQL 15+ / SQLite 3+
-- 版本：V1.0  日期：2026-03-30
-- ============================================================

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id            VARCHAR(36)   PRIMARY KEY,
    username      VARCHAR(50)   NOT NULL UNIQUE,
    email         VARCHAR(100)  UNIQUE,
    phone         VARCHAR(20)   UNIQUE,
    password_hash VARCHAR(60)   NOT NULL,
    role          VARCHAR(20)   NOT NULL DEFAULT 'enterprise',
    real_name     VARCHAR(50),
    avatar_url    VARCHAR(500),
    status        INTEGER       NOT NULL DEFAULT 1,
    last_login_at TIMESTAMP,
    created_at    TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_deleted    BOOLEAN       NOT NULL DEFAULT FALSE
);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- 企业表
CREATE TABLE IF NOT EXISTS enterprises (
    id                  VARCHAR(36)   PRIMARY KEY,
    name                VARCHAR(200)  NOT NULL,
    unified_code        VARCHAR(20)   UNIQUE,
    legal_person        VARCHAR(50),
    registered_capital  DECIMAL(15,2),
    industry            VARCHAR(50),
    province            VARCHAR(20),
    city                VARCHAR(20),
    founded_year        SMALLINT,
    employee_count      INTEGER,
    description         VARCHAR(2000),
    total_score         DECIMAL(6,1)  NOT NULL DEFAULT 0,
    operation_score     DECIMAL(5,1)  NOT NULL DEFAULT 0,
    innovation_score    DECIMAL(5,1)  NOT NULL DEFAULT 0,
    credit_score        DECIMAL(5,1)  NOT NULL DEFAULT 0,
    growth_score        DECIMAL(5,1)  NOT NULL DEFAULT 0,
    score_updated_at    TIMESTAMP,
    user_id             VARCHAR(36)   REFERENCES users(id),
    status              INTEGER       NOT NULL DEFAULT 2,
    created_at          TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_deleted          BOOLEAN       NOT NULL DEFAULT FALSE
);
CREATE INDEX IF NOT EXISTS idx_enterprises_score ON enterprises(total_score DESC);
CREATE INDEX IF NOT EXISTS idx_enterprises_province ON enterprises(province);
CREATE INDEX IF NOT EXISTS idx_enterprises_industry ON enterprises(industry);

-- 专家表
CREATE TABLE IF NOT EXISTS experts (
    id                  VARCHAR(36)   PRIMARY KEY,
    name                VARCHAR(50)   NOT NULL,
    title               VARCHAR(200),
    domain              VARCHAR(100),
    institution         VARCHAR(200),
    bio                 VARCHAR(2000),
    capability_score    DECIMAL(5,1)  NOT NULL DEFAULT 0,
    adaptability_score  DECIMAL(5,1)  NOT NULL DEFAULT 0,
    willingness_score   DECIMAL(5,1)  NOT NULL DEFAULT 0,
    total_score         DECIMAL(5,1)  NOT NULL DEFAULT 0,
    grade               VARCHAR(5),
    user_id             VARCHAR(36)   REFERENCES users(id),
    status              INTEGER       NOT NULL DEFAULT 2,
    created_at          TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_deleted          BOOLEAN       NOT NULL DEFAULT FALSE
);
CREATE INDEX IF NOT EXISTS idx_experts_score ON experts(total_score DESC);
CREATE INDEX IF NOT EXISTS idx_experts_domain ON experts(domain);

-- 会员贡献表
CREATE TABLE IF NOT EXISTS member_contributions (
    id            VARCHAR(36)   PRIMARY KEY,
    enterprise_id VARCHAR(36)   NOT NULL REFERENCES enterprises(id),
    action_type   VARCHAR(50)   NOT NULL,
    action_detail VARCHAR(500),
    score_earned  DECIMAL(6,1)  NOT NULL,
    action_date   DATE          NOT NULL,
    verified_by   VARCHAR(36)   REFERENCES users(id),
    remark        VARCHAR(500),
    created_at    TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_contributions_enterprise ON member_contributions(enterprise_id);
CREATE INDEX IF NOT EXISTS idx_contributions_date ON member_contributions(action_date);

-- 区域需求表
CREATE TABLE IF NOT EXISTS regions (
    id             VARCHAR(36)   PRIMARY KEY,
    name           VARCHAR(100)  NOT NULL,
    province       VARCHAR(20)   NOT NULL,
    city           VARCHAR(20),
    industry_focus TEXT,
    scale_require  VARCHAR(50),
    tech_require   VARCHAR(200),
    finance_scale  VARCHAR(100),
    credit_require DECIMAL(5,1)  NOT NULL DEFAULT 0,
    contact_person VARCHAR(50),
    contact_phone  VARCHAR(20),
    status         INTEGER       NOT NULL DEFAULT 1,
    expire_date    DATE,
    user_id        VARCHAR(36)   REFERENCES users(id),
    created_at     TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at     TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_deleted     BOOLEAN       NOT NULL DEFAULT FALSE
);
CREATE INDEX IF NOT EXISTS idx_regions_province ON regions(province);

-- 对接申请表
CREATE TABLE IF NOT EXISTS dockings (
    id            VARCHAR(36)   PRIMARY KEY,
    type          VARCHAR(20)   NOT NULL,
    initiator_id  VARCHAR(36)   NOT NULL,
    target_id     VARCHAR(36)   NOT NULL,
    title         VARCHAR(200)  NOT NULL,
    description   TEXT,
    match_score   DECIMAL(5,1)  NOT NULL DEFAULT 0,
    status        VARCHAR(20)   NOT NULL DEFAULT 'draft',
    result        TEXT,
    apply_date    DATE,
    complete_date DATE,
    reviewer_id   VARCHAR(36)   REFERENCES users(id),
    remark        VARCHAR(500),
    created_at    TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_dockings_status ON dockings(status);
CREATE INDEX IF NOT EXISTS idx_dockings_initiator ON dockings(initiator_id);
CREATE INDEX IF NOT EXISTS idx_dockings_type ON dockings(type);

-- 凭证文件表
CREATE TABLE IF NOT EXISTS vouchers (
    id             VARCHAR(36)   PRIMARY KEY,
    entity_type    VARCHAR(20)   NOT NULL,
    entity_id      VARCHAR(36)   NOT NULL,
    score_dim      VARCHAR(50)   NOT NULL,
    file_name      VARCHAR(200)  NOT NULL,
    file_path      VARCHAR(500)  NOT NULL,
    file_size      INTEGER,
    file_type      VARCHAR(20),
    status         INTEGER       NOT NULL DEFAULT 0,
    review_comment VARCHAR(500),
    reviewer_id    VARCHAR(36)   REFERENCES users(id),
    reviewed_at    TIMESTAMP,
    uploaded_by    VARCHAR(36)   NOT NULL REFERENCES users(id),
    created_at     TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_vouchers_entity ON vouchers(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_vouchers_status ON vouchers(status);

-- 审计日志表
CREATE TABLE IF NOT EXISTS audit_logs (
    id            VARCHAR(36)   PRIMARY KEY,
    user_id       VARCHAR(36),
    action        VARCHAR(100)  NOT NULL,
    resource_type VARCHAR(50),
    resource_id   VARCHAR(36),
    detail        TEXT,
    ip_address    VARCHAR(50),
    created_at    TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_time ON audit_logs(created_at DESC);

-- ============================================================
-- 初始化数据
-- ============================================================
-- 默认超级管理员账号：admin / Admin@123
-- password_hash 对应 bcrypt("Admin@123")
INSERT OR IGNORE INTO users (id, username, password_hash, role, real_name, status, created_at, updated_at)
VALUES (
    '00000000-0000-0000-0000-000000000001',
    'admin',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj8thkHJHnAe',
    'admin',
    '超级管理员',
    1,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);

-- 示例区域需求
INSERT OR IGNORE INTO regions (id, name, province, city, industry_focus, scale_require, finance_scale, credit_require, status, created_at, updated_at)
VALUES
    ('r0000001-0000-0000-0000-000000000001', '深圳新能源产业基地', '广东省', '深圳市', '["新能源","智能制造"]', '中大型企业', '5000万-5亿', 100, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('r0000001-0000-0000-0000-000000000002', '苏州智能制造园区', '江苏省', '苏州市', '["智能制造","半导体"]', '中型企业', '1000万-1亿', 80, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('r0000001-0000-0000-0000-000000000003', '成都生物医药产业园', '四川省', '成都市', '["生物医药","医疗器械"]', '各类规模', '500万-5000万', 60, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);
