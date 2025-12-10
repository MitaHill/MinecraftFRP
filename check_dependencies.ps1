# 快速验证脚本 - 运行此脚本检查依赖

Write-Host "====================================" -ForegroundColor Cyan
Write-Host "   Inno Setup 迁移依赖检查" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

$results = @()

# 1. Inno Setup
$innoPath = "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if (Test-Path $innoPath) {
    Write-Host "✅ Inno Setup 6 已安装" -ForegroundColor Green
    try {
        $version = & $innoPath /? 2>&1 | Select-String "Inno Setup" | Select-Object -First 1
        Write-Host "   版本: $version" -ForegroundColor Gray
    } catch {}
    $results += @{Name="Inno Setup"; Status="OK"}
} else {
    Write-Host "❌ Inno Setup 6 未安装" -ForegroundColor Red
    Write-Host "   请安装: https://jrsoftware.org/isdl.php" -ForegroundColor Yellow
    Write-Host "   或使用命令: winget install --id=JRSoftware.InnoSetup -e" -ForegroundColor Yellow
    $results += @{Name="Inno Setup"; Status="MISSING"}
}

Write-Host ""

# 2. 中文语言包
$langFile = "C:\Program Files (x86)\Inno Setup 6\Languages\ChineseSimplified.isl"
if (Test-Path $langFile) {
    Write-Host "✅ 中文语言包存在" -ForegroundColor Green
    $results += @{Name="Chinese Language"; Status="OK"}
} else {
    Write-Host "⚠️  中文语言包不存在（不影响功能）" -ForegroundColor Yellow
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
    $nuitkaCheck = python -c "import nuitka; print(f'Nuitka {nuitka.__version__}')" 2>&1
    Write-Host "✅ $nuitkaCheck" -ForegroundColor Green
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

# 7. 检查项目必需文件
Write-Host "检查项目文件..." -ForegroundColor Cyan
$projectFiles = @(
    "base\frpc.exe",
    "base\logo.ico",
    "config\app_config.yaml",
    "src_launcher\launcher.py",
    "app.py"
)

$allFilesExist = $true
foreach ($file in $projectFiles) {
    if (Test-Path $file) {
        Write-Host "  ✅ $file" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $file 不存在" -ForegroundColor Red
        $allFilesExist = $false
    }
}

if ($allFilesExist) {
    $results += @{Name="Project Files"; Status="OK"}
} else {
    $results += @{Name="Project Files"; Status="MISSING"}
}

Write-Host ""
Write-Host "====================================" -ForegroundColor Cyan
Write-Host "   检查结果汇总" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan

$missing = $results | Where-Object { $_.Status -eq "MISSING" }
$warnings = $results | Where-Object { $_.Status -eq "WARNING" }

if ($missing.Count -eq 0) {
    Write-Host ""
    Write-Host "🎉 所有必需依赖已安装，可以开始迁移！" -ForegroundColor Green
    Write-Host ""
    Write-Host "下一步: 回复 '准备完成' 开始Inno Setup迁移" -ForegroundColor Cyan
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "❌ 缺少以下必需依赖:" -ForegroundColor Red
    $missing | ForEach-Object { 
        Write-Host "   - $($_.Name)" -ForegroundColor Red 
    }
    Write-Host ""
    Write-Host "请先安装缺少的依赖:" -ForegroundColor Yellow
    Write-Host "  Inno Setup: winget install --id=JRSoftware.InnoSetup -e" -ForegroundColor Yellow
    Write-Host ""
}

if ($warnings.Count -gt 0) {
    Write-Host "⚠️  警告项 (不影响功能):" -ForegroundColor Yellow
    $warnings | ForEach-Object { 
        Write-Host "   - $($_.Name)" -ForegroundColor Yellow 
    }
    Write-Host ""
}
