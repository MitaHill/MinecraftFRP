# 远程服务器依赖安装脚本
# 在远程Windows服务器上运行

Write-Host "====================================" -ForegroundColor Cyan
Write-Host "   远程服务器依赖安装" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

# 1. 检查Python
Write-Host "1. 检查 Python..." -ForegroundColor Yellow
try {
    $pyVersion = python --version 2>&1
    Write-Host "   ✅ Python: $pyVersion" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Python 未安装" -ForegroundColor Red
    Write-Host "   请安装 Python 3.9+: https://www.python.org/downloads/" -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# 2. 检查Git
Write-Host "2. 检查 Git..." -ForegroundColor Yellow
try {
    $gitVersion = git --version 2>&1
    Write-Host "   ✅ Git: $gitVersion" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Git 未安装" -ForegroundColor Red
    Write-Host "   请安装 Git: https://git-scm.com/download/win" -ForegroundColor Yellow
}

Write-Host ""

# 3. 安装/检查 Inno Setup
Write-Host "3. 检查 Inno Setup..." -ForegroundColor Yellow
$innoPath = "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"

if (Test-Path $innoPath) {
    Write-Host "   ✅ Inno Setup 已安装" -ForegroundColor Green
    $version = & $innoPath /? 2>&1 | Select-String "Inno Setup" | Select-Object -First 1
    Write-Host "   版本: $version" -ForegroundColor Gray
} else {
    Write-Host "   ❌ Inno Setup 未安装" -ForegroundColor Red
    Write-Host "   正在下载安装..." -ForegroundColor Yellow
    
    $downloadUrl = "https://jrsoftware.org/download.php/is.exe"
    $savePath = "$env:TEMP\innosetup-installer.exe"
    
    try {
        Write-Host "   下载中..." -ForegroundColor Cyan
        Invoke-WebRequest -Uri $downloadUrl -OutFile $savePath -UseBasicParsing
        Write-Host "   ✅ 下载完成" -ForegroundColor Green
        
        Write-Host "   安装中（请等待安装向导完成）..." -ForegroundColor Cyan
        Start-Process -FilePath $savePath -Wait
        
        # 验证安装
        if (Test-Path $innoPath) {
            Write-Host "   ✅ Inno Setup 安装成功！" -ForegroundColor Green
        } else {
            Write-Host "   ⚠️  安装可能失败，请手动检查" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "   ❌ 自动安装失败: $_" -ForegroundColor Red
        Write-Host "   请手动下载: https://jrsoftware.org/isdl.php" -ForegroundColor Yellow
    }
}

Write-Host ""

# 4. 检查Nuitka
Write-Host "4. 检查 Nuitka..." -ForegroundColor Yellow
try {
    python -c "import nuitka; print('Nuitka installed')" 2>&1 | Out-Null
    Write-Host "   ✅ Nuitka 已安装" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Nuitka 未安装" -ForegroundColor Red
    Write-Host "   安装中..." -ForegroundColor Yellow
    python -m pip install nuitka
    Write-Host "   ✅ Nuitka 安装完成" -ForegroundColor Green
}

Write-Host ""

# 5. 检查PySide6
Write-Host "5. 检查 PySide6..." -ForegroundColor Yellow
try {
    $pysideVersion = python -c "import PySide6; print(f'PySide6 {PySide6.__version__}')" 2>&1
    Write-Host "   ✅ $pysideVersion" -ForegroundColor Green
} catch {
    Write-Host "   ❌ PySide6 未安装" -ForegroundColor Red
    Write-Host "   安装中（需要较长时间）..." -ForegroundColor Yellow
    python -m pip install PySide6
    Write-Host "   ✅ PySide6 安装完成" -ForegroundColor Green
}

Write-Host ""

# 6. 检查其他Python依赖
Write-Host "6. 检查其他Python依赖..." -ForegroundColor Yellow
$packages = @("requests", "pyyaml", "paramiko")

foreach ($pkg in $packages) {
    try {
        python -c "import $pkg" 2>&1 | Out-Null
        Write-Host "   ✅ $pkg 已安装" -ForegroundColor Green
    } catch {
        Write-Host "   ⚠️  $pkg 未安装，安装中..." -ForegroundColor Yellow
        python -m pip install $pkg
        Write-Host "   ✅ $pkg 安装完成" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "====================================" -ForegroundColor Cyan
Write-Host "   ✅ 依赖检查/安装完成！" -ForegroundColor Green
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "远程服务器已准备就绪，可以进行构建" -ForegroundColor Green
