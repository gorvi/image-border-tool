#!/usr/bin/env python3
"""
下载 Microsoft Fluent UI Emoji 3D 表情
从 GitHub 仓库遍历并下载所有 3D 风格的 emoji 图片
"""

import os
import sys
import urllib.request
import urllib.parse
import json
import time
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
FLUENT_3D_DIR = ASSETS_DIR / 'stickers' / 'fluent_3d'

FLUENT_3D_DIR.mkdir(parents=True, exist_ok=True)

# Fluent UI Emoji 基础 URL
FLUENT_EMOJI_BASE_URL = 'https://raw.githubusercontent.com/microsoft/fluentui-emoji/main/assets'
FLUENT_EMOJI_API_URL = 'https://api.github.com/repos/microsoft/fluentui-emoji/contents/assets'

def get_github_api_contents(path):
    """
    使用 GitHub API 获取目录内容
    
    Args:
        path: GitHub 仓库中的路径（需要URL编码）
    
    Returns:
        list: 文件/目录列表
    """
    try:
        # URL 编码路径
        encoded_path = urllib.parse.quote(path, safe='/')
        api_url = f"https://api.github.com/repos/microsoft/fluentui-emoji/contents/{encoded_path}"
        req = urllib.request.Request(api_url)
        req.add_header('Accept', 'application/vnd.github.v3+json')
        req.add_header('User-Agent', 'Mozilla/5.0')
        
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            return data
    except urllib.error.HTTPError as e:
        if e.code == 403:
            # 速率限制，稍后重试
            return None
        return None
    except Exception as e:
        return None

def normalize_category_name(name):
    """
    将目录名转换为文件名格式
    例如: "Red heart" -> "red_heart", "Bacon" -> "bacon"
    """
    # 转换为小写，空格替换为下划线
    normalized = name.lower().replace(' ', '_')
    return normalized

def find_3d_file_in_category(category_name):
    """
    在指定类别目录中查找 3D 文件
    
    Args:
        category_name: 类别目录名，如 "Bacon", "Red heart"
    
    Returns:
        str: 3D 文件名，如果找到的话
    """
    try:
        # 获取 3D 子目录的内容（使用URL编码）
        category_path = f"assets/{category_name}/3D"
        contents = get_github_api_contents(category_path)
        
        if not contents:
            # 如果API失败，尝试直接构建文件名
            normalized = normalize_category_name(category_name)
            return f"{normalized}_3d.png"
        
        # 查找 .png 文件
        for item in contents:
            if item.get('type') == 'file' and item.get('name', '').endswith('_3d.png'):
                return item.get('name')
        
        # 如果没找到，尝试构建文件名
        normalized = normalize_category_name(category_name)
        return f"{normalized}_3d.png"
    except Exception as e:
        # 如果出错，尝试构建文件名
        normalized = normalize_category_name(category_name)
        return f"{normalized}_3d.png"

