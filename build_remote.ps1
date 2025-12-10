# MinecraftFRP 远程/本地构建脚本
# 支持在本地构建或通过SSH触发远程服务器构建

param(
    [switch]$Remote,           # 是否使用远程服务器构建
    [switch]$Fast,             # 快速构建（无LTO）
    [switch]$Upload,           # 构建后上传到文件服务器
    [string]$RemoteHost = "192.168.9.158",
    [string]$RemoteUser = "vgpu-server-user",
    [string]$RemoteWorkDir = "D:\MinecraftFRP"
)

$ErrorActionPreference = "Stop"

Write-Host "====================================" -ForegroundColor Cyan
Write-Host "   MinecraftFRP 构建脚本" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

# 构建参数
$buildArgs = "--v2"
if ($Fast) { $buildArgs += " --fast" }
if ($Upload) { $buildArgs += " --upload" }

if ($Remote) {
    Write-Host "🌐 远程构建模式" -ForegroundColor Yellow
    Write-Host "   服务器: $RemoteUser@$RemoteHost" -ForegroundColor Gray
    Write-Host "   工作目录: $RemoteWorkDir" -ForegroundColor Gray
    Write-Host ""
    
    # 1. 测试连接
    Write-Host "1️⃣ 测试SSH连接..." -ForegroundColor Cyan
    $testResult = ssh -o ConnectTimeout=5 "$RemoteUser@$RemoteHost" "echo OK" 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ SSH连接失败！" -ForegroundColor Red
        Write-Host "   请检查: " -ForegroundColor Yellow
        Write-Host "   - SSH服务是否运行" -ForegroundColor Yellow
        Write-Host "   - 防火墙是否允许连接" -ForegroundColor Yellow
        Write-Host "   - 用户名密码是否正确" -ForegroundColor Yellow
        exit 1
    }
    Write-Host "   ✅ SSH连接正常" -ForegroundColor Green
    Write-Host ""
    
    # 2. 检查远程依赖
    Write-Host "2️⃣ 检查远程依赖..." -ForegroundColor Cyan
    $checkCmd = @"
