#!/usr/bin/env python3
"""
生成默认背景图片
"""

from PIL import Image, ImageDraw, ImageFilter
import os
from pathlib import Path

BG_DIR = Path(__file__).parent / 'assets' / 'backgrounds'
BG_DIR.mkdir(parents=True, exist_ok=True)

# 小红书竖屏尺寸
WIDTH = 1242
HEIGHT = 1660

def create_gradient_background(name, color1, color2):
    """创建渐变背景"""
    img = Image.new('RGB', (WIDTH, HEIGHT), color1)
    draw = ImageDraw.Draw(img)
    
    # 垂直渐变
    for y in range(HEIGHT):
        ratio = y / HEIGHT
        r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
        g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
        b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
        draw.line([(0, y), (WIDTH, y)], fill=(r, g, b))
    
    img.save(BG_DIR / f'{name}.png')
    print(f"✓ {name}.png")

def create_solid_background(name, color):
    """创建纯色背景"""
    img = Image.new('RGB', (WIDTH, HEIGHT), color)
    img.save(BG_DIR / f'{name}.png')
    print(f"✓ {name}.png")

def create_pattern_background(name, base_color, pattern_color):
    """创建图案背景"""
    img = Image.new('RGB', (WIDTH, HEIGHT), base_color)
    draw = ImageDraw.Draw(img)
    
    # 简单圆点图案
    spacing = 80
    radius = 10
    for x in range(0, WIDTH, spacing):
        for y in range(0, HEIGHT, spacing):
            draw.ellipse(
                [x-radius, y-radius, x+radius, y+radius],
                fill=pattern_color
            )
    
    img.save(BG_DIR / f'{name}.png')
    print(f"✓ {name}.png")

print("=" * 50)
print("  生成默认背景图片")
print("=" * 50)
print()

# 纯色背景
create_solid_background('white', (255, 255, 255))
create_solid_background('light_gray', (245, 245, 245))
create_solid_background('cream', (255, 248, 220))

# 渐变背景
create_gradient_background('gradient_blue', (227, 242, 253), (187, 222, 251))
create_gradient_background('gradient_pink', (252, 228, 236), (248, 187, 208))
create_gradient_background('gradient_purple', (243, 229, 245), (225, 190, 231))
create_gradient_background('gradient_green', (232, 245, 233), (200, 230, 201))

# 图案背景
create_pattern_background('dots_light', (255, 255, 255), (240, 240, 240))

print()
print(f"✓ 完成！共生成 8 个背景图片")
print(f"✓ 保存位置: {BG_DIR}")