def emoji_to_category_name(emoji_text):
    """
    将 emoji 转换为可能的 Fluent UI 类别名称
    返回可能的候选名称列表
    """
    # Emoji 到可能的类别名称映射
    emoji_mapping = {
        '❤️': ['Red heart', 'Heart'],
        '⭐': ['Star'],
        '✨': ['Sparkles'],
        '🔥': ['Fire'],
        '😊': ['Smiling face with smiling eyes', 'Smiling face'],
        '🌸': ['Cherry blossom'],
        '👑': ['Crown'],
        '🎀': ['Ribbon'],
        '🎂': ['Birthday cake', 'Cake'],
        '🎁': ['Wrapped gift', 'Gift'],
        '🎈': ['Balloon'],
        '🎵': ['Musical note', 'Note'],
        '😂': ['Face with tears of joy'],
        '😍': ['Smiling face with heart-eyes'],
        '😉': ['Winking face'],
        '😘': ['Face blowing a kiss'],
        '🥳': ['Partying face'],
        '😎': ['Smiling face with sunglasses'],
        '👏': ['Clapping hands'],
        '👍': ['Thumbs up'],
        '😀': ['Grinning face'],
        '🤩': ['Star-struck'],
        '🤗': ['Hugging face'],
        '😄': ['Grinning face with smiling eyes'],
        '😁': ['Beaming face with smiling eyes'],
        '😅': ['Grinning face with sweat'],
        '🤣': ['Rolling on the floor laughing'],
        '🥰': ['Smiling face with hearts'],
        '😚': ['Kissing face with closed eyes'],
        '😛': ['Face with tongue'],
        '😜': ['Winking face with tongue'],
        '🤪': ['Zany face'],
        '🤔': ['Thinking face'],
        '🐼': ['Panda'],
        '🦄': ['Unicorn'],
        '🦋': ['Butterfly'],
        '🐶': ['Dog face', 'Dog'],
        '🐱': ['Cat face', 'Cat'],
        '🐰': ['Rabbit face', 'Rabbit'],
        '🐻': ['Bear face', 'Bear'],
        '🐯': ['Tiger face', 'Tiger'],
        '🦁': ['Lion face', 'Lion'],
        '🦊': ['Fox'],
        '🐨': ['Koala'],
        '🐷': ['Pig face', 'Pig'],
        '🐸': ['Frog'],
        '🐔': ['Chicken'],
        '🐧': ['Penguin'],
        '🦉': ['Owl'],
        '🐝': ['Honeybee', 'Bee'],
        '🐬': ['Dolphin'],
        '🐳': ['Spouting whale', 'Whale'],
        '🐟': ['Fish'],
        '🐢': ['Turtle'],
        '🍦': ['Soft ice cream', 'Ice cream'],
        '🍩': ['Doughnut', 'Donut'],
        '🍕': ['Pizza'],
        '🍓': ['Strawberry'],
        '🍉': ['Watermelon'],
        '🍒': ['Cherries', 'Cherry'],
        '🍭': ['Lollipop'],
        '☕': ['Hot beverage', 'Coffee'],
        '🍎': ['Red apple', 'Apple'],
        '🍊': ['Tangerine', 'Orange'],
        '🍌': ['Banana'],
        '🍇': ['Grapes'],
        '🍑': ['Peach'],
        '🍍': ['Pineapple'],
        '🥭': ['Mango'],
        '🍪': ['Cookie'],
        '🧁': ['Cupcake'],
        '🍔': ['Hamburger'],
        '🍟': ['French fries', 'Fries'],
        '🌮': ['Taco'],
        '🍣': ['Sushi'],
        '🌈': ['Rainbow'],
        '☀️': ['Sun'],
        '🌙': ['Crescent moon', 'Moon'],
        '❄️': ['Snowflake'],
        '⚡': ['Lightning'],
        '💧': ['Droplet'],
        '🌞': ['Sun with face'],
        '🌕': ['Full moon'],
        '🌟': ['Glowing star', 'Star'],
        '☁️': ['Cloud'],
        '🌷': ['Tulip'],
        '🌹': ['Rose'],
        '🌺': ['Hibiscus'],
        '🌻': ['Sunflower'],
        '🍀': ['Four leaf clover'],
        '✅': ['Check mark button'],
        '💯': ['Hundred points'],
        '👌': ['OK hand'],
        '✌️': ['Victory hand'],
        '🤘': ['Sign of the horns'],
        '🤟': ['Love-you gesture'],
        '🤞': ['Crossed fingers'],
        '🤙': ['Call me hand'],
        '💪': ['Flexed biceps'],
        '👉': ['Backhand index pointing right'],
        '👈': ['Backhand index pointing left'],
        '👆': ['Backhand index pointing up'],
        '👇': ['Backhand index pointing down'],
        '🙏': ['Folded hands'],
        '👋': ['Waving hand'],
        '💎': ['Gem stone', 'Diamond'],
        '🚀': ['Rocket'],
        '🏆': ['Trophy'],
        '🏅': ['Sports medal', 'Medal'],
        '📷': ['Camera'],
        '🎊': ['Confetti ball'],
        '🎉': ['Party popper'],
        '🎆': ['Fireworks'],
        '🎇': ['Sparkler'],
        '💜': ['Purple heart'],
        '💚': ['Green heart'],
        '💙': ['Blue heart'],
        '💛': ['Yellow heart'],
        '🧡': ['Orange heart'],
        '💖': ['Sparkling heart'],
        '💕': ['Two hearts'],
        '💘': ['Heart with arrow'],
        '💝': ['Heart with ribbon'],
    }
    
    return emoji_mapping.get(emoji_text, [])

def get_fluent_emoji_url(category, filename):
    """
    构建 Fluent UI Emoji 的下载 URL
    
    Args:
        category: emoji 类别目录名
        filename: 文件名
    
    Returns:
        str: 完整的下载 URL
    """
    category_encoded = urllib.parse.quote(category, safe='')
    filename_encoded = urllib.parse.quote(filename, safe='')
    url = f"{FLUENT_EMOJI_BASE_URL}/{category_encoded}/3D/{filename_encoded}"
    return url

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

