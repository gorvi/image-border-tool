#!/usr/bin/env python3
"""
图片套版工具 - 主程序入口
"""

import sys
import os

# 检查是否使用了不兼容的Python（会导致Tkinter崩溃）
PYTHON_PATH = sys.executable
INCOMPATIBLE_PATHS = ['Xcode.app', 'CommandLineTools', '/Applications/Xcode.app', '/Library/Developer']

is_incompatible = any(path in PYTHON_PATH for path in INCOMPATIBLE_PATHS)

if is_incompatible:
    print("=" * 60)
    print("⚠️  警告: 检测到正在使用不兼容的 Python")
    print("=" * 60)
    print(f"当前 Python 路径: {PYTHON_PATH}")
    print()
    print("此 Python 版本（Xcode/CommandLineTools）与 Tkinter 不兼容，会导致程序崩溃！")
    print()
    print("✅ 解决方案：使用 Homebrew Python")
    print()
    print("方式1: 使用启动脚本（推荐）")
    print("  ./start.sh")
    print()
    print("方式2: 直接使用 Homebrew Python")
    print("  /opt/homebrew/bin/python3 main.py")
    print()
    print("方式3: 如果未安装 Homebrew Python，请先运行：")
    print("  ./install_python.sh")
    print()
    print("=" * 60)
    sys.exit(1)

# 检查 Tkinter 是否可用
try:
    import tkinter
except ImportError:
    print("错误: Tkinter 不可用，请检查 Python 安装")
    sys.exit(1)

from main_window import MainWindow


def main():
    """主函数"""
    try:
        app = MainWindow()
        app.mainloop()
    except Exception as e:
        print(f"程序运行错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
