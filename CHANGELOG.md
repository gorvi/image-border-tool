# 更新日志

## 2026-01-14 - v0.2.0

### ✨ 新功能

1. **开源资源集成**
   - 集成 Google Noto Emoji 开源贴纸（12个）
   - 自动生成 5 种边框样式预览图
   - 支持自定义添加PNG贴纸和边框

2. **界面优化**
   - 右侧面板改为标签页布局（基础/装饰/批量）
   - 窗口自适应屏幕大小（85%屏幕尺寸）
   - 设置最小窗口尺寸限制（1200x700）
   - 窗口居中显示

3. **图片编辑功能**
   - 逆时针旋转90°
   - 顺时针旋转90°
   - 水平翻转
   - 垂直翻转

4. **尺寸预设**
   - 新增小红书 4:3 尺寸（1242x1656）

### 🔧 改进

1. **自适应逻辑**
   - 窗口大小改变时自动调整画布
   - 防抖处理避免频繁触发

2. **资源管理**
   - 创建完整的资源目录结构（assets/stickers/borders/fonts）
   - 提供自动下载脚本（download_assets.py）
   - 提供边框生成脚本（generate_borders.py）

3. **文档完善**
   - 添加资源目录说明文档（assets/README.md）
   - 添加更新日志（CHANGELOG.md）

### 📦 资源文件

**贴纸** (12个 PNG 图片):
- heart.png, star.png, smile.png, fire.png
- sparkles.png, flower.png, crown.png, ribbon.png
- cake.png, gift.png, balloon.png, music.png

**边框** (5个预览图):
- simple.png - 简单边框
- thick.png - 粗边框
- double.png - 双线边框
- rounded.png - 圆角边框
- decorative.png - 装饰边框

---

## 2026-01-13 - v0.1.0

### 🎉 初始版本

- 基础图片套版功能
- 尺寸选择（证件照、海报等）
- 图片上传和裁剪
- 基础贴纸（Emoji）
- 基础边框样式
- 批量处理功能
- 撤销/重做功能
- 导出PNG/JPG
