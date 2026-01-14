#!/usr/bin/env python3
"""
下载开源贴纸和边框资源
"""

import os
import urllib.request
from pathlib import Path

# 创建目录
ASSETS_DIR = Path(__file__).parent / 'assets'
STICKERS_DIR = ASSETS_DIR / 'stickers'
BORDERS_DIR = ASSETS_DIR / 'borders'

STICKERS_DIR.mkdir(parents=True, exist_ok=True)
BORDERS_DIR.mkdir(parents=True, exist_ok=True)

# 开源贴纸资源（使用 Noto Emoji 和其他开源资源）
STICKER_RESOURCES = [
    # Noto Emoji (Google 开源)
    ('heart.png', 'https://raw.githubusercontent.com/googlefonts/noto-emoji/main/png/128/emoji_u2764.png'),
    ('star.png', 'https://raw.githubusercontent.com/googlefonts/noto-emoji/main/png/128/emoji_u2b50.png'),
    ('smile.png', 'https://raw.githubusercontent.com/googlefonts/noto-emoji/main/png/128/emoji_u1f60a.png'),
    ('fire.png', 'https://raw.githubusercontent.com/googlefonts/noto-emoji/main/png/128/emoji_u1f525.png'),
    ('sparkles.png', 'https://raw.githubusercontent.com/googlefonts/noto-emoji/main/png/128/emoji_u2728.png'),
    ('flower.png', 'https://raw.githubusercontent.com/googlefonts/noto-emoji/main/png/128/emoji_u1f338.png'),
    ('crown.png', 'https://raw.githubusercontent.com/googlefonts/noto-emoji/main/png/128/emoji_u1f451.png'),
    ('ribbon.png', 'https://raw.githubusercontent.com/googlefonts/noto-emoji/main/png/128/emoji_u1f380.png'),
    ('cake.png', 'https://raw.githubusercontent.com/googlefonts/noto-emoji/main/png/128/emoji_u1f382.png'),
    ('gift.png', 'https://raw.githubusercontent.com/googlefonts/noto-emoji/main/png/128/emoji_u1f381.png'),
    ('balloon.png', 'https://raw.githubusercontent.com/googlefonts/noto-emoji/main/png/128/emoji_u1f388.png'),
    ('music.png', 'https://raw.githubusercontent.com/googlefonts/noto-emoji/main/png/128/emoji_u1f3b5.png'),
]

def download_file(url, dest_path):
    """下载文件"""
    try:
        print(f"下载: {dest_path.name}...", end=" ")
        urllib.request.urlretrieve(url, dest_path)
        print("✓")
        return True
    except Exception as e:
        print(f"✗ ({e})")
        return False

def main():
    print("=" * 50)
    print("  下载开源贴纸和边框资源")
    print("=" * 50)
    print()
    
    # 下载贴纸
    print("📦 下载贴纸资源...")
    success_count = 0
    for filename, url in STICKER_RESOURCES:
        dest_path = STICKERS_DIR / filename
        if download_file(url, dest_path):
            success_count += 1
    
    print()
    print(f"✓ 贴纸下载完成: {success_count}/{len(STICKER_RESOURCES)}")
    print()
    
    # 创建边框说明文件
    borders_readme = BORDERS_DIR / 'README.txt'
    with open(borders_readme, 'w', encoding='utf-8') as f:
        f.write("""边框资源说明

边框通过代码生成，支持以下样式：
1. 简单边框 - 单色线条
2. 粗边框 - 加粗线条
3. 双线边框 - 双层线条
4. 圆角边框 - 圆角矩形
5. 阴影边框 - 带阴影效果

如需添加自定义边框图片，请将 PNG 图片放置在此目录。
""")
    
    print("✓ 边框说明文件已创建")
    print()
    print("=" * 50)
    print("  资源下载完成！")
    print("=" * 50)
    print()
    print(f"贴纸目录: {STICKERS_DIR}")
    print(f"边框目录: {BORDERS_DIR}")
    print()

if __name__ == '__main__':
    main()
