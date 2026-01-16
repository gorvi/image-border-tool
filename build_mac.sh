#!/bin/bash

# 确保在脚本所在目录
cd "$(dirname "$0")"

# 设置目标系统版本 (兼容旧版 macOS)
export MACOSX_DEPLOYMENT_TARGET=11.0

echo "=== 图片批量套版工具 - macOS 打包程序 ==="

# 1. 检查/创建虚拟环境
if [ ! -d ".venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv .venv
fi

# 2. 激活环境
source .venv/bin/activate

# 3. 安装打包依赖
echo "安装打包工具 PyInstaller..."
pip install pyinstaller -i https://pypi.tuna.tsinghua.edu.cn/simple
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 4. 清理旧构建
echo "清理旧文件..."
rm -rf build dist *.spec

# 5. 执行打包
# --noconsole: 不显示终端窗口
# --onefile: (可选) 打包成单文件，但启动较慢且不支持某些资源加载。这里建议用默认目录模式或 .app bundle
# macOS 默认会生成 .app 包在 dist 目录下
echo "开始打包 (请耐心等待)..."

pyinstaller --noconsole \
    --name "图片批量套版工具" \
    --clean \
    --windowed \
    --hidden-import=jieba \
    --hidden-import=PIL \
    --hidden-import=tkinter \
    --exclude-module=matplotlib \
    --collect-all=jieba \
    main.py

    # --add-data "resources:resources" \  # 如果有资源文件夹
    # --icon "app.icns" \  # 如果有图标

echo "=== 打包完成 ==="
echo "应用程序位于: dist/图片批量套版工具.app"
echo "您可以将该 .app 文件发送给用户 (用户需在 macOS 上运行)"
echo ""
echo "注意: 首次在其他电脑运行时，可能会因安全设置提示'来自不明开发者'。"
echo "解决方法: 系统设置 -> 隐私与安全性 -> 仍要打开。"
