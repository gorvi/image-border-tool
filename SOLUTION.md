# 🔧 最终解决方案

## 问题诊断

你的系统配置导致**所有 `python3` 命令都指向 Xcode 的 Python**，这会导致 Tkinter 崩溃。

**当前状态：**
- ❌ `/usr/bin/python3` → 重定向到 Xcode Python
- ❌ `python3` 命令 → 使用 Xcode Python
- ❌ 未安装 Homebrew Python
- ✅ 程序已更新，会自动检测并阻止 Xcode Python

## ✅ 推荐解决方案

### 方案1: 安装 Homebrew Python（最佳）⭐

**步骤：**

1. **安装 Homebrew**（如果还没有）
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

2. **安装 Python**
   ```bash
   brew install python3
   ```

3. **运行程序**
   ```bash
   # Apple Silicon Mac
   /opt/homebrew/bin/python3 main.py
   
   # Intel Mac
   /usr/local/bin/python3 main.py
   ```

4. **（可选）设置为默认 Python**
   在 `~/.zshrc` 中添加：
   ```bash
   # 优先使用 Homebrew Python
   if [ -f /opt/homebrew/bin/python3 ]; then
       alias python3='/opt/homebrew/bin/python3'
       export PATH="/opt/homebrew/bin:$PATH"
   elif [ -f /usr/local/bin/python3 ]; then
       alias python3='/usr/local/bin/python3'
       export PATH="/usr/local/bin:$PATH"
   fi
   ```
   然后运行：`source ~/.zshrc`

### 方案2: 从 python.org 安装独立 Python

1. **下载 Python**
   - 访问：https://www.python.org/downloads/
   - 下载 Python 3.11 或 3.12 for macOS

2. **安装**
   - 运行下载的安装包
   - 安装到默认位置：`/Library/Frameworks/Python.framework/`

3. **运行程序**
   ```bash
   /Library/Frameworks/Python.framework/Versions/3.11/bin/python3 main.py
   ```

### 方案3: 使用 pyenv（高级用户）

```bash
# 安装 pyenv
brew install pyenv

# 安装 Python 3.11
pyenv install 3.11.0

# 设置为本地版本
cd /Users/ghw/Documents/cursor_ws/tupian
pyenv local 3.11.0

# 运行程序
python3 main.py
```

## 🚀 快速开始（推荐）

**如果你愿意安装 Homebrew（约5分钟）：**

```bash
# 1. 安装 Homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 2. 安装 Python
brew install python3

# 3. 运行程序
/opt/homebrew/bin/python3 /Users/ghw/Documents/cursor_ws/tupian/main.py
```

**如果不想安装 Homebrew：**

从 python.org 下载并安装 Python，然后使用完整路径运行。

## 📋 验证安装

安装后，验证 Python 不是 Xcode 版本：

```bash
# 检查 Python 路径
/opt/homebrew/bin/python3 -c "import sys; print(sys.executable)"

# 应该显示类似：
# /opt/homebrew/bin/python3.11
# 而不是：
# /Applications/Xcode.app/...
```

## 🔄 更新启动脚本

安装 Homebrew Python 后，可以更新启动脚本：

```bash
# 编辑 run.sh，将 PYTHON_CMD 改为：
PYTHON_CMD="/opt/homebrew/bin/python3"  # Apple Silicon
# 或
PYTHON_CMD="/usr/local/bin/python3"     # Intel
```

## ⚠️ 临时解决方案（不推荐）

如果你暂时无法安装新的 Python，可以考虑：

1. **使用在线 Python 环境**（如 Replit、Google Colab）
2. **使用 Docker**（如果已安装）
3. **等待系统更新**（macOS 可能会修复这个问题）

## 📞 需要帮助？

如果遇到问题，请提供：
1. `python3 -c "import sys; print(sys.executable)"` 的输出
2. `which python3` 的输出
3. 是否已安装 Homebrew：`which brew`

---

**推荐：安装 Homebrew Python，这是最稳定和长期的解决方案！** ✅
