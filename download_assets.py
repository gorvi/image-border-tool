#!/usr/bin/env python3
"""
下载开源贴纸和边框资源
从 Google Noto Emoji 仓库下载常用 emoji 图片
"""

import os
import sys
import urllib.request
from pathlib import Path

# 添加项目根目录到路径，以便导入 constants
sys.path.insert(0, str(Path(__file__).parent))

try:
    from constants import STICKER_LIST
except ImportError:
    print("错误: 无法导入 constants 模块")
    sys.exit(1)

# 创建目录
ASSETS_DIR = Path(__file__).parent / 'assets'
STICKERS_DIR = ASSETS_DIR / 'stickers'
BORDERS_DIR = ASSETS_DIR / 'borders'

STICKERS_DIR.mkdir(parents=True, exist_ok=True)
BORDERS_DIR.mkdir(parents=True, exist_ok=True)

# Noto Emoji 基础 URL
NOTO_EMOJI_BASE_URL = 'https://raw.githubusercontent.com/googlefonts/noto-emoji/main/png/128'

def emoji_to_filename(emoji_text):
    """
    将 emoji 转换为 Noto Emoji 文件名格式
    
    Noto Emoji 文件命名规则：
    - 单个字符: emoji_u{4位小写十六进制}.png
    - 多个字符: emoji_u{4位小写十六进制}_{4位小写十六进制}.png
    
    Args:
        emoji_text: emoji 字符，如 '❤️', '⭐', '😊'
    
    Returns:
        str: 文件名，如 'emoji_u2764.png' 或 'emoji_u1f60a.png'
    """
    if not emoji_text:
        return None
    
    # 获取 emoji 的 Unicode 码点
    codepoints = []
    for char in emoji_text:
        codepoint = ord(char)
        
        # 跳过变体选择器 (VS16, U+FE0F) - 这些在文件名中通常不包含
        if codepoint == 0xFE0F:
            continue
        # 保留零宽连接符 (U+200D) - 某些复合 emoji 需要
        # 跳过肤色修饰符 (U+1F3FB-1F3FF) - 这些在文件名中通常不包含
        if 0x1F3FB <= codepoint <= 0x1F3FF:
            continue
        
        # 转换为4位小写十六进制
        codepoints.append(f"{codepoint:04x}")
    
    if not codepoints:
        return None
    
    # 用下划线连接所有码点
    filename = f"emoji_u{'_'.join(codepoints)}.png"
    return filename

def get_sticker_resources():
    """
    从 STICKER_LIST 生成下载资源列表
    
    Returns:
        list: [(本地文件名, URL), ...]
    """
    resources = []
    for sticker in STICKER_LIST:
        if 'file' in sticker and 'emoji' in sticker:
            local_filename = sticker['file']
            emoji_text = sticker['emoji']
            noto_filename = emoji_to_filename(emoji_text)
            
            if noto_filename:
                url = f"{NOTO_EMOJI_BASE_URL}/{noto_filename}"
                resources.append((local_filename, url, emoji_text, sticker.get('name', '')))
            else:
                print(f"[警告] 无法转换 emoji '{emoji_text}' 为文件名，跳过 {local_filename}")
    
    return resources

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
    print("  来源: Google Noto Emoji")
    print("=" * 50)
    print()
    
    # 从 constants.py 获取贴纸列表
    sticker_resources = get_sticker_resources()
    
    if not sticker_resources:
        print("⚠️  未找到需要下载的贴纸资源")
        return
    
    # 下载贴纸
    print(f"📦 下载贴纸资源 ({len(sticker_resources)} 个)...")
    print()
    success_count = 0
    failed_items = []
    
    for local_filename, url, emoji, name in sticker_resources:
        dest_path = STICKERS_DIR / local_filename
        print(f"[{emoji}] {name or local_filename}: ", end="")
        
        # 检查文件是否已存在
        if dest_path.exists():
            print("已存在，跳过")
            success_count += 1
            continue
        
        if download_file(url, dest_path):
            success_count += 1
        else:
            failed_items.append((local_filename, emoji, name))
    
    print()
    print(f"✓ 贴纸下载完成: {success_count}/{len(sticker_resources)}")
    
    if failed_items:
        print()
        print("⚠️  以下贴纸下载失败:")
        for filename, emoji, name in failed_items:
            print(f"  - {emoji} {name or filename}")
        print()
        print("提示: 可能是 emoji Unicode 码点映射不正确，")
        print("      可以手动检查 Noto Emoji 仓库中的文件名。")
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
