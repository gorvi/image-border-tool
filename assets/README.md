# 资源目录说明

## 📁 目录结构

```
assets/
├── stickers/    # 贴纸资源 (PNG 图片)
├── borders/     # 边框预览图
└── fonts/       # 字体文件（可选）
```

## 🎨 贴纸资源

当前贴纸来自 **Google Noto Emoji** 开源项目。

- 格式: PNG (128x128)
- 许可: Apache License 2.0
- 来源: https://github.com/googlefonts/noto-emoji

### 已包含的贴纸

1. heart.png - 红心
2. star.png - 星星
3. smile.png - 笑脸
4. fire.png - 火焰
5. sparkles.png - 闪光
6. flower.png - 花朵
7. crown.png - 皇冠
8. ribbon.png - 蝴蝶结
9. cake.png - 蛋糕
10. gift.png - 礼物
11. balloon.png - 气球
12. music.png - 音符

## 🖼️ 边框资源

边框预览图由程序生成。

### 已包含的边框

1. simple.png - 简单边框
2. thick.png - 粗边框
3. double.png - 双线边框
4. rounded.png - 圆角边框
5. decorative.png - 装饰边框

## 📝 添加自定义资源

### 添加贴纸

1. 将 PNG 图片放入 `stickers/` 目录
2. 更新 `constants.py` 中的 `STICKER_LIST`
3. 建议尺寸: 128x128 或 256x256

### 添加边框

1. 将边框图片放入 `borders/` 目录
2. 更新 `constants.py` 中的 `BORDER_STYLES_WITH_PREVIEW`

## 🔄 重新下载资源

运行以下命令重新下载贴纸：

```bash
python3 download_assets.py
```

运行以下命令重新生成边框：

```bash
python3 generate_borders.py
```

## 📜 许可信息

- Noto Emoji: Apache License 2.0
- 边框预览图: MIT License（本项目生成）

## 🌐 相关资源

- Noto Emoji: https://github.com/googlefonts/noto-emoji
- Twemoji: https://github.com/twitter/twemoji
- OpenMoji: https://openmoji.org/

---

**最后更新**: 2026-01-14
