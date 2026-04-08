@echo off
chcp 65001 >nul
setlocal

title 智能报销系统-后端
cd /d "%~dp0backend\finance_reimbursement"

echo [后端] 正在启动 Django 服务...
echo [后端] 地址: http://127.0.0.1:8000/
echo.

if not exist "..\..\.venv\Scripts\python.exe" (
  echo [错误] 未找到 Python 虚拟环境: ..\..\.venv\Scripts\python.exe
  echo [提示] 请先在项目根目录创建 .venv 并安装依赖。
  pause
  exit /b 1
)

"..\..\.venv\Scripts\python.exe" manage.py runserver 127.0.0.1:8000

echo.
echo [后端] 服务已退出。
pause
