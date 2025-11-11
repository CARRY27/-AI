@echo off
echo ========================================
echo   DocAgent 项目重启脚本
echo ========================================
echo.

echo 正在停止所有服务...
call stop_all.bat

echo.
echo 等待 3 秒后重新启动...
timeout /t 3 >nul

echo.
echo 正在启动所有服务...
call start_all.bat

