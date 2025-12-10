# 远程服务器环境检查脚本
Write-Host "====================================" -ForegroundColor Cyan
Write-Host "   远程服务器环境检查" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

# 1. 检查Inno Setup
Write-Host "1. Inno Setup 检查:" -ForegroundColor Yellow
$innoPath = "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if (Test-Path $innoPath) {
    Write-Host "   ✅ Inno Setup 6 已安装" -ForegroundColor Green
    try {
        $version = & $innoPath /? 2>&1 | Select-String "Inno Setup" | Select-Object -First 1
        Write-Host "   版本: $version" -ForegroundColor Gray
    } catch {}
} else {
    Write-Host "   ❌ Inno Setup 6 未找到" -ForegroundColor Red
}
Write-Host ""

# 2. 检查全局Python环境
Write-Host "2. 全局Python环境:" -ForegroundColor Yellow
try {
    $pyVersion = python --version 2>&1
    Write-Host "   Python: $pyVersion" -ForegroundColor Gray
    
    # 检查全局包
    Write-Host "   检查全局安装的包..." -ForegroundColor Gray
    $hasPySide6 = python -c "import PySide6" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ⚠️  PySide6 仍在全局环境（应该卸载）" -ForegroundColor Yellow
    } else {
        Write-Host "   ✅ PySide6 不在全局环境" -ForegroundColor Green
    }
} catch {
    Write-Host "   Python 未找到" -ForegroundColor Red
}
Write-Host ""

# 3. 检查项目虚拟环境
Write-Host "3. 项目虚拟环境:" -ForegroundColor Yellow
$projectPath = "D:\MinecraftFRP"
$venvPath = Join-Path $projectPath ".venv"

if (Test-Path $venvPath) {
    Write-Host "   ✅ 虚拟环境存在: $venvPath" -ForegroundColor Green
    
    $venvPython = Join-Path $venvPath "Scripts\python.exe"
    if (Test-Path $venvPython) {
        Write-Host "   Python路径: $venvPython" -ForegroundColor Gray
        
        # 检查虚拟环境的包
        Write-Host "   检查虚拟环境依赖..." -ForegroundColor Gray
        
        $pyVer = & $venvPython --version 2>&1
        Write-Host "     Python: $pyVer" -ForegroundColor Gray
        
        $packages = @("nuitka", "PySide6", "requests", "pyyaml")
        foreach ($pkg in $packages) {
            $check = & $venvPython -c "import $pkg; print('OK')" 2>&1
            if ($check -like "*OK*") {
                Write-Host "     ✅ $pkg" -ForegroundColor Green
            } else {
                Write-Host "     ❌ $pkg 未安装" -ForegroundColor Red
            }
        }
    }
} else {
    Write-Host "   ❌ 虚拟环境不存在: $venvPath" -ForegroundColor Red
    Write-Host "   需要创建虚拟环境并安装依赖" -ForegroundColor Yellow
}
Write-Host ""

# 4. 检查项目文件
Write-Host "4. 项目文件:" -ForegroundColor Yellow
if (Test-Path $projectPath) {
    Write-Host "   ✅ 项目目录存在: $projectPath" -ForegroundColor Green
    
    $requiredFiles = @(
        "build.py",
        "app.py",
        "base\frpc.exe",
        "config\app_config.yaml"
    )
    
    foreach ($file in $requiredFiles) {
        $fullPath = Join-Path $projectPath $file
        if (Test-Path $fullPath) {
            Write-Host "     ✅ $file" -ForegroundColor Green
        } else {
            Write-Host "     ❌ $file 缺失" -ForegroundColor Red
        }
    }
} else {
    Write-Host "   ❌ 项目目录不存在: $projectPath" -ForegroundColor Red
}
Write-Host ""

Write-Host "====================================" -ForegroundColor Cyan
Write-Host "   检查完成" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