def find_and_download_fluent_emoji(emoji_text, sticker_id, name):
    """
    查找并下载 Fluent UI Emoji 3D 版本
    
    Args:
        emoji_text: emoji 字符
        sticker_id: 贴纸 ID
        name: 贴纸名称
    
    Returns:
        tuple: (本地文件名, URL) 或 None
    """
    # 获取可能的类别名称
    category_candidates = emoji_to_category_name(emoji_text)
    
    if not category_candidates:
        return None
    
    # 尝试每个候选类别名称
    for category_name in category_candidates:
        # 先尝试直接构建文件名
        normalized = normalize_category_name(category_name)
        possible_filename = f"{normalized}_3d.png"
        
        # 尝试下载
        url = get_fluent_emoji_url(category_name, possible_filename)
        test_path = FLUENT_3D_DIR / f"test_{possible_filename}"
        
        try:
            urllib.request.urlretrieve(url, test_path)
            # 如果下载成功，删除测试文件
            test_path.unlink()
            # 返回成功的结果
            local_filename = f"{sticker_id}_fluent_3d.png"
            return (local_filename, url)
        except:
            # 如果直接构建失败，尝试通过 API 查找
            actual_filename = find_3d_file_in_category(category_name)
            if actual_filename:
                url = get_fluent_emoji_url(category_name, actual_filename)
                local_filename = f"{sticker_id}_fluent_3d.png"
                return (local_filename, url)
        
        # 避免请求过快
        time.sleep(0.1)
    
    return None

def get_all_categories():
    """
    获取所有可用的 emoji 类别
    
    Returns:
        list: 类别名称列表
    """
    print("正在获取所有 emoji 类别...")
    contents = get_github_api_contents("assets")
    
    if not contents:
        print("⚠️  无法获取类别列表，将使用映射表")
        return []
    
    categories = []
    for item in contents:
        if item.get('type') == 'dir':
            categories.append(item.get('name'))
    
    print(f"找到 {len(categories)} 个类别")
    return categories

def try_download_emoji(category, filename, use_api=False):
    """
    尝试下载单个 emoji 文件
    
    Args:
        category: 类别名
        filename: 文件名
        use_api: 是否使用API查找实际文件名（默认False，直接下载）
    
    Returns:
        tuple: (是否成功, 实际使用的文件名)
    """
    url = get_fluent_emoji_url(category, filename)
    dest_path = FLUENT_3D_DIR / filename
    
    # 检查文件是否已存在
    if dest_path.exists():
        return True, filename
    
    try:
        urllib.request.urlretrieve(url, dest_path)
        # 验证文件是否真的下载了（检查文件大小）
        if dest_path.exists() and dest_path.stat().st_size > 0:
            return True, filename
        else:
            # 文件下载失败，删除空文件
            if dest_path.exists():
                dest_path.unlink()
            return False, filename
    except urllib.error.HTTPError as e:
        if e.code == 404 and use_api:
            # 只有在允许使用API时才尝试查找实际文件名
            actual_filename = find_3d_file_in_category(category)
            if actual_filename and actual_filename != filename:
                url = get_fluent_emoji_url(category, actual_filename)
                dest_path = FLUENT_3D_DIR / actual_filename
                if not dest_path.exists():
                    try:
                        urllib.request.urlretrieve(url, dest_path)
                        if dest_path.exists() and dest_path.stat().st_size > 0:
                            return True, actual_filename
                        else:
                            if dest_path.exists():
                                dest_path.unlink()
                            return False, filename
                    except:
                        return False, filename
                else:
                    return True, actual_filename
        # 下载失败，删除可能存在的空文件
        if dest_path.exists():
            dest_path.unlink()
        return False, filename
    except Exception:
        # 下载失败，删除可能存在的空文件
        if dest_path.exists():
            dest_path.unlink()
        return False, filename

