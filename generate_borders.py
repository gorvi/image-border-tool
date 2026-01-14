#!/usr/bin/env python3
"""
生成边框样式预览图
"""

from PIL import Image, ImageDraw
from pathlib import Path

BORDERS_DIR = Path(__file__).parent / 'assets' / 'borders'
BORDERS_DIR.mkdir(parents=True, exist_ok=True)

def create_border_preview(name, draw_func, size=(200, 200)):
    """创建边框预览图"""
    img = Image.new('RGBA', size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    draw_func(draw, size)
    
    filepath = BORDERS_DIR / f'{name}.png'
    img.save(filepath)
    print(f"✓ 生成: {name}.png")

def simple_border(draw, size):
    """简单边框"""
    w, h = size
    border_width = 10
    draw.rectangle([0, 0, w-1, h-1], outline='black', width=border_width)

def thick_border(draw, size):
    """粗边框"""
    w, h = size
    border_width = 20
    draw.rectangle([0, 0, w-1, h-1], outline='#333333', width=border_width)

def double_border(draw, size):
    """双线边框"""
    w, h = size
    # 外边框
    draw.rectangle([0, 0, w-1, h-1], outline='black', width=3)
    # 内边框
    margin = 10
    draw.rectangle([margin, margin, w-1-margin, h-1-margin], outline='black', width=3)

def rounded_border(draw, size):
    """圆角边框"""
    w, h = size
    radius = 20
    border_width = 10
    draw.rounded_rectangle([0, 0, w-1, h-1], radius=radius, outline='black', width=border_width)

def decorative_border(draw, size):
    """装饰性边框"""
    w, h = size
    # 外框
    draw.rectangle([0, 0, w-1, h-1], outline='#FFD700', width=15)
    # 内框
    margin = 20
    draw.rectangle([margin, margin, w-1-margin, h-1-margin], outline='#FF6B6B', width=5)

def main():
    print("=" * 50)
    print("  生成边框预览图")
    print("=" * 50)
    print()
    
    borders = [
        ('simple', simple_border),
        ('thick', thick_border),
        ('double', double_border),
        ('rounded', rounded_border),
        ('decorative', decorative_border),
    ]
    
    for name, func in borders:
        create_border_preview(name, func)
    
    print()
    print(f"✓ 完成！生成了 {len(borders)} 个边框预览图")
    print(f"✓ 保存位置: {BORDERS_DIR}")
    print()

if __name__ == '__main__':
    main()
