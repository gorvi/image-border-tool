# 🚨 快速修复指南 - 更新版

## ⚠️ 重要发现

你的系统 `/usr/bin/python3` **被重定向到了 Xcode 的 Python**，这会导致 Tkinter 崩溃！

即使运行 `/usr/bin/python3`，实际执行的仍然是：
```
/Applications/Xcode.app/Contents/Developer/usr/bin/python3
```

## ✅ 解决方案

### 方案1: 使用 Homebrew Python（推荐）⭐

如果你安装了 Homebrew：

```bash
# 检查是否有 Homebrew Python
brew list python3 2>/dev/null && echo "已安装" || echo "未安装"

# 如果未安装，先安装
brew install python3

# 然后使用 Homebrew 的 Python
/opt/homebrew/bin/python3 main.py
# 或
/usr/local/bin/python3 main.py  # Intel Mac
```

### 方案2: 安装独立的 Python

```bash
# 从 python.org 下载并安装 Python 3.11 或 3.12
# 然后使用安装路径，例如：
/Library/Frameworks/Python.framework/Versions/3.11/bin/python3 main.py
```

### 方案3: 使用程序内置检测（已更新）

程序现在会在启动时自动检测 Xcode Python 并提示：

```bash
# 如果使用 Xcode Python，程序会显示错误并退出
python3 main.py

# 输出会提示你使用正确的 Python
```

### 方案4: 修改 shell 配置（永久解决）

在你的 `~/.zshrc` 或 `~/.bash_profile` 中添加：

```bash
# 优先使用 Homebrew Python（如果已安装）
if [ -f /opt/homebrew/bin/python3 ]; then
    export PATH="/opt/homebrew/bin:$PATH"
elif [ -f /usr/local/bin/python3 ]; then
    export PATH="/usr/local/bin:$PATH"
fi
```

然后重新加载：
```bash
source ~/.zshrc
```

## 🔍 检查当前 Python

运行以下命令检查：

```bash
# 检查当前使用的 Python
python3 -c "import sys; print('路径:', sys.executable)"

# 检查是否是 Xcode Python
python3 -c "import sys; print('Xcode Python' if 'Xcode.app' in sys.executable else '系统Python')"
```

## 📝 推荐操作步骤

1. **检查是否有 Homebrew Python**
   ```bash
   ls -la /opt/homebrew/bin/python3* 2>/dev/null || ls -la /usr/local/bin/python3* 2>/dev/null
   ```

2. **如果有，直接使用**
   ```bash
   /opt/homebrew/bin/python3 main.py  # Apple Silicon
   # 或
   /usr/local/bin/python3 main.py    # Intel
   ```

3. **如果没有，安装 Homebrew Python**
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   brew install python3
   /opt/homebrew/bin/python3 main.py
   ```

## ⚡ 最快解决方案

**如果你有 Homebrew：**
```bash
/opt/homebrew/bin/python3 main.py
```

**如果没有 Homebrew，先安装：**
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew install python3
/opt/homebrew/bin/python3 main.py
```

---

**程序已更新，会自动检测并阻止使用 Xcode Python！** ✅
