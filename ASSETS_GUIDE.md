# 资源使用指南

## 📦 当前资源

### 贴纸资源

程序已自动下载 **12 个开源贴纸**（来自 Google Noto Emoji）：

1. ❤️ 爱心 (heart.png)
2. ⭐ 星星 (star.png)
3. 😊 笑脸 (smile.png)
4. 🔥 火焰 (fire.png)
5. ✨ 闪光 (sparkles.png)
6. 🌸 花朵 (flower.png)
7. 👑 皇冠 (crown.png)
8. 🎀 蝴蝶结 (ribbon.png)
9. 🎂 蛋糕 (cake.png)
10. 🎁 礼物 (gift.png)
11. 🎈 气球 (balloon.png)
12. 🎵 音符 (music.png)

### 边框资源

程序已自动生成 **5 个边框预览图**：

1. 简单边框 (simple.png)
2. 粗边框 (thick.png)
3. 双线边框 (double.png)
4. 圆角边框 (rounded.png)
5. 装饰边框 (decorative.png)

## 🔄 重新下载资源

如果资源文件丢失或损坏，可以重新下载：

```bash
# 下载贴纸
python3 download_assets.py

# 生成边框
python3 generate_borders.py
```

## ➕ 添加自定义资源

### 添加自定义贴纸

1. **准备PNG图片**
   - 推荐尺寸: 128x128 或 256x256
   - 格式: PNG（支持透明背景）
   - 文件名: 英文小写，如 `custom_heart.png`

2. **放置文件**
   ```bash
   cp your_sticker.png assets/stickers/
   ```

3. **更新配置**（可选）
   编辑 `constants.py`，在 `STICKER_LIST` 中添加：
   ```python
   {'id': 'custom_heart', 'emoji': '💗', 'name': '自定义心', 'file': 'custom_heart.png'}
   ```

### 添加自定义边框

1. **准备边框图片**
   - 推荐尺寸: 200x200（预览图）
   - 格式: PNG（透明背景）
   - 文件名: 英文小写，如 `vintage.png`

2. **放置文件**
   ```bash
   cp vintage_border.png assets/borders/
   ```

3. **更新配置**
   编辑 `constants.py`，在 `BORDER_STYLES_WITH_PREVIEW` 中添加：
   ```python
   {'id': 'vintage', 'name': '复古边框', 'width': 15, 'color': '#8B4513', 'preview': 'vintage.png'}
   ```

## 🌐 推荐的开源资源

### 贴纸/Emoji

1. **Google Noto Emoji** ✅ 当前使用
   - 网址: https://github.com/googlefonts/noto-emoji
   - 许可: Apache License 2.0

2. **Twemoji** (Twitter Emoji)
   - 网址: https://github.com/twitter/twemoji
   - 许可: CC-BY 4.0
   - 下载: 提供SVG和PNG格式

3. **OpenMoji**
   - 网址: https://openmoji.org/
   - 许可: CC BY-SA 4.0
   - 特点: 开源设计，风格统一

4. **Fluent Emoji** (Microsoft)
   - 网址: https://github.com/microsoft/fluentui-emoji
   - 许可: MIT License
   - 特点: 3D风格，现代设计

### 边框/装饰

1. **Unsplash** (部分边框设计)
   - 网址: https://unsplash.com/
   - 许可: Unsplash License（免费商用）

2. **Pexels**
   - 网址: https://www.pexels.com/
   - 许可: 免费商用

3. **自己设计**
   - 使用 Figma/Sketch/Photoshop 设计
   - 或使用 Python Pillow 编程生成

## 📋 批量下载示例

如果想批量添加更多 Noto Emoji：

```python
# 创建 download_more_emojis.py
import urllib.request
from pathlib import Path

STICKERS_DIR = Path('assets/stickers')
STICKERS_DIR.mkdir(parents=True, exist_ok=True)

# 更多emoji的unicode编码
emojis = [
    ('sunglasses', 'emoji_u1f60e'),  # 😎
    ('party', 'emoji_u1f973'),        # 🥳
    ('cool', 'emoji_u1f192'),         # 🆒
    # 添加更多...
]

for name, code in emojis:
    url = f'https://raw.githubusercontent.com/googlefonts/noto-emoji/main/png/128/{code}.png'
    dest = STICKERS_DIR / f'{name}.png'
    try:
        urllib.request.urlretrieve(url, dest)
        print(f'✓ {name}.png')
    except:
        print(f'✗ {name}.png')
```

然后运行：
```bash
python3 download_more_emojis.py
```

## ⚖️ 许可注意事项

- **Google Noto Emoji**: Apache License 2.0（可商用，需保留版权声明）
- **Twemoji**: CC-BY 4.0（可商用，需署名）
- **OpenMoji**: CC BY-SA 4.0（可商用，需署名和相同许可）

使用前请确认许可证要求！

---

**最后更新**: 2026-01-14
