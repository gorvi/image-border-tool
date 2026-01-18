#!/usr/bin/env python3
"""
直接下载重试脚本：不使用API，直接尝试下载文件
重试失败的项最多2次
"""

import urllib.request
import urllib.parse
import time
from pathlib import Path

# 创建目录
ASSETS_DIR = Path(__file__).parent / 'assets'
FLUENT_3D_DIR = ASSETS_DIR / 'stickers' / 'fluent_3d'
FLUENT_EMOJI_BASE_URL = 'https://raw.githubusercontent.com/microsoft/fluentui-emoji/main/assets'

FLUENT_3D_DIR.mkdir(parents=True, exist_ok=True)

def normalize_category_name(name):
    """将目录名转换为文件名格式"""
    return name.lower().replace(' ', '_')

def get_fluent_emoji_url(category, filename):
    """构建下载 URL"""
    category_encoded = urllib.parse.quote(category, safe='')
    filename_encoded = urllib.parse.quote(filename, safe='')
    return f"{FLUENT_EMOJI_BASE_URL}/{category_encoded}/3D/{filename_encoded}"

def try_download(category, filename):
    """尝试直接下载文件"""
    dest_path = FLUENT_3D_DIR / filename
    
    # 如果文件已存在，跳过
    if dest_path.exists():
        return True
    
    url = get_fluent_emoji_url(category, filename)
    
    try:
        urllib.request.urlretrieve(url, dest_path)
        # 验证文件是否真的下载了（检查文件大小）
        if dest_path.exists() and dest_path.stat().st_size > 0:
            return True
        else:
            # 文件下载失败，删除空文件
            if dest_path.exists():
                dest_path.unlink()
            return False
    except urllib.error.HTTPError as e:
        if dest_path.exists():
            dest_path.unlink()
        return False
    except Exception:
        if dest_path.exists():
            dest_path.unlink()
        return False

def get_missing_files_from_downloaded():
    """从已下载的文件列表推断可能缺失的文件
    由于我们不知道完整的类别列表，这个方法可以尝试一些常见的类别
    或者从已有的文件名模式推断
    """
    # 获取所有已下载的文件名
    downloaded_files = set()
    if FLUENT_3D_DIR.exists():
        for f in FLUENT_3D_DIR.glob("*_3d.png"):
            downloaded_files.add(f.name)
    
    # 由于我们不知道完整的类别列表，这里我们使用一个已知的类别列表
    # 或者让用户手动提供，或者从之前的运行记录中获取
    
    # 常见类别名（从Fluent UI Emoji的常见emoji推断）
    # 这是一个不完整列表，但可以覆盖大部分
    common_categories = [
        "Bacon", "Red heart", "Green heart", "Blue heart", "Yellow heart",
        "Purple heart", "Orange heart", "Sparkling heart", "Two hearts",
        "Smiling face with hearts", "Grinning face", "Smiling face with open mouth",
        "Smiling face with smiling eyes", "Star-struck", "Kissing face",
        "Winking face", "Thinking face", "Cool", "Hugging", "Folded hands",
        "Clapping hands", "OK hand", "Victory hand", "Call me hand",
        "Backhand index pointing right", "Backhand index pointing left",
        "Backhand index pointing up", "Backhand index pointing down",
        "Flexed biceps", "Waving hand", "Apple", "Banana", "Orange",
        "Strawberry", "Grapes", "Watermelon", "Cherry", "Peach", "Mango",
        "Pineapple", "Cake", "Cookie", "Donut", "Ice cream", "Lollipop",
        "Cupcake", "Hamburger", "Pizza", "Taco", "Fries", "Sushi",
        "Coffee", "Sunflower", "Rose", "Tulip", "Hibiscus", "Four leaf clover",
        "Sun", "Full moon", "Star", "Rainbow", "Cloud", "Lightning",
        "Fire", "Snowflake", "Droplet", "Camera", "Rocket", "Trophy",
        "Medal", "Confetti ball", "Party popper", "Fireworks", "Sparkler",
        "Gift", "Crown", "Gem stone", "Diamond", "Check mark button",
        "Hundred points", "Cat", "Dog", "Rabbit", "Mouse", "Hamster",
        "Panda", "Bear", "Polar bear", "Koala", "Tiger", "Lion",
        "Cow", "Pig", "Frog", "Monkey", "Chicken", "Penguin",
        "Owl", "Butterfly", "Bee", "Lady beetle", "Fish", "Dolphin",
        "Whale", "Turtle", "Unicorn", "Fox"
    ]
    
    # 找出缺失的文件
    missing = []
    for category in common_categories:
        normalized = normalize_category_name(category)
        filename = f"{normalized}_3d.png"
        
        if filename not in downloaded_files:
            missing.append((category, filename))
    
    return missing

def main():
    print("=" * 60)
    print("  直接下载重试：不使用API")
    print("  重试失败的 Fluent UI Emoji 3D 表情（最多2次）")
    print("=" * 60)
    print()
    
    # 方法1：尝试从常见类别找出缺失的
    print("正在检查缺失的文件...")
    missing = get_missing_files_from_downloaded()
    
    if not missing:
        print("✓ 所有常见表情都已下载成功！")
        print()
        print("提示：如果需要重试更多文件，请提供类别列表或运行完整下载脚本")
        return
    
    print(f"找到 {len(missing)} 个可能缺失的文件")
    print()
    
    # 重试2次
    for retry_round in range(1, 3):
        if not missing:
            break
        
        print(f"🔄 第 {retry_round} 次重试 ({len(missing)} 个文件)...")
        print()
        
        success_count = 0
        still_missing = []
        
        for i, (category, filename) in enumerate(missing):
            print(f"  [{i+1}/{len(missing)}] {filename}: ", end="")
            
            if try_download(category, filename):
                print("✓")
                success_count += 1
            else:
                print("✗")
                still_missing.append((category, filename))
            
            # 避免请求过快
            if (i + 1) % 20 == 0:
                time.sleep(0.3)
            else:
                time.sleep(0.05)
        
        missing = still_missing
        
        print()
        if success_count > 0:
            print(f"  ✓ 成功下载: {success_count} 个文件")
        if missing:
            print(f"  ⚠️  仍然失败: {len(missing)} 个文件")
        else:
            print(f"  ✓ 所有文件下载成功！")
        
        if retry_round < 2 and missing:
            print()
            time.sleep(1)
    
    print()
    print("=" * 60)
    print("  重试完成！")
    print("=" * 60)
    print()
    
    # 统计最终结果
    total_downloaded = len(list(FLUENT_3D_DIR.glob("*_3d.png")))
    print(f"当前已下载文件数: {total_downloaded}")
    
    if missing:
        print(f"⚠️  仍有 {len(missing)} 个文件下载失败:")
        for category, filename in missing[:20]:
            print(f"  - {category}/{filename}")
        if len(missing) > 20:
            print(f"  ... 还有 {len(missing) - 20} 个失败项")
    else:
        print("✓ 所有文件都已成功下载！")
    print()

if __name__ == '__main__':
    main()