cd $RemoteWorkDir
if (Test-Path '.venv\Scripts\python.exe') {
    Write-Host 'Python (venv): OK'
    & .\.venv\Scripts\python.exe --version
    & .\.venv\Scripts\python.exe -c 'import nuitka; print(\"Nuitka: OK\")'
    & .\.venv\Scripts\python.exe -c 'import PySide6; print(\"PySide6: OK\")'
} else {
    Write-Host 'ERROR: Virtual environment not found'
    exit 1
}
if (Test-Path 'C:\Program Files (x86)\Inno Setup 6\ISCC.exe') { 
    Write-Host 'Inno Setup: OK' 
} else { 
    Write-Host 'ERROR: Inno Setup not installed' 
    exit 1
}
"@
    
    $depCheck = ssh "$RemoteUser@$RemoteHost" "powershell -Command `"$checkCmd`"" 2>&1
    Write-Host $depCheck
    
    if ($depCheck -match "ERROR") {
        Write-Host ""
        Write-Host "❌ 远程服务器依赖不完整！" -ForegroundColor Red
        Write-Host "   问题可能是:" -ForegroundColor Yellow
        Write-Host "   - 虚拟环境(.venv)未同步到远程" -ForegroundColor Yellow
        Write-Host "   - Inno Setup未安装" -ForegroundColor Yellow
        exit 1
    }
    Write-Host "   ✅ 远程依赖完整" -ForegroundColor Green
    Write-Host ""
    
    # 3. 同步代码（如果需要）
    Write-Host "3️⃣ 同步代码到远程..." -ForegroundColor Cyan
    Write-Host "   ⏭️ 跳过（假设有自动同步机制）" -ForegroundColor Gray
    Write-Host ""
    
    # 4. 触发远程构建
    Write-Host "4️⃣ 触发远程构建..." -ForegroundColor Cyan
    Write-Host "   命令: .\.venv\Scripts\python.exe build.py $buildArgs" -ForegroundColor Gray
    Write-Host ""
    
    $buildCmd = @"
cd $RemoteWorkDir
.\.venv\Scripts\python.exe build.py $buildArgs 2>&1
"@
    
    ssh "$RemoteUser@$RemoteHost" "powershell -Command `"$buildCmd`""
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "❌ 远程构建失败！" -ForegroundColor Red
        exit 1
    }
    
    Write-Host ""
    Write-Host "✅ 远程构建完成" -ForegroundColor Green
    Write-Host ""
    
    # 5. 下载构建产物
    Write-Host "5️⃣ 下载构建产物..." -ForegroundColor Cyan
    
    # 创建本地dist目录
    if (-not (Test-Path "dist")) {
        New-Item -Path "dist" -ItemType Directory | Out-Null
    }
    
    # 下载installer
    Write-Host "   下载installer..." -ForegroundColor Gray
    scp -r "$RemoteUser@${RemoteHost}:$RemoteWorkDir/dist/MinecraftFRP_*_installer" dist/
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ 构建产物已下载到本地 dist/" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️ 下载失败，请手动从远程服务器获取" -ForegroundColor Yellow
    }
    
} else {
    Write-Host "💻 本地构建模式" -ForegroundColor Yellow
    Write-Host ""
    
    # 1. 检查本地依赖
    Write-Host "1️⃣ 检查本地依赖..." -ForegroundColor Cyan
    
    $missingDeps = @()
    
    # Python
    try {
        $pyVersion = python --version 2>&1
        Write-Host "   ✅ Python: $pyVersion" -ForegroundColor Green
    } catch {
        Write-Host "   ❌ Python 未安装" -ForegroundColor Red
        $missingDeps += "Python"
    }
    
    # Inno Setup
    $innoPath = "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
    if (Test-Path $innoPath) {
        Write-Host "   ✅ Inno Setup 已安装" -ForegroundColor Green
    } else {
        Write-Host "   ❌ Inno Setup 未安装" -ForegroundColor Red
        $missingDeps += "Inno Setup"
    }
    
    # Nuitka
    try {
        python -c "import nuitka" 2>&1 | Out-Null
        Write-Host "   ✅ Nuitka 已安装" -ForegroundColor Green
    } catch {
        Write-Host "   ❌ Nuitka 未安装" -ForegroundColor Red
        $missingDeps += "Nuitka"
    }
    
    # PySide6
    try {
        python -c "import PySide6" 2>&1 | Out-Null
        Write-Host "   ✅ PySide6 已安装" -ForegroundColor Green
    } catch {
        Write-Host "   ❌ PySide6 未安装" -ForegroundColor Red
        $missingDeps += "PySide6"
    }
    
    if ($missingDeps.Count -gt 0) {
        Write-Host ""
        Write-Host "❌ 缺少依赖: $($missingDeps -join ', ')" -ForegroundColor Red
        Write-Host "   请先运行: .\check_dependencies.ps1" -ForegroundColor Yellow
        exit 1
    }
    
    Write-Host ""
    
    # 2. 执行本地构建
    Write-Host "2️⃣ 执行本地构建..." -ForegroundColor Cyan
    Write-Host "   命令: python build.py $buildArgs" -ForegroundColor Gray
    Write-Host ""
    
    python build.py $buildArgs
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "❌ 构建失败！" -ForegroundColor Red
        exit 1
    }
    
    Write-Host ""
    Write-Host "✅ 本地构建完成" -ForegroundColor Green
}

Write-Host ""
Write-Host "====================================" -ForegroundColor Cyan
Write-Host "   ✅ 构建任务完成" -ForegroundColor Green
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

# 显示构建产物
if (Test-Path "dist") {
    Write-Host "📦 构建产物:" -ForegroundColor Cyan
    Get-ChildItem "dist\MinecraftFRP_*_installer" -Recurse -File -Filter "*.exe" | 
        ForEach-Object {
            $sizeMB = [math]::Round($_.Length / 1MB, 2)
            Write-Host "   📄 $($_.Name) ($sizeMB MB)" -ForegroundColor White
            Write-Host "      路径: $($_.FullName)" -ForegroundColor Gray
        }
}

Write-Host ""
