@echo off
echo ========================================
echo   DocAgent 项目启动脚本
echo ========================================
echo.

REM 检查端口占用
echo [1/5] 检查端口占用...
netstat -ano | findstr :8000 >nul
if %errorlevel% equ 0 (
    echo 警告: 端口 8000 已被占用，正在清理...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000') do taskkill /F /PID %%a 2>nul
)

netstat -ano | findstr :5173 >nul
if %errorlevel% equ 0 (
    echo 警告: 端口 5173 已被占用，正在清理...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5173') do taskkill /F /PID %%a 2>nul
)

echo.
echo [2/5] 检查 Redis 服务...
redis-cli ping >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: Redis 未运行，请先启动 Redis!
    echo 提示: 运行 redis-server 启动 Redis
    pause
    exit /b 1
)
echo Redis 运行正常 ✓

echo.
echo [3/5] 检查 PostgreSQL 服务...
pg_isready -h localhost -p 5432 >nul 2>&1
if %errorlevel% neq 0 (
    echo 警告: PostgreSQL 可能未运行
    echo 提示: 请确保 PostgreSQL 服务已启动
)

echo.
echo [4/5] 启动后端服务...
cd backend
start "DocAgent Backend" cmd /k "python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
timeout /t 3 >nul

echo.
echo [5/5] 启动 Celery Worker...
start "Celery Worker" cmd /k "celery -A app.tasks.celery_app worker --loglevel=info --pool=solo"
timeout /t 2 >nul

echo.
echo 启动 Celery Beat (定时任务)...
start "Celery Beat" cmd /k "celery -A app.tasks.celery_app beat --loglevel=info"
timeout /t 2 >nul

cd ..

echo.
echo [6/6] 启动前端服务...
cd frontend
start "DocAgent Frontend" cmd /k "npm run dev"

cd ..

echo.
echo ========================================
echo   所有服务已启动！
echo ========================================
echo.
echo 后端地址: http://localhost:8000
echo API文档: http://localhost:8000/docs
echo 前端地址: http://localhost:5173
echo.
echo 按任意键打开浏览器...
pause >nul

start http://localhost:5173

echo.
echo 提示: 关闭此窗口不会停止服务
echo 要停止所有服务，请运行 stop_all.bat
echo.
pause