def download_all_3d_emojis():
    """
    遍历所有类别，下载所有 3D emoji
    先尝试直接下载，失败时使用API查找实际文件名
    对失败的项进行2次重试
    """
    print("=" * 60)
    print("  下载 Microsoft Fluent UI Emoji 3D 表情")
    print("  来源: https://github.com/microsoft/fluentui-emoji")
    print("=" * 60)
    print()
    
    # 获取所有类别
    all_categories = get_all_categories()
    
    if not all_categories:
        print("⚠️  无法获取类别列表，使用基于 STICKER_LIST 的下载方式")
        return download_from_sticker_list()
    
    print(f"📦 遍历 {len(all_categories)} 个类别，查找 3D 表情...")
    print()
    
    success_count = 0
    total_count = 0
    failed_items = []
    
    # 第一轮：尝试下载所有文件
    for i, category in enumerate(all_categories):
        normalized = normalize_category_name(category)
        filename = f"{normalized}_3d.png"
        
        # 检查文件是否已存在
        dest_path = FLUENT_3D_DIR / filename
        if dest_path.exists():
            success_count += 1
            total_count += 1
            continue
        
        total_count += 1
        
        # 尝试下载
        print(f"[{i+1}/{len(all_categories)}] [{category}] {filename}: ", end="")
        success, actual_filename = try_download_emoji(category, filename)
        
        if success:
            if actual_filename != filename:
                print(f"✓ (使用实际文件名: {actual_filename})")
            else:
                print("✓")
            success_count += 1
        else:
            print("✗")
            failed_items.append((category, filename))
        
        # 避免请求过快（每10个请求后稍作延迟）
        if (i + 1) % 10 == 0:
            time.sleep(0.2)
        else:
            time.sleep(0.05)
    
    # 重试失败的项（最多2次）
    if failed_items:
        print()
        print(f"🔄 开始重试 {len(failed_items)} 个失败项（最多2次）...")
        print()
        
        for retry_round in range(1, 3):  # 重试2次
            retry_success = []
            retry_failed = []
            
            print(f"  第 {retry_round} 次重试 ({len(failed_items)} 个文件)...")
            
            for category, filename in failed_items:
                print(f"  [{category}] {filename}: ", end="")
                # 重试时不使用API，直接下载
                success, actual_filename = try_download_emoji(category, filename, use_api=False)
                
                if success:
                    if actual_filename != filename:
                        print(f"✓ (使用实际文件名: {actual_filename})")
                    else:
                        print("✓")
                    retry_success.append((category, filename))
                    success_count += 1
                else:
                    print("✗")
                    retry_failed.append((category, filename))
                
                time.sleep(0.1)  # 重试时稍慢一些
            
            failed_items = retry_failed
            
            if retry_success:
                print(f"  ✓ 第 {retry_round} 次重试成功: {len(retry_success)} 个文件")
            if not failed_items:
                print(f"  ✓ 所有文件下载成功！")
                break
            
            if retry_round < 2:
                print(f"  ⚠️  还有 {len(failed_items)} 个文件失败，将进行下一次重试...")
                time.sleep(1)  # 重试间隔稍长
    
    print()
    print(f"✓ 下载完成: {success_count}/{total_count}")
    
    if failed_items:
        print()
        print("⚠️  以下表情下载失败（可能是命名不匹配或不存在3D版本）:")
        for category, filename in failed_items[:30]:  # 只显示前30个
            print(f"  - {category}/{filename}")
        if len(failed_items) > 30:
            print(f"  ... 还有 {len(failed_items) - 30} 个失败项")
    
    print()
    print("=" * 60)
    print("  资源下载完成！")
    print("=" * 60)
    print()
    print(f"3D 表情目录: {FLUENT_3D_DIR}")
    print(f"总计: {total_count} 个文件，成功: {success_count} 个")
    if failed_items:
        print(f"失败: {len(failed_items)} 个")
    print()

def download_from_sticker_list():
    """
    基于 STICKER_LIST 下载对应的 Fluent UI Emoji
    """
    print("📦 基于 STICKER_LIST 下载 Fluent UI 3D 表情...")
    print()
    
    success_count = 0
    failed_items = []
    
    for sticker in STICKER_LIST:
        if 'emoji' not in sticker:
            continue
        
        emoji_text = sticker['emoji']
        sticker_id = sticker.get('id', 'unknown')
        name = sticker.get('name', '')
        
        result = find_and_download_fluent_emoji(emoji_text, sticker_id, name)
        
        if result:
            local_filename, url = result
            dest_path = FLUENT_3D_DIR / local_filename
            
            print(f"[{emoji_text}] {name or sticker_id}: ", end="")
            
            if dest_path.exists():
                print("已存在，跳过")
                success_count += 1
                continue
            
            if download_file(url, dest_path):
                success_count += 1
            else:
                failed_items.append((sticker_id, emoji_text, name))
        else:
            failed_items.append((sticker_id, emoji_text, name))
            print(f"[{emoji_text}] {name or sticker_id}: 未找到对应的 Fluent UI emoji")
    
    print()
    print(f"✓ 下载完成: {success_count}/{len(STICKER_LIST)}")
    
    if failed_items:
        print()
        print("⚠️  以下表情未找到或下载失败:")
        for sticker_id, emoji, name in failed_items[:10]:
            print(f"  - {emoji} {name or sticker_id}")
        if len(failed_items) > 10:
            print(f"  ... 还有 {len(failed_items) - 10} 个失败项")
    
    print()
    print(f"3D 表情目录: {FLUENT_3D_DIR}")
    print()

def main():
    # 默认使用遍历所有类别的方式
    download_all_3d_emojis()

if __name__ == '__main__':
    main()
