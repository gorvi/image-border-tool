#!/usr/bin/env python3
"""
直接检查缺失文件：不依赖API
从已下载的文件推断可能的类别，然后检查并下载缺失的文件
"""

import urllib.request
import urllib.parse
import time
from pathlib import Path
import re

# 创建目录
ASSETS_DIR = Path(__file__).parent / 'assets'
FLUENT_3D_DIR = ASSETS_DIR / 'stickers' / 'fluent_3d'
FLUENT_EMOJI_BASE_URL = 'https://raw.githubusercontent.com/microsoft/fluentui-emoji/main/assets'

FLUENT_3D_DIR.mkdir(parents=True, exist_ok=True)

def normalize_category_name(name):
    """将目录名转换为文件名格式"""
    return name.lower().replace(' ', '_')

def category_name_from_filename(filename):
    """从文件名反推类别名（大写首字母，空格分隔）"""
    # 移除 _3d.png 后缀
    if filename.endswith('_3d.png'):
        base = filename[:-7]  # 移除 '_3d.png'
    elif filename.endswith('.png'):
        base = filename[:-4]
    else:
        return None
    
    # 将下划线转换为空格，并大写首字母
    words = base.split('_')
    category = ' '.join(word.capitalize() for word in words)
    return category

def get_fluent_emoji_url(category, filename):
    """构建下载 URL"""
    category_encoded = urllib.parse.quote(category, safe='')
    filename_encoded = urllib.parse.quote(filename, safe='')
    return f"{FLUENT_EMOJI_BASE_URL}/{category_encoded}/3D/{filename_encoded}"

def try_direct_download(category, filename):
    """直接下载文件（不使用API）"""
    dest_path = FLUENT_3D_DIR / filename
    
    # 如果文件已存在且大小>0，跳过
    if dest_path.exists() and dest_path.stat().st_size > 0:
        return True
    
    url = get_fluent_emoji_url(category, filename)
    
    try:
        urllib.request.urlretrieve(url, dest_path)
        # 验证文件是否真的下载了
        if dest_path.exists() and dest_path.stat().st_size > 0:
            return True
        else:
            if dest_path.exists():
                dest_path.unlink()
            return False
    except urllib.error.HTTPError:
        if dest_path.exists():
            dest_path.unlink()
        return False
    except Exception:
        if dest_path.exists():
            dest_path.unlink()
        return False

def get_all_downloaded_categories():
    """从已下载的文件名推断类别列表"""
    downloaded_files = list(FLUENT_3D_DIR.glob("*_3d.png"))
    categories = {}
    
    for file in downloaded_files:
        category = category_name_from_filename(file.name)
        if category:
            categories[category] = file.name
    
    return categories

def generate_common_categories():
    """生成常见的类别列表（基于常见emoji）"""
    # 这些是常见的类别，可以根据需要扩展
    common_categories = [
        "Abacus", "Airplane", "Alarm clock", "Alien", "Ambulance", "Anchor",
        "Apple", "Avocado", "Baby", "Balloon", "Banana", "Baseball",
        "Basketball", "Bear", "Bee", "Bell", "Bicycle", "Birthday cake",
        "Blue heart", "Book", "Bouquet", "Bread", "Bridge", "Broccoli",
        "Butterfly", "Cake", "Calendar", "Camera", "Candy", "Car",
        "Cat", "Cherry", "Chicken", "Christmas tree", "Cocktail", "Coffee",
        "Cookie", "Cool", "Cow", "Crab", "Crown", "Cupcake",
        "Diamond", "Dog", "Dolphin", "Donut", "Dragon", "Duck",
        "Eagle", "Earth", "Egg", "Elephant", "Fire", "Fireworks",
        "Fish", "Flag", "Flower", "Folded hands", "Fox", "Fries",
        "Frog", "Full moon", "Gift", "Giraffe", "Grapes", "Green heart",
        "Grinning face", "Hamburger", "Hamster", "Hand", "Heart", "Hibiscus",
        "Honeybee", "Horse", "Hot dog", "Ice cream", "Key", "Kiss",
        "Koala", "Lady beetle", "Laptop", "Lemon", "Light bulb", "Lightning",
        "Lion", "Lollipop", "Love letter", "Mango", "Map", "Medal",
        "Melon", "Milk", "Money", "Monkey", "Moon", "Mouse",
        "Music", "Mushroom", "Ok hand", "Orange", "Orange heart", "Owl",
        "Panda", "Peach", "Penguin", "Phone", "Pig", "Pineapple",
        "Pizza", "Polar bear", "Popcorn", "Pray", "Purple heart", "Rabbit",
        "Rainbow", "Raising hands", "Rocket", "Rose", "Santa", "Shark",
        "Ship", "Smiling face with hearts", "Snowflake", "Soccer ball", "Sparkler", "Sparkles",
        "Sparkling heart", "Star", "Star-struck", "Strawberry", "Sun", "Sunflower",
        "Sushi", "Swan", "Taco", "Tennis", "Thinking face", "Thumbs up",
        "Tiger", "Toast", "Trophy", "Tulip", "Turtle", "Two hearts",
        "Unicorn", "Watermelon", "Waving hand", "Whale", "Wink", "Yellow heart",
        "Zebra", "Zipper mouth"
    ]
    return common_categories

def main():
    print("=" * 60)
    print("  直接检查缺失文件（不使用API）")
    print("=" * 60)
    print()
    
    # 获取已下载的文件
    print("正在检查已下载的文件...")
    downloaded_categories = get_all_downloaded_categories()
    print(f"已下载: {len(downloaded_categories)} 个文件")
    print()
    
    # 生成常见类别列表
    print("正在生成常见类别列表...")
    all_categories = generate_common_categories()
    print(f"常见类别: {len(all_categories)} 个")
    print()
    
    # 检查缺失的文件
    print("正在检查缺失的文件...")
    missing = []
    existing_count = 0
    
    for category in all_categories:
        normalized = normalize_category_name(category)
        filename = f"{normalized}_3d.png"
        dest_path = FLUENT_3D_DIR / filename
        
        if dest_path.exists() and dest_path.stat().st_size > 0:
            existing_count += 1
        else:
            missing.append((category, filename))
    
    print(f"已存在: {existing_count} 个文件")
    print(f"缺失: {len(missing)} 个文件")
    print()
    
    if not missing:
        print("✓ 所有常见文件都已下载成功！")
        return
    
    # 直接下载缺失的文件（重试2次）
    for retry_round in range(1, 3):
        if not missing:
            break
        
        print(f"🔄 第 {retry_round} 次重试 ({len(missing)} 个文件)...")
        print()
        
        success_count = 0
        still_missing = []
        
        for i, (category, filename) in enumerate(missing):
            print(f"  [{i+1}/{len(missing)}] {filename}: ", end="")
            
            if try_direct_download(category, filename):
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
    
    # 最终统计
    final_count = len(list(FLUENT_3D_DIR.glob("*_3d.png")))
    
    print()
    print("=" * 60)
    print("  检查完成！")
    print("=" * 60)
    print()
    print(f"总类别数: {len(all_categories)}")
    print(f"已下载文件数: {final_count}")
    
    if missing:
        print(f"失败: {len(missing)} 个文件")
        print()
        print("失败的项（可能是命名不匹配或不存在3D版本）:")
        for category, filename in missing[:30]:
            print(f"  - {category}/{filename}")
        if len(missing) > 30:
            print(f"  ... 还有 {len(missing) - 30} 个失败项")
    else:
        print("✓ 所有文件都已成功下载！")
    print()

if __name__ == '__main__':
    main()
