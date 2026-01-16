@echo off
chcp 65001
echo ==========================================
echo      图片批量套版工具 - Windows 打包脚本
echo ==========================================

cd /d "%~dp0"

REM 1. 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Python，请先安装 Python 3.10+ 并添加到必须 PATH。
    pause
    exit /b
)

REM 2. 创建/激活虚拟环境
if not exist "venv" (
    echo [1/4] 创建虚拟环境...
    python -m venv venv
)

echo [2/4] 激活环境并安装依赖...
call venv\Scripts\activate
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple --upgrade pip
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple pyinstaller
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

REM 3. 清理旧文件
echo [3/4] 清理旧构建...
if exist build rd /s /q build
if exist dist rd /s /q dist
if exist *.spec del *.spec

REM 4. 执行打包
echo [4/4] 开始打包 (请耐心等待)...
pyinstaller --noconsole ^
    --name "图片批量套版工具" ^
    --clean ^
    --windowed ^
    --hidden-import=jieba ^
    --hidden-import=PIL ^
    --hidden-import=tkinter ^
    --exclude-module=matplotlib ^
    --collect-all=jieba ^
    main.py

echo.
echo ==========================================
echo [完成] 打包成功！
echo 程序位置: dist\图片批量套版工具\图片批量套版工具.exe
echo ==========================================
pause
