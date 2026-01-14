#!/bin/bash

echo "================================"
echo "  图片套版工具 - 使用系统Python"
echo "================================"
echo ""

# 强制使用系统Python
PYTHON_CMD="/usr/bin/python3"

if [ ! -f "$PYTHON_CMD" ]; then
    echo "❌ 错误: 系统 Python 不存在"
    exit 1
fi

echo "✓ 使用系统 Python:"
$PYTHON_CMD --version
echo ""

# 检查依赖
echo "检查依赖..."
if ! $PYTHON_CMD -c "import PIL" 2>/dev/null; then
    echo "📦 安装依赖中..."
    $PYTHON_CMD -m pip install --user -r requirements.txt
    echo ""
fi

echo "✓ 依赖检查完成"
echo ""

# 启动程序
echo "🚀 启动程序..."
echo ""
$PYTHON_CMD main.py
