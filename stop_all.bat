@echo off
echo ========================================
echo   DocAgent 项目停止脚本
echo ========================================
echo.

echo [1/4] 停止后端服务 (端口 8000)...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000') do (
    taskkill /F /PID %%a 2>nul
    if %errorlevel% equ 0 echo 已停止进程 %%a
)

echo.
echo [2/4] 停止前端服务 (端口 5173)...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5173') do (
    taskkill /F /PID %%a 2>nul
    if %errorlevel% equ 0 echo 已停止进程 %%a
)

echo.
echo [3/4] 停止 Celery Worker...
taskkill /F /IM celery.exe 2>nul
if %errorlevel% equ 0 (
    echo Celery Worker 已停止 ✓
) else (
    echo Celery Worker 未运行
)

echo.
echo [4/4] 停止 Python 进程...
taskkill /F /FI "WINDOWTITLE eq DocAgent*" 2>nul

echo.
echo ========================================
echo   所有服务已停止！
echo ========================================
echo.
pause

