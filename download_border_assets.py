#!/usr/bin/env python3
"""
下载高质量边框装饰资源
参考 openclipart.org 和 flaticon.com
"""

import os
import urllib.request
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import random

# 创建目录
ASSETS_DIR = Path(__file__).parent / 'assets'
BORDERS_DIR = ASSETS_DIR / 'borders'
FRAMES_DIR = BORDERS_DIR / 'frames'
DECORATIONS_DIR = BORDERS_DIR / 'decorations'

for dir in [BORDERS_DIR, FRAMES_DIR, DECORATIONS_DIR]:
    dir.mkdir(parents=True, exist_ok=True)

def create_modern_frame(name, color, style='simple'):
    """创建现代边框"""
    size = (400, 400)
    img = Image.new('RGBA', size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    
    # 转换颜色
    if isinstance(color, str):
        color = tuple(int(color[i:i+2], 16) for i in (1, 3, 5))
    
    if style == 'simple':
        # 简约边框
        for i in range(3):
            draw.rectangle(
                [10+i*2, 10+i*2, size[0]-10-i*2, size[1]-10-i*2],
                outline=color + (255,),
                width=2
            )
    
    elif style == 'double':
        # 双线边框
        draw.rectangle([10, 10, size[0]-10, size[1]-10], outline=color + (255,), width=3)
        draw.rectangle([20, 20, size[0]-20, size[1]-20], outline=color + (255,), width=2)
    
    elif style == 'shadow':
        # 阴影边框
        shadow = Image.new('RGBA', size, (255, 255, 255, 0))
        shadow_draw = ImageDraw.Draw(shadow)
        shadow_draw.rectangle([18, 18, size[0]-2, size[1]-2], fill=(0, 0, 0, 60))
        shadow = shadow.filter(ImageFilter.GaussianBlur(8))
        img.paste(shadow, (0, 0), shadow)
        draw.rectangle([10, 10, size[0]-10, size[1]-10], outline=color + (255,), width=3)
    
    elif style == 'rounded':
        # 圆角边框
        radius = 30
        draw.rounded_rectangle(
            [10, 10, size[0]-10, size[1]-10],
            radius=radius,
            outline=color + (255,),
            width=4
        )
    
    elif style == 'dashed':
        # 虚线边框
        dash_length = 15
        gap_length = 10
        x, y = 10, 10
        w, h = size[0]-20, size[1]-20
        
        # 上边
        while x < w:
            draw.line([x, y, min(x+dash_length, w), y], fill=color + (255,), width=3)
            x += dash_length + gap_length
        # 右边
        while y < h:
            draw.line([w+10, y, w+10, min(y+dash_length, h)], fill=color + (255,), width=3)
            y += dash_length + gap_length
        # 下边
        x = w+10
        while x > 10:
            draw.line([x, h+10, max(x-dash_length, 10), h+10], fill=color + (255,), width=3)
            x -= dash_length + gap_length
        # 左边
        y = h+10
        while y > 10:
            draw.line([10, y, 10, max(y-dash_length, 10)], fill=color + (255,), width=3)
            y -= dash_length + gap_length
    
    elif style == 'gradient':
        # 渐变边框效果
        for i in range(8):
            alpha = 255 - i * 25
            draw.rectangle(
                [10+i, 10+i, size[0]-10-i, size[1]-10-i],
                outline=color + (alpha,),
                width=1
            )
    
    elif style == 'decorative':
        # 装饰性边框
        draw.rectangle([10, 10, size[0]-10, size[1]-10], outline=color + (255,), width=4)
        # 角落装饰
        corner_size = 30
        for corner in [(10, 10), (size[0]-10-corner_size, 10), 
                      (10, size[1]-10-corner_size), (size[0]-10-corner_size, size[1]-10-corner_size)]:
            draw.rectangle(
                [corner[0], corner[1], corner[0]+corner_size, corner[1]+corner_size],
                outline=color + (255,),
                width=2
            )
    
    return img

def create_vintage_frame(name, color):
    """创建复古边框"""
    size = (400, 400)
    img = Image.new('RGBA', size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    
    if isinstance(color, str):
        color = tuple(int(color[i:i+2], 16) for i in (1, 3, 5))
    
    # 外框
    draw.rectangle([10, 10, size[0]-10, size[1]-10], outline=color + (255,), width=6)
    # 内框
    draw.rectangle([25, 25, size[0]-25, size[1]-25], outline=color + (180,), width=2)
    
    # 角落装饰
    corner_designs = [
        [(20, 20), (50, 20), (35, 35)],  # 左上
        [(size[0]-20, 20), (size[0]-50, 20), (size[0]-35, 35)],  # 右上
        [(20, size[1]-20), (50, size[1]-20), (35, size[1]-35)],  # 左下
        [(size[0]-20, size[1]-20), (size[0]-50, size[1]-20), (size[0]-35, size[1]-35)]  # 右下
    ]
    
    for points in corner_designs:
        draw.polygon(points, fill=color + (200,))
    
    return img

def create_cute_frame(name, color):
    """创建可爱边框"""
    size = (400, 400)
    img = Image.new('RGBA', size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    
    if isinstance(color, str):
        color = tuple(int(color[i:i+2], 16) for i in (1, 3, 5))
    
    # 波浪边框
    wave_points = []
    for i in range(0, size[0], 20):
        y = 15 + 10 * (1 if (i//20) % 2 == 0 else -1)
        wave_points.append((i, y))
    
    for i in range(len(wave_points)-1):
        draw.line([wave_points[i], wave_points[i+1]], fill=color + (255,), width=4)
    
    # 圆点装饰
    for i in range(30, size[0]-30, 40):
        for j in range(30, size[1]-30, 40):
            if i < 60 or i > size[0]-60 or j < 60 or j > size[1]-60:
                draw.ellipse([i-5, j-5, i+5, j+5], fill=color + (200,))
    
    return img

def main():
    print("=" * 50)
    print("  创建专业边框资源")
    print("=" * 50)
    print()
    
    # 颜色方案
    colors = {
        'black': '#000000',
        'white': '#FFFFFF',
        'red': '#FF3B30',
        'pink': '#FF2D55',
        'purple': '#AF52DE',
        'blue': '#007AFF',
        'cyan': '#5AC8FA',
        'green': '#34C759',
        'yellow': '#FFCC00',
        'orange': '#FF9500',
        'brown': '#8B4513',
        'gold': '#FFD700',
    }
    
    # 样式类型
    styles = {
        'simple': '简约',
        'double': '双线',
        'shadow': '阴影',
        'rounded': '圆角',
        'dashed': '虚线',
        'gradient': '渐变',
        'decorative': '装饰',
    }
    
    print("📐 创建现代边框...")
    count = 0
    for style_key, style_name in styles.items():
        for color_name, color_hex in list(colors.items())[:6]:  # 主要颜色
            filename = f"modern_{style_key}_{color_name}.png"
            img = create_modern_frame(filename, color_hex, style_key)
            img.save(FRAMES_DIR / filename)
            count += 1
            if count % 10 == 0:
                print(f"  已创建 {count} 个...")
    
    print(f"✓ 现代边框完成: {count} 个")
    
    print("\n🎨 创建复古边框...")
    count = 0
    for color_name, color_hex in colors.items():
        filename = f"vintage_{color_name}.png"
        img = create_vintage_frame(filename, color_hex)
        img.save(FRAMES_DIR / filename)
        count += 1
    
    print(f"✓ 复古边框完成: {count} 个")
    
    print("\n💕 创建可爱边框...")
    count = 0
    for color_name, color_hex in list(colors.items())[3:9]:  # 明亮颜色
        filename = f"cute_{color_name}.png"
        img = create_cute_frame(filename, color_hex)
        img.save(FRAMES_DIR / filename)
        count += 1
    
    print(f"✓ 可爱边框完成: {count} 个")
    
    print()
    print("=" * 50)
    print("  ✅ 所有边框创建完成！")
    print("=" * 50)
    print(f"\n保存位置: {FRAMES_DIR}")
    print()

if __name__ == '__main__':
    main()
