# MinecraftFRP V2 构建指南

## 📋 快速开始

### 方法 1: 快速构建（推荐）
```bash
python quick_build.py
```

### 方法 2: 完整构建
```bash
python build.py --v2
```

### 方法 3: 先检查环境再构建
```bash
python check_inno_setup.py
python build.py --v2
```

---

## 🔧 可用脚本

### 1. `check_inno_setup.py` - 环境检查
检查构建环境是否就绪：
- Inno Setup 是否已安装
- setup.iss 配置文件是否存在
- 构建输出目录是否完整
- 资源文件是否齐全

```bash
python check_inno_setup.py
```

### 2. `quick_build.py` - 快速构建
简化版构建脚本，自动执行 `build.py --v2`：
- 检查虚拟环境
- 执行完整构建流程
- 显示构建结果

```bash
python quick_build.py
```

### 3. `build.py` - 主构建脚本
完整的构建脚本，支持多种参数：

```bash
# V2 架构构建（推荐）
python build.py --v2

# 仅编译 Launcher
python build.py --v2 --launcher-only

# 仅编译 Main App
python build.py --v2 --app-only

# 清理构建缓存
python build.py --clean
```

---

## ⚙️ 构建流程

### 完整流程（python build.py --v2）

1. **🏗️ 编译 Launcher** (~2-3分钟)
   - 源码: `src_launcher/`
   - 输出: `build/temp_launcher/launcher.exe`
   - 模式: Nuitka onefile

2. **🏗️ 编译 Main App** (~3-5分钟)
   - 源码: `src/`
   - 输出: `build/temp_main_app/app.dist/`
   - 模式: Nuitka standalone

3. **📦 组织文件**
   - 复制 `launcher.exe`
   - 复制 `app.dist/`
   - 输出: `dist/MinecraftFRP_build/`

4. **🔧 Inno Setup 打包** (~1-2分钟)
   - 配置: `setup.iss`
   - 输出: `dist/MinecraftFRP_Setup_0.5.32.exe`

**总耗时**: 首次 6-10 分钟，后续有缓存更快

---

## 📂 输出结构

```
dist/
├── MinecraftFRP_Setup_0.5.32.exe    # 最终安装包 (~200 MB)
└── MinecraftFRP_build/               # 中间产物（可删除）
    ├── launcher.exe
    └── app.dist/
        └── MinecraftFRP.exe
```

---

## 🐛 常见问题

### 问题 1: 找不到 Inno Setup

```
❌ 未找到 Inno Setup 编译器
```

**解决方案**：
1. 下载 Inno Setup 6: https://jrsoftware.org/isdl.php
2. 安装到默认路径: `C:\Program Files (x86)\Inno Setup 6\`

### 问题 2: 虚拟环境未激活

```
⚠️ 虚拟环境未激活
```

**解决方案**：
```bash
# 激活虚拟环境
.venv\Scripts\activate

# 或使用完整路径
.venv\Scripts\python.exe quick_build.py
```

### 问题 3: 构建目录不存在

```
⚠️ 构建目录不存在: dist/MinecraftFRP_build
```

**解决方案**：
确保 Launcher 和 Main App 都已成功编译。检查 `build/` 目录。

### 问题 4: Nuitka 编译失败

**解决方案**：
1. 清理缓存: `python build.py --clean`
2. 检查依赖: `pip install -r requirements.txt`
3. 重新编译: `python build.py --v2`

### 问题 5: 防病毒软件干扰 Inno Setup

```
Error: Resource update error: EndUpdateResource failed, 
try excluding the Output folder from your antivirus software (32)
```

**原因**: 防病毒软件（如火绒、360）阻止 Inno Setup 写入输出文件。

**解决方案**：

**临时方案** - 清理后重试：
```bash
python build.py --clean
python build.py --v2
```

**永久方案** - 添加到白名单（推荐）：

如果使用**火绒安全**：
1. 打开火绒安全软件
2. 设置 → 信任区 → 添加信任目录
3. 添加项目目录: `D:\PycharmProjects\MinecraftFRP`

如果使用 **Windows Defender**：
1. 打开 Windows 安全中心
2. 病毒和威胁防护 → 管理设置
3. 排除项 → 添加或删除排除项
4. 添加文件夹: `D:\PycharmProjects\MinecraftFRP`

### 问题 6: 缺少 BMP 图片文件

```
Error: Could not read "D:\...\base\logo.bmp"
```

**解决方案**: 
已修复。setup.iss 已注释掉可选的图片配置。如果仍有此错误，请检查 setup.iss 中的 `WizardImageFile` 和 `WizardSmallImageFile` 是否已注释。

---

## 🔧 高级配置

### 修改版本号

编辑 `setup.iss`:
```ini
#define MyAppVersion "0.5.32"  ; 修改这里
```

### 修改压缩级别

编辑 `setup.iss`:
```ini
Compression=lzma2/ultra64  ; 最高压缩（慢）
; 或
Compression=lzma2/fast     ; 快速压缩
```

### 禁用 Inno Setup（仅生成便携版）

编辑 `build.py`，注释 Inno Setup 部分：
```python
# if not build_installer_with_inno(build_output_dir, version):
#     raise BuildError("Inno Setup compilation failed")
```

---

## 📝 重要说明

### ⚠️ 永远不要修改 AppId

在 `setup.iss` 中：
```ini
#define MyAppId "{{8B5F6C3D-9E4A-4F2B-A1D3-7C8E9F0B1A2C}}"
```

这个 GUID 用于识别同一个应用，修改后将无法覆盖安装！

### 🚫 禁止使用 BAT/PS1 脚本

根据项目规范（见 PROJECT.MD），所有自动化脚本必须使用 Python 编写。

---

## 🆘 需要帮助？

1. 运行环境检查: `python check_inno_setup.py`
2. 查看构建日志: `build_final.log`
3. 阅读完整文档: `PROJECT.MD`

---

## 📌 项目状态

- ✅ V2 架构迁移完成
- ✅ Inno Setup 集成完成
- ✅ 覆盖更新支持
- ✅ Python 脚本标准化
- ⏳ 自动在线更新（待实现）
- ⏳ 远程构建优化（待完善）
