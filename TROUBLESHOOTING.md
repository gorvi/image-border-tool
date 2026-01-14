# 故障排除指南 🔧

## 常见问题及解决方案

### ❌ 问题1: Tkinter 崩溃 (Abort trap: 6)

**症状**:
```
Abort trap: 6
TkpInit + 452
```

**原因**:
- Xcode 自带的 Python (`/Applications/Xcode.app/.../python3`) 与系统 Tkinter 不兼容
- macOS 26.1 系统版本较新，Xcode Python 的 Tkinter 模块可能有问题

**解决方案**:

#### 方案1: 使用系统 Python（推荐）⭐
```bash
# 直接使用系统Python
/usr/bin/python3 main.py

# 或使用专用启动脚本
./run_system_python.sh
```

#### 方案2: 更新启动脚本
```bash
# run.sh 已更新，会自动优先使用系统Python
./run.sh
```

#### 方案3: 检查当前使用的 Python
```bash
# 查看当前Python路径
python3 -c "import sys; print(sys.executable)"

# 如果是Xcode的Python，改用系统Python
which python3
```

**验证修复**:
```bash
# 测试Tkinter是否可用
/usr/bin/python3 -c "import tkinter; print('OK')"
```

---

### ❌ 问题2: Pillow 版本不兼容

**症状**:
```
macOS 26 (2601) or later required, have instead 16 (1601)
```

**解决方案**:
```bash
# 卸载新版本
pip3 uninstall Pillow

# 安装兼容版本
pip3 install Pillow==10.0.0

# 验证
python3 -c "from PIL import Image; print(Image.__version__)"
```

---

### ❌ 问题3: 找不到模块

**症状**:
```
ModuleNotFoundError: No module named 'PIL'
```

**解决方案**:
```bash
# 安装依赖
pip3 install -r requirements.txt

# 或使用系统Python安装
/usr/bin/python3 -m pip install --user -r requirements.txt
```

---

### ❌ 问题4: 权限错误

**症状**:
```
Permission denied
```

**解决方案**:
```bash
# 使用 --user 安装到用户目录
pip3 install --user -r requirements.txt

# 或使用系统Python
/usr/bin/python3 -m pip install --user -r requirements.txt
```

---

### ❌ 问题5: 程序启动但窗口不显示

**可能原因**:
1. 窗口在屏幕外
2. 多显示器配置问题
3. Tkinter 初始化失败

**解决方案**:
```bash
# 检查是否有错误输出
python3 main.py 2>&1 | tee error.log

# 尝试使用系统Python
/usr/bin/python3 main.py
```

---

## 系统环境检查

### 检查 Python 版本
```bash
python3 --version
/usr/bin/python3 --version
```

### 检查 Python 路径
```bash
which python3
python3 -c "import sys; print(sys.executable)"
```

### 检查依赖
```bash
# 检查Pillow
python3 -c "from PIL import Image; print('Pillow OK')"

# 检查Tkinter
python3 -c "import tkinter; print('Tkinter OK')"

# 检查所有模块
python3 test_import.py
```

### 检查系统信息
```bash
# macOS版本
sw_vers

# 架构
uname -m

# Python架构
python3 -c "import platform; print(platform.machine())"
```

---

## 推荐配置

### 最佳实践

1. **使用系统 Python**
   ```bash
   /usr/bin/python3 main.py
   ```

2. **安装依赖到用户目录**
   ```bash
   /usr/bin/python3 -m pip install --user Pillow==10.0.0
   ```

3. **使用启动脚本**
   ```bash
   ./run_system_python.sh  # 最稳定
   ```

---

## 如果问题仍然存在

### 收集诊断信息

```bash
# 创建诊断脚本
cat > diagnose.sh << 'EOF'
#!/bin/bash
echo "=== 系统信息 ==="
sw_vers
echo ""
echo "=== Python信息 ==="
which python3
python3 --version
python3 -c "import sys; print(sys.executable)"
echo ""
echo "=== 依赖检查 ==="
python3 -c "from PIL import Image; print('Pillow:', Image.__version__)" 2>&1
python3 -c "import tkinter; print('Tkinter: OK')" 2>&1
echo ""
echo "=== 模块测试 ==="
python3 test_import.py 2>&1
EOF

chmod +x diagnose.sh
./diagnose.sh > diagnose.log 2>&1
cat diagnose.log
```

### 联系支持

如果问题仍未解决，请提供：
1. `diagnose.log` 文件内容
2. 完整的错误信息
3. 操作系统版本
4. Python 版本和路径

---

## 快速修复命令

```bash
# 一键修复（使用系统Python）
cd /Users/ghw/Documents/cursor_ws/tupian
/usr/bin/python3 -m pip install --user Pillow==10.0.0
/usr/bin/python3 test_import.py
/usr/bin/python3 main.py
```

---

**最后更新**: 2026-01-14
