# Inno Setup 迁移依赖清单

## 📋 总览

迁移到Inno Setup架构需要在本地开发机安装新工具，远程服务器无需额外依赖。

---

## 💻 本地开发电脑依赖

### 1. **Inno Setup 6** (必需)

**用途**: 编译安装脚本生成Windows安装器

**下载链接**: https://jrsoftware.org/isdl.php

**安装步骤**:
```powershell
# 方法1: 手动下载安装
# 1. 访问 https://jrsoftware.org/isdl.php
# 2. 下载 "Inno Setup 6.x.x" (约2MB)
# 3. 运行安装程序，使用默认路径

# 方法2: 使用 Chocolatey (如果已安装)
choco install innosetup -y

# 方法3: 使用 Winget
winget install --id=JRSoftware.InnoSetup -e
```

**默认安装路径**: 
- `C:\Program Files (x86)\Inno Setup 6\`
- 编译器: `C:\Program Files (x86)\Inno Setup 6\ISCC.exe`

**验证安装**:
```powershell
# 检查Inno Setup是否安装成功
$innoPath = "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if (Test-Path $innoPath) {
    Write-Host "✅ Inno Setup 已安装" -ForegroundColor Green
    & $innoPath /?  # 显示版本信息
} else {
    Write-Host "❌ Inno Setup 未找到" -ForegroundColor Red
}
```

**预期输出**:
```
Inno Setup 6.x.x Command-Line Compiler
Copyright (C) 1997-2024 Jordan Russell
```

---

### 2. **Inno Setup 中文语言包** (可选，推荐)

**用途**: 安装向导显示中文界面

**说明**: Inno Setup自带中文语言文件，无需额外安装

**位置**: `C:\Program Files (x86)\Inno Setup 6\Languages\ChineseSimplified.isl`

**验证**:
```powershell
$langFile = "C:\Program Files (x86)\Inno Setup 6\Languages\ChineseSimplified.isl"
if (Test-Path $langFile) {
    Write-Host "✅ 中文语言包存在" -ForegroundColor Green
} else {
    Write-Host "⚠️ 中文语言包不存在" -ForegroundColor Yellow
}
```

---

### 3. **现有依赖确认** (已安装)

这些是你已经安装的，确认即可：

```powershell
# Python 3.9+
python --version

# Nuitka
python -m nuitka --version

# PySide6
python -c "import PySide6; print(f'PySide6 {PySide6.__version__}')"

# Git
git --version
```

**预期输出**:
```
Python 3.9.x
Nuitka 2.8.9
PySide6 6.x.x
git version 2.x.x
```

---

## 🖥️ 远程服务器依赖

### **无需额外安装**

远程服务器只需要：
- ✅ SSH/SFTP访问 (已有)
- ✅ 存储空间 (约200MB+)
- ✅ Web服务器 (chfs，已有)

**原因**: 
- 安装器在本地构建完成后，直接上传.exe文件
- 服务器只负责托管下载链接，不参与构建

---

## 🔧 完整验证脚本

**在本地PowerShell运行**:

```powershell
Write-Host "====================================" -ForegroundColor Cyan
Write-Host "   Inno Setup 迁移依赖检查" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

$results = @()

# 1. Inno Setup
$innoPath = "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if (Test-Path $innoPath) {
    Write-Host "✅ Inno Setup 6 已安装" -ForegroundColor Green
    $version = (& $innoPath /? 2>&1 | Select-String "Inno Setup" | Out-String).Trim()
    Write-Host "   版本: $version" -ForegroundColor Gray
    $results += @{Name="Inno Setup"; Status="OK"}
} else {
    Write-Host "❌ Inno Setup 6 未安装" -ForegroundColor Red
    Write-Host "   请安装: https://jrsoftware.org/isdl.php" -ForegroundColor Yellow
    $results += @{Name="Inno Setup"; Status="MISSING"}
}

Write-Host ""

# 2. 中文语言包
$langFile = "C:\Program Files (x86)\Inno Setup 6\Languages\ChineseSimplified.isl"
if (Test-Path $langFile) {
    Write-Host "✅ 中文语言包存在" -ForegroundColor Green
    $results += @{Name="Chinese Language"; Status="OK"}
} else {
    Write-Host "⚠️ 中文语言包不存在（不影响功能）" -ForegroundColor Yellow
    $results += @{Name="Chinese Language"; Status="WARNING"}
}

