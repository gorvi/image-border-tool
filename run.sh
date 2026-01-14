#!/bin/bash

echo "================================"
echo "  图片套版工具 启动脚本"
echo "================================"
echo ""

# 强制使用系统Python，避免Xcode Python的Tkinter兼容性问题
if [ -f /usr/bin/python3 ]; then
    PYTHON_CMD="/usr/bin/python3"
    echo "✓ 使用系统 Python (/usr/bin/python3):"
elif command -v python3 &> /dev/null; then
    # 检查是否是Xcode的Python
    PYTHON_PATH=$(python3 -c "import sys; print(sys.executable)" 2>/dev/null)
    if echo "$PYTHON_PATH" | grep -q "Xcode.app"; then
        echo "❌ 错误: 检测到 Xcode 的 Python，会导致 Tkinter 崩溃！"
        echo "请使用系统 Python: /usr/bin/python3 main.py"
        exit 1
    fi
    PYTHON_CMD="python3"
    echo "✓ 使用 Python:"
else
    echo "❌ 错误: 未找到 Python3"
    echo "请先安装 Python 3.8 或更高版本"
    exit 1
fi

$PYTHON_CMD --version
$PYTHON_CMD -c "import sys; print('Python 路径:', sys.executable)" 2>/dev/null || true
echo ""

# 检查依赖是否安装
echo "检查依赖..."
if ! $PYTHON_CMD -c "import PIL" 2>/dev/null; then
    echo "📦 安装依赖中..."
    $PYTHON_CMD -m pip install -r requirements.txt
    echo ""
fi

echo "✓ 依赖检查完成"
echo ""

# 启动程序
echo "🚀 启动程序..."
echo ""
$PYTHON_CMD main.py
