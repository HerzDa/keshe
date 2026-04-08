@echo off
chcp 65001 >nul
setlocal

title 智能报销系统-一键启动
cd /d "%~dp0"

echo 正在分别启动后端与前端窗口...
echo.

start "后端-Django" cmd /k "cd /d "%~dp0backend\finance_reimbursement" && ..\..\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000"
start "前端-Vite" cmd /k "cd /d "%~dp0frontend" && npm.cmd run dev -- --host 127.0.0.1 --port 5173"

echo 启动命令已发送。
echo 前端: http://127.0.0.1:5173/
echo 后端: http://127.0.0.1:8000/
echo.
pause
