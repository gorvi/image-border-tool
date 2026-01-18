#!/usr/bin/env python3
"""
重试之前下载失败的 Fluent UI Emoji 3D 表情
只处理失败的项，最多重试2次
"""

import os
import sys
import urllib.request
import urllib.parse
import json
import time
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

# 创建目录
ASSETS_DIR = Path(__file__).parent / 'assets'
FLUENT_3D_DIR = ASSETS_DIR / 'stickers' / 'fluent_3d'

FLUENT_3D_DIR.mkdir(parents=True, exist_ok=True)

# Fluent UI Emoji 基础 URL
FLUENT_EMOJI_BASE_URL = 'https://raw.githubusercontent.com/microsoft/fluentui-emoji/main/assets'

def normalize_category_name(name):
    """将目录名转换为文件名格式"""
    return name.lower().replace(' ', '_')

def get_fluent_emoji_url(category, filename):
    """构建 Fluent UI Emoji 的下载 URL"""
    category_encoded = urllib.parse.quote(category, safe='')
    filename_encoded = urllib.parse.quote(filename, safe='')
    url = f"{FLUENT_EMOJI_BASE_URL}/{category_encoded}/3D/{filename_encoded}"
    return url

def get_github_api_contents(path):
    """使用 GitHub API 获取目录内容"""
    try:
        encoded_path = urllib.parse.quote(path, safe='/')
        api_url = f"https://api.github.com/repos/microsoft/fluentui-emoji/contents/{encoded_path}"
        req = urllib.request.Request(api_url)
        req.add_header('Accept', 'application/vnd.github.v3+json')
        req.add_header('User-Agent', 'Mozilla/5.0')
        
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            return data
    except:
        return None

def find_3d_file_in_category(category_name):
    """在指定类别目录中查找 3D 文件"""
    try:
        category_path = f"assets/{category_name}/3D"
        contents = get_github_api_contents(category_path)
        
        if not contents:
            normalized = normalize_category_name(category_name)
            return f"{normalized}_3d.png"
        
        for item in contents:
            if item.get('type') == 'file' and item.get('name', '').endswith('_3d.png'):
                return item.get('name')
        
        normalized = normalize_category_name(category_name)
        return f"{normalized}_3d.png"
    except:
        normalized = normalize_category_name(category_name)
        return f"{normalized}_3d.png"

def try_download(category, filename):
    """尝试下载单个文件"""
    # 先尝试使用原始文件名
    url = get_fluent_emoji_url(category, filename)
    dest_path = FLUENT_3D_DIR / filename
    
    if dest_path.exists():
        return True, filename
    
    try:
        urllib.request.urlretrieve(url, dest_path)
        return True, filename
    except urllib.error.HTTPError as e:
        if e.code == 404:
            # 尝试通过API查找实际文件名
            actual_filename = find_3d_file_in_category(category)
            if actual_filename and actual_filename != filename:
                url = get_fluent_emoji_url(category, actual_filename)
                dest_path = FLUENT_3D_DIR / actual_filename
                if not dest_path.exists():
                    try:
                        urllib.request.urlretrieve(url, dest_path)
                        return True, actual_filename
                    except:
                        return False, filename
                else:
                    return True, actual_filename
        return False, filename
    except Exception:
        return False, filename

def get_failed_categories():
    """获取所有类别，找出未下载成功的"""
    print("正在获取所有 emoji 类别...")
    
    # 尝试多次获取类别列表
    contents = None
    for attempt in range(3):
        contents = get_github_api_contents("assets")
        if contents:
            break
        print(f"  第 {attempt + 1} 次尝试获取类别列表失败，等待后重试...")
        time.sleep(2)
    
    if not contents:
        print("⚠️  无法获取类别列表，尝试从已下载文件推断...")
        # 如果API失败，我们可以尝试一些常见的类别
        # 但更好的方法是让用户手动指定或使用之前的失败列表
        return []
    
    categories = []
    for item in contents:
        if item.get('type') == 'dir':
            categories.append(item.get('name'))
    
    print(f"找到 {len(categories)} 个类别")
    
    # 找出未下载成功的类别
    failed = []
    for category in categories:
        normalized = normalize_category_name(category)
        filename = f"{normalized}_3d.png"
        dest_path = FLUENT_3D_DIR / filename
        
        if not dest_path.exists():
            failed.append((category, filename))
    
    return failed

def main():
    print("=" * 60)
    print("  重试下载失败的 Fluent UI Emoji 3D 表情")
    print("=" * 60)
    print()
    
    # 获取失败的类别
    failed_items = get_failed_categories()
    
    if not failed_items:
        print("✓ 所有文件都已下载成功！")
        return
    
    print(f"📦 找到 {len(failed_items)} 个未下载的文件")
    print()
    
    success_count = 0
    
    # 重试2次
    for retry_round in range(1, 3):
        if not failed_items:
            break
        
        print(f"🔄 第 {retry_round} 次重试 ({len(failed_items)} 个文件)...")
        print()
        
        retry_failed = []
        
        for i, (category, filename) in enumerate(failed_items):
            print(f"  [{i+1}/{len(failed_items)}] [{category}] {filename}: ", end="")
            success, actual_filename = try_download(category, filename)
            
            if success:
                if actual_filename != filename:
                    print(f"✓ (使用实际文件名: {actual_filename})")
                else:
                    print("✓")
                success_count += 1
            else:
                print("✗")
                retry_failed.append((category, filename))
            
            # 避免请求过快
            if (i + 1) % 10 == 0:
                time.sleep(0.3)
            else:
                time.sleep(0.1)
        
        failed_items = retry_failed
        
        if retry_failed:
            print()
            print(f"  ⚠️  第 {retry_round} 次重试后还有 {len(retry_failed)} 个文件失败")
        else:
            print()
            print(f"  ✓ 第 {retry_round} 次重试完成，所有文件下载成功！")
        
        if retry_round < 2 and retry_failed:
            print()
            time.sleep(1)
    
    print()
    print("=" * 60)
    print("  重试完成！")
    print("=" * 60)
    print()
    print(f"成功下载: {success_count} 个文件")
    if failed_items:
        print(f"仍然失败: {len(failed_items)} 个文件")
        print()
        print("失败的项:")
        for category, filename in failed_items[:20]:
            print(f"  - {category}/{filename}")
        if len(failed_items) > 20:
            print(f"  ... 还有 {len(failed_items) - 20} 个失败项")
    print()

if __name__ == '__main__':
    main()
