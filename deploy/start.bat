@echo off
chcp 65001 > nul
echo ================================================
echo   商协会数字化产融对接平台（产融分）Windows启动
echo ================================================

set PLATFORM_DIR=%~dp0..
set BACKEND_DIR=%PLATFORM_DIR%\backend
set FRONTEND_DIR=%PLATFORM_DIR%\frontend

echo [1/3] 安装后端依赖...
cd /d "%BACKEND_DIR%"
pip install -r requirements.txt -q
if %errorlevel% neq 0 (echo [ERROR] 后端依赖安装失败 & pause & exit /b 1)

echo [2/3] 启动后端服务 (http://localhost:8000)...
cd /d "%BACKEND_DIR%"
if not exist uploads mkdir uploads
start "产融分-后端" cmd /k "python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
timeout /t 3 /nobreak > nul

echo [3/3] 启动前端服务 (http://localhost:5173)...
cd /d "%FRONTEND_DIR%"
start "产融分-前端" cmd /k "npm run dev"

echo.
echo ================================================
echo   平台启动完成！
echo   前端访问：http://localhost:5173
echo   后端API文档：http://localhost:8000/api/docs
echo   默认账号：admin / Admin@123
echo ================================================
pause