Write-Host ""

# 3. Python
try {
    $pyVersion = python --version 2>&1
    Write-Host "✅ Python: $pyVersion" -ForegroundColor Green
    $results += @{Name="Python"; Status="OK"}
} catch {
    Write-Host "❌ Python 未安装" -ForegroundColor Red
    $results += @{Name="Python"; Status="MISSING"}
}

Write-Host ""

# 4. Nuitka
try {
    $nuitkaVersion = python -m nuitka --version 2>&1 | Select-String "Nuitka" | Out-String
    Write-Host "✅ Nuitka: $($nuitkaVersion.Trim())" -ForegroundColor Green
    $results += @{Name="Nuitka"; Status="OK"}
} catch {
    Write-Host "❌ Nuitka 未安装" -ForegroundColor Red
    $results += @{Name="Nuitka"; Status="MISSING"}
}

Write-Host ""

# 5. PySide6
try {
    $pysideVersion = python -c "import PySide6; print(f'PySide6 {PySide6.__version__}')" 2>&1
    Write-Host "✅ $pysideVersion" -ForegroundColor Green
    $results += @{Name="PySide6"; Status="OK"}
} catch {
    Write-Host "❌ PySide6 未安装" -ForegroundColor Red
    $results += @{Name="PySide6"; Status="MISSING"}
}

Write-Host ""

# 6. Git
try {
    $gitVersion = git --version 2>&1
    Write-Host "✅ Git: $gitVersion" -ForegroundColor Green
    $results += @{Name="Git"; Status="OK"}
} catch {
    Write-Host "❌ Git 未安装" -ForegroundColor Red
    $results += @{Name="Git"; Status="MISSING"}
}

Write-Host ""
Write-Host "====================================" -ForegroundColor Cyan
Write-Host "   检查结果汇总" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan

$missing = $results | Where-Object { $_.Status -eq "MISSING" }
$warnings = $results | Where-Object { $_.Status -eq "WARNING" }

if ($missing.Count -eq 0) {
    Write-Host "✅ 所有必需依赖已安装，可以开始迁移！" -ForegroundColor Green
} else {
    Write-Host "❌ 缺少以下依赖:" -ForegroundColor Red
    $missing | ForEach-Object { Write-Host "   - $($_.Name)" -ForegroundColor Red }
    Write-Host ""
    Write-Host "请先安装缺少的依赖再继续" -ForegroundColor Yellow
}

if ($warnings.Count -gt 0) {
    Write-Host "⚠️ 警告项:" -ForegroundColor Yellow
    $warnings | ForEach-Object { Write-Host "   - $($_.Name)" -ForegroundColor Yellow }
}
```

---

## 📦 安装顺序建议

1. **Inno Setup** (5分钟)
   ```powershell
   # 使用Winget快速安装
   winget install --id=JRSoftware.InnoSetup -e
   ```

2. **验证安装**
   ```powershell
   # 运行上面的完整验证脚本
   ```

3. **准备就绪标志**
   - ✅ Inno Setup 验证通过
   - ✅ 中文语言包存在
   - ✅ 所有Python依赖正常

---

## 🚀 安装完成后的下一步

安装完成后，我将：

1. 创建 `setup.iss` (Inno Setup脚本)
2. 修改 `build.py` (集成Inno Setup)
3. 创建 `src_builder/inno_builder.py` (Inno Setup构建器)
4. 测试完整构建流程
5. 清理 `src_installer/` 目录（不再需要）

---

## ❓ 常见问题

**Q: Inno Setup会增加构建时间吗？**
A: 不会，反而会减少。Inno Setup打包只需30秒，比Nuitka编译installer快5倍。

**Q: Inno Setup是免费的吗？**
A: 是的，完全免费且开源。

**Q: 打包后的installer大小会变化吗？**
A: 会略小，LZMA2压缩率优于Nuitka，预计从211MB降到180MB左右。

**Q: 需要学习Inno Setup脚本语法吗？**
A: 不需要，我会提供完整的配置好的脚本，只需要调整版本号等少量参数。

**Q: 服务器需要安装Inno Setup吗？**
A: 不需要，服务器只接收最终的.exe文件。

---

## ✅ 准备完成确认

请运行验证脚本，确认所有依赖都显示 ✅，然后回复 "准备完成"，我将开始迁移工作。
