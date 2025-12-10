# MinecraftFRP v2 Inno Setup 构建指南

## 🎯 快速开始

### 本地构建

```powershell
python build.py --v2
```

就这么简单！`--v2` 会自动启用 `--fast` 模式。

### 本地构建并上传

```powershell
python build.py --v2 --upload
```

### 远程构建

```powershell
.\build_remote.ps1 -Remote -Fast
```

---

## 📊 构建流程

### 阶段说明

1. **Launcher编译** (4-5分钟)
   - 编译 `src_launcher/launcher.exe`
   - Nuitka onefile模式

2. **主应用编译** (4-5分钟)
   - 编译 `app.py` → `app.dist/`
   - Nuitka standalone模式

3. **文件组织** (几秒)
   - 组织到 `dist/MinecraftFRP_build/`
   - launcher.exe
   - app.dist/ (所有应用文件)

4. **Inno Setup打包** (30秒)
   - 使用 `setup.iss` 脚本
   - 生成最终安装器

**总耗时**: 约10-12分钟

---

## 📦 构建产物

### 位置
```
dist/MinecraftFRP_0.5.32_installer/MinecraftFRP_Setup_0.5.32.exe
```

### 大小
约 180-200 MB (LZMA2 高压缩)

### 特性
- ✅ 标准Windows安装程序
- ✅ 中文界面
- ✅ 自定义安装路径
- ✅ 桌面/开始菜单快捷方式
- ✅ 完整的卸载程序
- ✅ 自动注册到控制面板
- ✅ 保留配置文件

---

## 🧪 测试安装器

```powershell
# 启动安装程序
Start-Process "dist\MinecraftFRP_0.5.32_installer\MinecraftFRP_Setup_0.5.32.exe"
```

### 安装流程
1. 欢迎页面
2. 选择安装位置 (默认: `C:\Program Files\MinecraftFRP`)
3. 选择快捷方式
4. 安装进度
5. 完成页面 (可选立即启动)

### 安装后
- 程序安装到: `C:\Program Files\MinecraftFRP\`
- 配置保存到: `文档\MitaHillFRP\`
- 注册表: `HKCU\Software\MitaHill\MinecraftFRP`

---

## 🗑️ 卸载

### 方法1: 控制面板
设置 → 应用 → MinecraftFRP → 卸载

### 方法2: 开始菜单
开始菜单 → MinecraftFRP → 卸载 MinecraftFRP

### 卸载选项
- 程序文件会被删除
- 提示是否删除配置文件
- 配置文件位于: `文档\MitaHillFRP\`

---

## 🔧 高级选项

### 自定义版本号

编辑 `setup.iss`:
```iss
#define MyAppVersion "0.5.32"
```

### 修改安装选项

编辑 `setup.iss` 的 `[Setup]` 部分:
```iss
DefaultDirName={autopf}\{#MyAppName}     ; 默认安装路径
PrivilegesRequired=lowest                 ; 需要的权限
```

### 修改快捷方式

编辑 `setup.iss` 的 `[Tasks]` 部分:
```iss
Name: "desktopicon"; Description: "创建桌面快捷方式"; Flags: unchecked
```

---

## 📝 与旧版本对比

| 特性 | V1 (Python Installer) | V2 (Inno Setup) |
|------|----------------------|-----------------|
| 构建命令 | `python build.py --fast` | `python build.py --v2` |
| Installer构建 | Nuitka (3分钟) | Inno Setup (30秒) |
| 安装体验 | 自定义界面 | 标准Windows界面 |
| 卸载程序 | 手动实现 | 自动提供 |
| 控制面板集成 | ❌ | ✅ |
| 配置保护 | 手动 | 自动 (onlyifdoesntexist) |
| 代码维护 | src_installer/ 目录 | setup.iss 脚本 |
| 资源路径问题 | ⚠️ 需要处理 | ✅ 无问题 |

---

## 🐛 故障排查

### 构建失败

**检查Inno Setup**:
```powershell
Test-Path "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
```

**查看构建日志**:
```powershell
python build.py --v2 2>&1 | Tee-Object -FilePath build.log
```

### 安装器无法运行

**检查文件完整性**:
```powershell
$installer = "dist\MinecraftFRP_0.5.32_installer\MinecraftFRP_Setup_0.5.32.exe"
Get-FileHash $installer -Algorithm SHA256
```

**重新构建**:
```powershell
Remove-Item build -Recurse -Force
Remove-Item "dist\MinecraftFRP_build" -Recurse -Force
python build.py --v2
```

### 安装失败

- 检查是否有足够的磁盘空间 (需要约500MB)
- 检查是否有防病毒软件拦截
- 尝试以管理员身份运行安装器

---

## 📚 相关文件

- `setup.iss` - Inno Setup 安装脚本
- `src_builder/inno_builder.py` - Inno Setup 构建器
- `src_builder/v2_builder.py` - V2 构建主逻辑
- `build.py` - 构建入口
- `build_remote.ps1` - 远程/本地构建脚本

---

## 🚀 持续集成

### 自动构建

```yaml
# cicd.yaml 示例
build:
  commands:
    - python build.py --v2 --upload
```

### 远程构建服务器

1. 确保安装了 Inno Setup
2. 同步 .venv 虚拟环境
3. 运行远程构建:
```powershell
.\build_remote.ps1 -Remote -Fast
```

---

## ✅ 最佳实践

1. **本地开发**: 使用 `python build.py --v2`
2. **测试安装**: 每次修改后测试完整安装流程
3. **版本管理**: 更新 `setup.iss` 中的版本号
4. **配置保护**: 重要配置放到 `文档\MitaHillFRP\`
5. **清理构建**: 定期清理 `build/` 目录

---

## 📞 获取帮助

```powershell
python build.py --help
```

构建有问题？检查:
- Inno Setup 是否正确安装
- Python 依赖是否完整
- 构建日志中的错误信息
