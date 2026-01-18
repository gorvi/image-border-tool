#!/usr/bin/env python3
"""
检查并下载缺失的 Fluent UI Emoji 3D 表情
获取完整类别列表，检查缺失文件，然后直接下载（不使用API）
"""

import urllib.request
import urllib.parse
import json
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

def get_all_categories():
    """获取所有类别（仅使用一次API）"""
    print("正在获取所有类别列表...")
    
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
                wait_time = 3 * (attempt + 1)
                print(f"  第 {attempt + 1} 次尝试失败，等待 {wait_time} 秒后重试...")
                time.sleep(wait_time)
            else:
                print(f"  ⚠️  无法获取类别列表: {e}")
                return None
    
    return None

def try_download(category, filename):
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
    except urllib.error.HTTPError as e:
        if dest_path.exists():
            dest_path.unlink()
        return False
    except Exception as e:
        if dest_path.exists():
            dest_path.unlink()
        return False

def main():
    print("=" * 60)
    print("  检查并下载缺失的 Fluent UI Emoji 3D 表情")
    print("=" * 60)
    print()
    
    # 获取所有类别
    all_categories = get_all_categories()
    
    if not all_categories:
        print("⚠️  无法获取类别列表，请稍后重试")
        return
    
    print(f"找到 {len(all_categories)} 个类别")
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
        print("✓ 所有文件都已下载成功！")
        return
    
    # 下载缺失的文件（重试2次）
    for retry_round in range(1, 3):
        if not missing:
            break
        
        print(f"🔄 第 {retry_round} 次尝试下载 ({len(missing)} 个文件)...")
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
            time.sleep(2)
    
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
