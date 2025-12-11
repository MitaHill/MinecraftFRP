# 远程构建服务器配置指南

## 📋 服务器信息
- **主机**: 192.168.9.158
- **用户**: vgpu-server-user
- **工作目录**: D:\MinecraftFRP
- **系统**: Windows 11

---

## ✅ 已安装的依赖
- ✅ Python 3.9.13
- ✅ Git 2.52.0
- ✅ Nuitka
- ✅ requests, pyyaml, paramiko

---

## ❌ 需要手动安装的依赖

### 1. Inno Setup 6

**通过SSH安装**:
```powershell
# 本地执行：
ssh vgpu-server-user@192.168.9.158

# 远程服务器执行：
# 下载Inno Setup
Invoke-WebRequest -Uri "https://jrsoftware.org/download.php/is.exe" -OutFile "$env:TEMP\innosetup.exe"

# 静默安装（使用默认路径）
Start-Process -FilePath "$env:TEMP\innosetup.exe" -ArgumentList "/VERYSILENT /NORESTART" -Wait

# 验证安装
Test-Path "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
```

**或手动安装**:
1. 访问 https://jrsoftware.org/isdl.php
2. 下载并安装 Inno Setup 6
3. 使用默认安装路径

---

### 2. PySide6

```powershell
# 通过SSH安装
ssh vgpu-server-user@192.168.9.158 "python -m pip install PySide6"

# 或登录后安装
ssh vgpu-server-user@192.168.9.158
python -m pip install PySide6
```

---

## 🔍 验证安装

**在远程服务器执行**:
```powershell
# 检查Inno Setup
Test-Path "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"

# 检查PySide6
python -c "import PySide6; print(f'PySide6 {PySide6.__version__}')"
```

**从本地验证**:
```powershell
# 运行远程依赖检查
.\build_remote.ps1 -Remote -Fast
```

---

## 📝 快速安装命令（一键执行）

```powershell
# 在本地PowerShell执行：
ssh vgpu-server-user@192.168.9.158 @"
# 安装PySide6
python -m pip install PySide6

# 下载Inno Setup
`$innoUrl = 'https://jrsoftware.org/download.php/is.exe'
`$innoPath = '`$env:TEMP\innosetup.exe'
Invoke-WebRequest -Uri `$innoUrl -OutFile `$innoPath

# 静默安装Inno Setup  
Start-Process -FilePath `$innoPath -ArgumentList '/VERYSILENT /NORESTART' -Wait

Write-Host '✅ 安装完成'
"@
```

---

## 🚀 使用远程构建

**安装完依赖后**:

```powershell
# 远程快速构建
.\build_remote.ps1 -Remote -Fast

# 远程构建并上传
.\build_remote.ps1 -Remote -Fast -Upload
```

---

## 🔧 故障排查

### 问题1: SSH连接失败
```powershell
# 测试连接
ssh -v vgpu-server-user@192.168.9.158

# 检查SSH服务
ssh vgpu-server-user@192.168.9.158 "Get-Service sshd"
```

### 问题2: 权限不足
```powershell
# 以管理员身份运行PowerShell
ssh vgpu-server-user@192.168.9.158 "Start-Process powershell -Verb RunAs"
```

### 问题3: 文件同步问题
- 确保本地代码已推送到Git
- 确保远程服务器已拉取最新代码
- 或手动使用rsync/robocopy同步

---

## 📂 目录结构

```
远程服务器:
D:\MinecraftFRP\          # 工作目录（同步自开发机）
├── src_launcher\
├── src_installer\
├── base\
├── config\
├── build.py
└── setup.iss             # Inno Setup脚本（待创建）

本地开发机:
D:\PycharmProjects\MinecraftFRP\
├── build_remote.ps1      # 远程/本地构建脚本
├── check_dependencies.ps1
└── setup_remote_server.ps1
```

---

## ⏱️ 预估时间

- **PySide6安装**: 5-10分钟
- **Inno Setup安装**: 2分钟
- **首次远程构建**: 15分钟（含缓存生成）
- **后续构建**: 10分钟

---

## 📞 需要帮助？

如果遇到问题，请提供：
1. 错误信息截图
2. `.\build_remote.ps1 -Remote -Fast` 的完整输出
3. 远程服务器系统信息: `ssh vgpu-server-user@192.168.9.158 "systeminfo"`
