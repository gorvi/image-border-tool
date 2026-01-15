@echo off
chcp 65001 >nul
echo ====================================
echo   图片套版工具 - 安全启动 (Windows)
echo ====================================

cd /d "%~dp0"

:: 检查是否安装 Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到 Python。请先安装 Python 3.10+ 并添加到 PATH。
    pause
    exit /b
)

:: 检查虚拟环境
echo 检查虚拟环境...
if not exist ".venv" (
    echo 创建虚拟环境...
    python -m venv .venv
)

:: 激活虚拟环境
echo 激活虚拟环境...
if not exist ".venv\Scripts\activate.bat" (
    echo [错误] 虚拟环境创建失败或路径不正确。.venv\Scripts\activate.bat 不存在。
    pause
    exit /b
)
call .venv\Scripts\activate.bat

:: 安装依赖
echo 检查依赖...
pip install -r requirements.txt

:: 启动程序
echo 启动程序...
python main.py

if %errorlevel% neq 0 (
    echo [错误] 程序异常退出。
    pause
)
