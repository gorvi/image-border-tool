#!/usr/bin/env python3
"""
快速测试脚本 - 验证所有模块能否正常导入
"""

print("=" * 50)
print("  图片套版工具 - 模块导入测试")
print("=" * 50)
print()

# 测试导入
try:
    print("1. 测试 Pillow...", end=" ")
    from PIL import Image
    print(f"✓ 成功 (版本: {Image.__version__})")
except Exception as e:
    print(f"✗ 失败: {e}")
    exit(1)

try:
    print("2. 测试 Tkinter...", end=" ")
    import tkinter
    print("✓ 成功")
except Exception as e:
    print(f"✗ 失败: {e}")
    exit(1)

try:
    print("3. 测试 constants...", end=" ")
    import constants
    print("✓ 成功")
except Exception as e:
    print(f"✗ 失败: {e}")
    exit(1)

try:
    print("4. 测试 image_processor...", end=" ")
    import image_processor
    print("✓ 成功")
except Exception as e:
    print(f"✗ 失败: {e}")
    exit(1)

try:
    print("5. 测试 canvas_widget...", end=" ")
    import canvas_widget
    print("✓ 成功")
except Exception as e:
    print(f"✗ 失败: {e}")
    exit(1)

try:
    print("6. 测试 main_window...", end=" ")
    import main_window
    print("✓ 成功")
except Exception as e:
    print(f"✗ 失败: {e}")
    exit(1)

try:
    print("7. 测试 main...", end=" ")
    import main
    print("✓ 成功")
except Exception as e:
    print(f"✗ 失败: {e}")
    exit(1)

print()
print("=" * 50)
print("  ✅ 所有模块导入成功！")
print("=" * 50)
print()
print("现在可以运行程序了：")
print("  python3 main.py")
print("  或")
print("  ./run.sh")
print()
