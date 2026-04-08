@echo off
chcp 65001 >nul
setlocal

title 智能报销系统-前端
cd /d "%~dp0frontend"

echo [前端] 正在启动 Vite 开发服务...
echo [前端] 地址: http://127.0.0.1:5173/
echo.

where npm.cmd >nul 2>nul
if errorlevel 1 (
  echo [错误] 未找到 npm.cmd，请先安装 Node.js。
  pause
  exit /b 1
)

npm.cmd run dev -- --host 127.0.0.1 --port 5173

echo.
echo [前端] 服务已退出。
pause
