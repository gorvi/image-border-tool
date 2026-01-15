#!/bin/bash

echo "================================"
echo "  图片套版工具 - 安全启动"
echo "================================"
echo ""

# 优先使用项目虚拟环境
if [ -f .venv/bin/python ]; then
    PYTHON_CMD=".venv/bin/python"
    echo "✓ 使用项目虚拟环境 (.venv):"
# 检查是否有保存的 Python 路径
elif [ -f .python_path ]; then
    PYTHON_CMD=$(cat .python_path)
    echo "✓ 使用已配置的 Python:"
elif [ -f /opt/homebrew/bin/python3 ]; then
    PYTHON_CMD="/opt/homebrew/bin/python3"
    echo "✓ 使用 Homebrew Python (Apple Silicon):"
elif [ -f /usr/local/bin/python3 ]; then
    PYTHON_CMD="/usr/local/bin/python3"
    echo "✓ 使用 Homebrew Python (Intel):"
else
    PYTHON_CMD="/usr/bin/python3"
    echo "⚠️  使用系统 Python（可能不兼容）:"
fi

$PYTHON_CMD --version
PYTHON_EXEC=$($PYTHON_CMD -c "import sys; print(sys.executable)" 2>/dev/null)
echo "Python 路径: $PYTHON_EXEC"
echo ""

# 检查是否是不兼容的 Python
INCOMPATIBLE_PATTERNS="Xcode.app|CommandLineTools|/Applications/Xcode.app|/Library/Developer"
if echo "$PYTHON_EXEC" | grep -qE "$INCOMPATIBLE_PATTERNS"; then
    echo "❌ 错误: 检测到不兼容的 Python（Xcode/CommandLineTools），会导致 Tkinter 崩溃！"
    echo "   Python 路径: $PYTHON_EXEC"
    echo ""
    echo "请先运行安装脚本安装 Homebrew Python："
    echo "  ./install_python.sh"
    echo ""
    echo "或直接使用 Homebrew Python："
    echo "  /opt/homebrew/bin/python3 main.py"
    echo ""
    exit 1
fi

# 检查依赖
echo "检查依赖..."
if ! $PYTHON_CMD -c "import PIL" 2>/dev/null; then
    echo "📦 安装依赖中..."
    # Python 3.11+ 需要 --break-system-packages
    PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
    MAJOR_VERSION=$(echo $PYTHON_VERSION | cut -d. -f1)
    MINOR_VERSION=$(echo $PYTHON_VERSION | cut -d. -f2)
    
    if [ "$MAJOR_VERSION" -ge 3 ] && [ "$MINOR_VERSION" -ge 11 ]; then
        $PYTHON_CMD -m pip install --user --break-system-packages -r requirements.txt
    else
        $PYTHON_CMD -m pip install --user -r requirements.txt
    fi
    echo ""
fi

echo "✓ 依赖检查完成"
echo ""

# 启动程序
echo "🚀 启动程序..."
echo ""
cd "$(dirname "$0")"
$PYTHON_CMD main.py
