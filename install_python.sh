#!/bin/bash

echo "=========================================="
echo "  自动安装 Python 环境"
echo "=========================================="
echo ""

# 检测系统架构
ARCH=$(uname -m)
if [ "$ARCH" = "arm64" ]; then
    HOMEBREW_PREFIX="/opt/homebrew"
    echo "✓ 检测到 Apple Silicon (ARM64)"
else
    HOMEBREW_PREFIX="/usr/local"
    echo "✓ 检测到 Intel Mac"
fi

echo "Homebrew 路径: $HOMEBREW_PREFIX"
echo ""

# 检查 Homebrew 是否已安装
if [ -f "$HOMEBREW_PREFIX/bin/brew" ]; then
    echo "✓ Homebrew 已安装"
    BREW_CMD="$HOMEBREW_PREFIX/bin/brew"
elif [ -f "/usr/local/bin/brew" ] && [ "$ARCH" != "arm64" ]; then
    echo "✓ Homebrew 已安装 (Intel)"
    BREW_CMD="/usr/local/bin/brew"
    HOMEBREW_PREFIX="/usr/local"
else
    echo "📦 正在安装 Homebrew..."
    echo "   这可能需要几分钟，请耐心等待..."
    echo ""
    
    # 尝试安装 Homebrew
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" || {
        echo ""
        echo "❌ Homebrew 安装失败"
        echo ""
        echo "可能的原因："
        echo "  1. 网络连接问题"
        echo "  2. 需要管理员权限"
        echo ""
        echo "请手动安装 Homebrew："
        echo "  /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
        echo ""
        exit 1
    }
    
    # 设置 Homebrew 路径
    if [ -f "$HOMEBREW_PREFIX/bin/brew" ]; then
        BREW_CMD="$HOMEBREW_PREFIX/bin/brew"
        echo "✓ Homebrew 安装成功"
    else
        echo "❌ Homebrew 安装后未找到，请检查安装过程"
        exit 1
    fi
fi

echo ""
echo "📦 正在安装 Python 3..."
echo ""

# 安装 Python
$BREW_CMD install python3 || {
    echo ""
    echo "❌ Python 安装失败"
    echo ""
    echo "请手动运行："
    echo "  $BREW_CMD install python3"
    exit 1
}

# 安装 python-tk（Tkinter 支持）
echo ""
echo "📦 正在安装 python-tk（Tkinter 支持）..."
$BREW_CMD install python-tk@3.14 2>/dev/null || {
    # 尝试自动检测 Python 版本
    PYTHON_VERSION=$($HOMEBREW_PREFIX/bin/python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
    echo "尝试安装 python-tk@$PYTHON_VERSION..."
    $BREW_CMD install python-tk@$PYTHON_VERSION 2>/dev/null || {
        echo "⚠️  警告: python-tk 安装失败，Tkinter 可能不可用"
        echo "   可以稍后手动安装: $BREW_CMD install python-tk"
    }
}

echo ""
echo "✓ Python 安装成功"
echo ""

# 确定 Python 路径
PYTHON_PATH="$HOMEBREW_PREFIX/bin/python3"

if [ ! -f "$PYTHON_PATH" ]; then
    # 尝试查找实际的 Python 路径
    PYTHON_PATH=$($BREW_CMD --prefix python3)/bin/python3 2>/dev/null || {
        echo "❌ 无法找到 Python 路径"
        exit 1
    }
fi

echo "✓ Python 路径: $PYTHON_PATH"
echo ""

# 验证 Python
echo "验证 Python 安装..."
$PYTHON_PATH --version || {
    echo "❌ Python 验证失败"
    exit 1
}

# 检查是否是 Xcode Python
PYTHON_EXEC=$($PYTHON_PATH -c "import sys; print(sys.executable)" 2>/dev/null)
if echo "$PYTHON_EXEC" | grep -q "Xcode.app"; then
    echo "⚠️  警告: 仍然使用 Xcode Python"
    echo "   路径: $PYTHON_EXEC"
    exit 1
fi

echo "✓ Python 验证通过"
echo ""

# 安装项目依赖
echo "📦 安装项目依赖..."
cd "$(dirname "$0")"

# Python 3.11+ 需要特殊处理
PYTHON_VERSION=$($PYTHON_PATH --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
MAJOR_VERSION=$(echo $PYTHON_VERSION | cut -d. -f1)
MINOR_VERSION=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$MAJOR_VERSION" -ge 3 ] && [ "$MINOR_VERSION" -ge 11 ]; then
    echo "检测到 Python 3.11+，使用 --break-system-packages 标志"
    $PYTHON_PATH -m pip install --user --break-system-packages -r requirements.txt || {
        echo "❌ 依赖安装失败"
        exit 1
    }
else
    $PYTHON_PATH -m pip install --user -r requirements.txt || {
        echo "❌ 依赖安装失败"
        exit 1
    }
fi

echo ""
echo "=========================================="
echo "  ✅ 安装完成！"
echo "=========================================="
echo ""
echo "现在可以使用以下命令运行程序："
echo ""
echo "  $PYTHON_PATH main.py"
echo ""
echo "或者使用启动脚本："
echo "  ./start.sh"
echo ""
echo "Python 路径已保存到: .python_path"
echo "$PYTHON_PATH" > .python_path
echo ""
