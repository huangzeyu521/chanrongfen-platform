# 商协会数字化产融对接平台（产融分）

## 项目概述

本平台是基于《商协会数字化产融对接平台产品设计文档》全栈开发的数字化产融对接管理系统，实现商协会可信产融对接评分（产融分）的核心功能。

## 功能模块

| 模块 | 版本 | 功能说明 |
|------|------|---------|
| 企业价值评分 | 1.0 | 经营/创新/信用/发展四维度量化评分，满分1000分 |
| 区域产融适配 | 1.0 | 企业与目标区域智能匹配，输出匹配得分与等级 |
| 会员贡献评分 | 1.0 | 多维度贡献量化，与展示权重/评优资格挂钩 |
| 专家三维评分 | 2.0 | 专业能力/适配度/意愿度三维评分，给出对接规格建议 |
| 对接流程管理 | 1.0 | 企业-政府/企业-金融/专家-政府全流程线上对接 |
| 数据看板      | 1.0 | 平台运营数据实时统计与可视化 |
| 凭证管理      | 1.0 | 凭证上传、审核、存储全流程管理 |

## 技术栈

- **后端**：Python 3.11 + FastAPI 0.109 + SQLAlchemy 2.0 + SQLite/PostgreSQL
- **前端**：React 18 + Vite 5 + Ant Design 5 + Recharts
- **认证**：JWT Token（Access Token 2h + Refresh Token 7d）
- **部署**：Docker + Docker Compose + Nginx

## 快速启动

### 方式一：Windows 一键启动
```
双击 deploy/start.bat
```

### 方式二：手动启动

**后端**
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**前端**
```bash
cd frontend
npm install
npm run dev
```

### 方式三：Docker Compose
```bash
cd deploy
docker-compose up -d
```

## 访问地址

| 地址 | 说明 |
|------|------|
| http://localhost:5173 | 前端应用（开发模式） |
| http://localhost:8000/api/docs | Swagger API文档 |
| http://localhost:8000/api/health | 健康检查接口 |

## 默认账号

| 用户名 | 密码 | 角色 |
|--------|------|------|
| admin | Admin@123 | 超级管理员 |

## 目录结构

```
platform/
├── backend/               # Python FastAPI 后端
│   ├── app/
│   │   ├── api/routes/    # API路由（auth/users/enterprises/experts/...）
│   │   ├── core/          # 核心配置（config/database/security）
│   │   └── models/        # 数据库模型
│   ├── tests/             # 自动化测试（33个用例，100%通过）
│   ├── requirements.txt   # Python依赖
│   └── Dockerfile
├── frontend/              # React + Vite 前端
│   ├── src/
│   │   ├── pages/         # 页面组件（Dashboard/Enterprise/Expert/...）
│   │   ├── components/    # 公共组件（Layout等）
│   │   ├── services/      # API调用封装
│   │   └── store/         # Zustand状态管理
│   ├── dist/              # 生产构建产物
│   └── Dockerfile
├── db/
│   └── init.sql           # 数据库初始化脚本
├── deploy/
│   ├── docker-compose.yml # Docker Compose部署配置
│   ├── start.bat          # Windows一键启动
│   └── start.sh           # Linux/Mac一键启动
└── README.md
```

## API接口文档

启动后端后访问 http://localhost:8000/api/docs 查看完整的Swagger交互式文档。

## 测试

```bash
cd backend
pytest tests/test_api.py -v
# 33 passed in 3.5s
```

## 安全说明

- 密码使用 bcrypt 哈希存储
- API 全部使用 JWT Token 认证
- 生产部署请修改 `SECRET_KEY` 环境变量
- 支持 HTTPS/TLS（通过Nginx配置）
