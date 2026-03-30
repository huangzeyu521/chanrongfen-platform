#!/bin/bash
# 产融分平台 - 本地快速启动脚本（无Docker，直接运行）

set -e
PLATFORM_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND_DIR="$PLATFORM_DIR/backend"
FRONTEND_DIR="$PLATFORM_DIR/frontend"

echo "================================================"
echo "  商协会数字化产融对接平台（产融分）启动脚本"
echo "================================================"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python3 未安装，请先安装 Python 3.11+"
    exit 1
fi

# Check Node
if ! command -v node &> /dev/null; then
    echo "[ERROR] Node.js 未安装，请先安装 Node.js 18+"
    exit 1
fi

echo "[1/4] 安装后端依赖..."
cd "$BACKEND_DIR"
pip install -r requirements.txt -q

echo "[2/4] 安装前端依赖..."
cd "$FRONTEND_DIR"
npm install -q

echo "[3/4] 启动后端服务 (http://localhost:8000)..."
cd "$BACKEND_DIR"
mkdir -p uploads
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
echo "  后端PID: $BACKEND_PID"
sleep 3

echo "[4/4] 启动前端开发服务 (http://localhost:5173)..."
cd "$FRONTEND_DIR"
npm run dev &
FRONTEND_PID=$!
echo "  前端PID: $FRONTEND_PID"

echo ""
echo "================================================"
echo "  平台启动完成！"
echo "  前端访问：http://localhost:5173"
echo "  后端API：http://localhost:8000/api/docs"
echo "  默认账号：admin / Admin@123"
echo "================================================"
echo ""
echo "按 Ctrl+C 停止所有服务..."

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo '服务已停止'" INT TERM
wait
