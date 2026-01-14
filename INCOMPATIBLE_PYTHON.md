# ⚠️ 不兼容的 Python 版本

## 问题说明

以下 Python 版本与 Tkinter 不兼容，会导致程序崩溃：

### ❌ 不兼容的 Python 版本

1. **Xcode Python**
   - 路径包含: `Xcode.app`
   - 示例: `/Applications/Xcode.app/.../python3`

2. **CommandLineTools Python**
   - 路径包含: `CommandLineTools`
   - 示例: `/Library/Developer/CommandLineTools/.../python3`

3. **系统 Python（某些情况）**
   - 路径: `/usr/bin/python3`（如果重定向到 Xcode/CommandLineTools）

### ✅ 兼容的 Python 版本

1. **Homebrew Python**（推荐）⭐
   - Apple Silicon: `/opt/homebrew/bin/python3`
   - Intel: `/usr/local/bin/python3`

2. **从 python.org 安装的独立 Python**
   - 路径: `/Library/Frameworks/Python.framework/.../python3`

## 🔍 如何检查

运行以下命令检查当前 Python：

```bash
python3 -c "import sys; print(sys.executable)"
```

如果路径包含 `Xcode.app` 或 `CommandLineTools`，说明使用了不兼容的版本。

## ✅ 解决方案

### 方案1: 使用 Homebrew Python（推荐）

```bash
# 安装 Homebrew Python（如果还没有）
./install_python.sh

# 使用 Homebrew Python 运行
/opt/homebrew/bin/python3 main.py
```

### 方案2: 使用启动脚本

启动脚本会自动检测并使用正确的 Python：

```bash
./start.sh
```

### 方案3: 程序自动检测

程序现在会自动检测不兼容的 Python 并提示：

```bash
python3 main.py
```

如果检测到不兼容版本，程序会显示错误信息并退出。

## 📝 已更新的文件

1. **main.py** - 检测所有不兼容的 Python 版本
2. **start.sh** - 启动前检查 Python 兼容性
3. **install_python.sh** - 自动安装兼容的 Python

## 🎯 推荐操作

**始终使用 Homebrew Python：**

```bash
/opt/homebrew/bin/python3 main.py
```

或使用启动脚本：

```bash
./start.sh
```

---

**重要提示**: 如果程序崩溃，请检查是否使用了不兼容的 Python 版本！
