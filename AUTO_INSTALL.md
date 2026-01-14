# 🚀 自动安装指南

## ⚡ 一键安装命令

**在终端中运行以下命令（需要输入密码）：**

```bash
cd /Users/ghw/Documents/cursor_ws/tupian

# 运行自动安装脚本
./install_python.sh
```

**或者手动执行以下步骤：**

## 📋 手动安装步骤

### 步骤 1: 安装 Homebrew

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

**注意事项：**
- 安装过程可能需要 5-10 分钟
- 会要求输入管理员密码
- 可能需要按 Enter 确认

### 步骤 2: 安装 Python

```bash
# Apple Silicon Mac
/opt/homebrew/bin/brew install python3

# Intel Mac
/usr/local/bin/brew install python3
```

### 步骤 3: 安装项目依赖

```bash
cd /Users/ghw/Documents/cursor_ws/tupian

# Apple Silicon
/opt/homebrew/bin/python3 -m pip install --user -r requirements.txt

# Intel
/usr/local/bin/python3 -m pip install --user -r requirements.txt
```

### 步骤 4: 运行程序

```bash
# Apple Silicon
/opt/homebrew/bin/python3 main.py

# Intel
/usr/local/bin/python3 main.py
```

## 🎯 快速命令（复制粘贴）

**完整安装流程（Apple Silicon）：**

```bash
cd /Users/ghw/Documents/cursor_ws/tupian && \
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" && \
/opt/homebrew/bin/brew install python3 && \
/opt/homebrew/bin/python3 -m pip install --user -r requirements.txt && \
/opt/homebrew/bin/python3 main.py
```

**完整安装流程（Intel）：**

```bash
cd /Users/ghw/Documents/cursor_ws/tupian && \
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" && \
/usr/local/bin/brew install python3 && \
/usr/local/bin/python3 -m pip install --user -r requirements.txt && \
/usr/local/bin/python3 main.py
```

## ✅ 验证安装

安装完成后，验证 Python 不是 Xcode 版本：

```bash
# Apple Silicon
/opt/homebrew/bin/python3 -c "import sys; print('✓ OK' if 'Xcode' not in sys.executable else '✗ Xcode Python')"

# Intel
/usr/local/bin/python3 -c "import sys; print('✓ OK' if 'Xcode' not in sys.executable else '✗ Xcode Python')"
```

应该显示：`✓ OK`

## 🔄 后续使用

安装完成后，可以使用启动脚本：

```bash
./start.sh
```

启动脚本会自动检测并使用正确的 Python。

## ❓ 遇到问题？

1. **网络问题**：确保网络连接正常
2. **权限问题**：确保有管理员权限
3. **安装失败**：查看错误信息，可能需要手动安装

---

**推荐：直接运行 `./install_python.sh` 脚本，它会引导你完成所有步骤！** ✅
