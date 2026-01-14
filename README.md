# 🎨 图片套版工具

一个简单易用的图片套版处理软件，支持图片裁剪、贴纸、边框和批量处理功能。

> ✨ **v0.2.0 更新** - 集成开源贴纸、优化界面布局、新增图片编辑功能！  
> 📖 查看 [快速开始.md](快速开始.md) 快速上手

## 🎯 功能特性

### 核心功能
- 📐 **多种预设尺寸** - 证件照（1寸/2寸）、正方形、小红书4:3、海报（横版/竖版）
- 🖼️ **图片编辑** - 旋转（顺时针/逆时针）、翻转（水平/垂直）
- 🎨 **12个开源贴纸** - Google Noto Emoji（❤️⭐😊🔥✨🌸👑🎀🎂🎁🎈🎵）
- 🖼️ **5种边框样式** - 简单、粗边框、双线、圆角、装饰
- ⚡ **批量处理** - 一键应用到多张图片
- 💾 **快速导出** - PNG/JPG格式
- ↶↷ **撤销重做** - 支持多步操作历史

### 界面特点
- 📑 **标签页布局** - 基础编辑 / 装饰 / 批量处理
- 📱 **自适应窗口** - 根据屏幕自动调整（85%屏幕尺寸）
- 🎨 **网格式选择** - 贴纸4列网格布局，直观易用

## 安装和运行

### ⚠️ 重要提示

**如果你的系统 `/usr/bin/python3` 指向 Xcode Python，程序会自动检测并阻止运行。**

请查看 [SOLUTION.md](SOLUTION.md) 了解完整解决方案。

### 1. 安装依赖

**推荐使用 Homebrew Python：**
```bash
# 如果使用 Homebrew Python
/opt/homebrew/bin/python3 -m pip install -r requirements.txt
```

**或使用系统 Python（如果可用）：**
```bash
pip3 install -r requirements.txt
```

**注意**: 如果遇到 macOS 兼容性问题，请使用：
```bash
pip3 install Pillow==10.0.0
```

### 2. 运行程序

**推荐方式（使用 Homebrew Python）：**
```bash
/opt/homebrew/bin/python3 main.py  # Apple Silicon
# 或
/usr/local/bin/python3 main.py     # Intel
```

**或使用启动脚本：**
```bash
./start.sh  # 最安全的启动方式
```

**注意**: 如果程序提示使用了 Xcode Python，请按照提示操作。

### 3. 测试安装
```bash
/opt/homebrew/bin/python3 test_import.py  # 使用 Homebrew Python
```

## 使用说明

1. **选择尺寸**：从左侧面板选择预设尺寸或自定义尺寸
2. **上传图片**：点击"上传图片"按钮选择图片
3. **编辑图片**：
   - 使用裁剪工具调整图片区域
   - 添加贴纸装饰
   - 选择边框样式
4. **批量处理**：上传多张图片，一键批量生成
5. **导出**：点击"导出图片"保存最终结果

## 系统要求

- Python 3.8+
- macOS / Windows / Linux

## 快捷键

- `Cmd+Z` / `Ctrl+Z`：撤销
- `Cmd+Shift+Z` / `Ctrl+Y`：重做
- `Cmd+S` / `Ctrl+S`：保存/导出

## 技术栈

- Python 3
- Tkinter (GUI)
- Pillow (图片处理)

## 故障排除

### 问题: Tkinter 崩溃 (Abort trap: 6)
**错误信息**: `Abort trap: 6` 或 `TkpInit` 崩溃

**原因**: Xcode 自带的 Python 与系统 Tkinter 不兼容

**解决方案（推荐）**:
```bash
# 方式1: 使用系统Python启动脚本
./run_system_python.sh

# 方式2: 直接使用系统Python
/usr/bin/python3 main.py

# 方式3: 更新启动脚本（已自动优先使用系统Python）
./run.sh
```

### 问题: macOS 版本不兼容错误
**错误信息**: `macOS 26 (2601) or later required, have instead 16 (1601)`

**解决方案**:
```bash
pip3 uninstall Pillow
pip3 install Pillow==10.0.0
```

### 问题: 模块导入失败
**解决方案**: 确保在项目目录下运行
```bash
cd /Users/ghw/Documents/cursor_ws/tupian
/usr/bin/python3 main.py  # 使用系统Python
```

### 问题: Tkinter 不可用
**macOS**: Tkinter 是系统自带的，通常无需安装  
**Linux**: 需要安装 `python3-tk` 包
```bash
sudo apt-get install python3-tk  # Ubuntu/Debian
```
