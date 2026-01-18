#!/usr/bin/env python3
"""
快速重试：只处理缺失的文件，最多重试2次
通过直接尝试下载来避免API速率限制
"""

import urllib.request
import urllib.parse
import time
from pathlib import Path

# 创建目录
ASSETS_DIR = Path(__file__).parent / 'assets'
FLUENT_3D_DIR = ASSETS_DIR / 'stickers' / 'fluent_3d'
FLUENT_EMOJI_BASE_URL = 'https://raw.githubusercontent.com/microsoft/fluentui-emoji/main/assets'

def normalize_category_name(name):
    """将目录名转换为文件名格式"""
    return name.lower().replace(' ', '_')

def get_fluent_emoji_url(category, filename):
    """构建下载 URL"""
    category_encoded = urllib.parse.quote(category, safe='')
    filename_encoded = urllib.parse.quote(filename, safe='')
    return f"{FLUENT_EMOJI_BASE_URL}/{category_encoded}/3D/{filename_encoded}"

def try_download(category, filename):
    """尝试下载文件"""
    url = get_fluent_emoji_url(category, filename)
    dest_path = FLUENT_3D_DIR / filename
    
    if dest_path.exists():
        return True
    
    try:
        urllib.request.urlretrieve(url, dest_path)
        return True
    except:
        return False

def get_category_list_from_api():
    """从API获取类别列表（带重试）"""
    import json
    
    for attempt in range(3):
        try:
            encoded_path = urllib.parse.quote("assets", safe='/')
            api_url = f"https://api.github.com/repos/microsoft/fluentui-emoji/contents/{encoded_path}"
            req = urllib.request.Request(api_url)
            req.add_header('Accept', 'application/vnd.github.v3+json')
            req.add_header('User-Agent', 'Mozilla/5.0')
            
            with urllib.request.urlopen(req, timeout=15) as response:
                data = json.loads(response.read().decode())
                categories = [item.get('name') for item in data if item.get('type') == 'dir']
                return categories
        except Exception as e:
            if attempt < 2:
                print(f"  API请求失败，等待 {3 * (attempt + 1)} 秒后重试...")
                time.sleep(3 * (attempt + 1))
            else:
                print(f"  API请求最终失败: {e}")
    return None

def main():
    print("=" * 60)
    print("  快速重试：下载缺失的 Fluent UI Emoji 3D 表情")
    print("=" * 60)
    print()
    
    # 获取类别列表
    print("正在获取类别列表...")
    categories = get_category_list_from_api()
    
    if not categories:
        print("⚠️  无法获取类别列表，请稍后重试")
        return
    
    print(f"找到 {len(categories)} 个类别")
    print()
    
    # 找出缺失的文件
    print("检查缺失的文件...")
    missing = []
    for category in categories:
        normalized = normalize_category_name(category)
        filename = f"{normalized}_3d.png"
        dest_path = FLUENT_3D_DIR / filename
        
        if not dest_path.exists():
            missing.append((category, filename))
    
    if not missing:
        print("✓ 所有文件都已下载成功！")
        return
    
    print(f"找到 {len(missing)} 个缺失的文件")
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
            print(f"  [{i+1}/{len(missing)}] [{category}] {filename}: ", end="")
            
            if try_download(category, filename):
                print("✓")
                success_count += 1
            else:
                print("✗")
                still_missing.append((category, filename))
            
            # 避免请求过快
            if (i + 1) % 20 == 0:
                time.sleep(0.5)
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
            time.sleep(2)
    
    print()
    print("=" * 60)
    print("  重试完成！")
    print("=" * 60)
    print()
    
    if missing:
        print(f"⚠️  仍有 {len(missing)} 个文件下载失败:")
        for category, filename in missing[:30]:
            print(f"  - {category}/{filename}")
        if len(missing) > 30:
            print(f"  ... 还有 {len(missing) - 30} 个失败项")
    else:
        print("✓ 所有文件都已成功下载！")
    print()

if __name__ == '__main__':
    main()
