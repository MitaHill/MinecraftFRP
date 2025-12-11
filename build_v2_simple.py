#!/usr/bin/env python3
"""
V2 架构构建脚本 - 使用 Inno Setup
简化版，专注于编译和打包
"""
import sys
import time
import subprocess
from pathlib import Path

# 添加 src_builder 到路径
sys.path.insert(0, str(Path(__file__).parent))

from src_builder.inno_setup_builder import InnoSetupBuilder
from src_builder.config import BuildConfig


def print_banner():
    """打印横幅"""
    print()
    print("=" * 80)
    print("  🚀 MinecraftFRP V2 Build Script")
    print("  Using Inno Setup Professional Installer")
    print("=" * 80)
    print()


def build_launcher() -> Path:
    """
    构建 Launcher
    
    Returns:
        Path: launcher.exe 路径
    """
    print()
    print("=" * 80)
    print("🔨 Building Launcher")
    print("=" * 80)
    print()
    
    start_time = time.time()
    
    cmd = [
        sys.executable, "-m", "nuitka",
        "--standalone",
        "--onefile",
        "--enable-plugin=pyside6",
        "--disable-console",
        f"--output-dir=build/temp_launcher",
        "--output-filename=launcher.exe",
        "src_launcher/launcher.py"
    ]
    
    print(f"⏳ Compiling launcher...")
    result = subprocess.run(cmd, capture_output=False, text=True)
    
    if result.returncode != 0:
        print(f"❌ ERROR: Launcher build failed!")
        sys.exit(1)
    
    launcher_path = Path("build/temp_launcher/launcher.exe")
    if not launcher_path.exists():
        print(f"❌ ERROR: launcher.exe not found at {launcher_path}")
        sys.exit(1)
    
    size_mb = launcher_path.stat().st_size / (1024 * 1024)
    elapsed = time.time() - start_time
    
    print(f"✅ Launcher built successfully in {elapsed:.2f}s")
    print(f"   Location: {launcher_path}")
    print(f"   Size: {size_mb:.2f} MB")
    
    return launcher_path


def build_main_app() -> Path:
    """
    构建主程序
    
    Returns:
        Path: app.dist 目录路径
    """
    print()
    print("=" * 80)
    print("🔨 Building Main Application")
    print("=" * 80)
    print()
    
    start_time = time.time()
    
    cmd = [
        sys.executable, "-m", "nuitka",
        "--standalone",
        "--enable-plugin=pyside6",
        "--disable-console",
        f"--output-dir=build/temp_main_app",
        "--output-filename=MinecraftFRP.exe",
        "app.py"
    ]
    
    print(f"⏳ Compiling main application...")
    print("   This may take 5-10 minutes...")
    print()
    
    result = subprocess.run(cmd, capture_output=False, text=True)
    
    if result.returncode != 0:
        print(f"❌ ERROR: Main app build failed!")
        sys.exit(1)
    
    app_dist_path = Path("build/temp_main_app/app.dist")
    if not app_dist_path.exists():
        print(f"❌ ERROR: app.dist not found at {app_dist_path}")
        sys.exit(1)
    
    main_exe = app_dist_path / "MinecraftFRP.exe"
    if not main_exe.exists():
        print(f"❌ ERROR: MinecraftFRP.exe not found in app.dist")
        sys.exit(1)
    
    size_mb = main_exe.stat().st_size / (1024 * 1024)
    file_count = sum(1 for _ in app_dist_path.rglob("*") if _.is_file())
    elapsed = time.time() - start_time
    
    print()
    print(f"✅ Found MinecraftFRP.exe ({size_mb:.2f} MB)")
    print(f"✅ app.dist contains {file_count} files")
    print(f"✅ Main app built successfully in {elapsed:.2f}s")
    print(f"   Location: {app_dist_path}")
    
    return app_dist_path


def main():
    """主函数"""
    total_start_time = time.time()
    
    print_banner()
    
    # 读取版本号
    config = BuildConfig()
    version = config.version
    print(f"📌 Version: {version}")
    
    # 1. 构建 Launcher
    launcher_build_start = time.time()
    launcher_path = build_launcher()
    launcher_build_time = time.time() - launcher_build_start
    
    # 2. 构建主程序
    main_app_build_start = time.time()
    app_dist_path = build_main_app()
    main_app_build_time = time.time() - main_app_build_start
    
    # 3. 使用 Inno Setup 打包
    inno_build_start = time.time()
    inno_builder = InnoSetupBuilder(version)
    success, final_installer_path = inno_builder.build_and_release(launcher_path, app_dist_path)
    inno_build_time = time.time() - inno_build_start
    
    if not success:
        print()
        print("❌ Build failed!")
        sys.exit(1)
    
    # 打印总结
    total_time = time.time() - total_start_time
    
    print()
    print("=" * 80)
    print("  ✅ V2 BUILD COMPLETED SUCCESSFULLY!")
    print("=" * 80)
    print()
    print(f"📊 Build Summary:")
    print(f"   Launcher: {launcher_build_time:.2f}s")
    print(f"   Main App: {main_app_build_time:.2f}s")
    print(f"   Installer: {inno_build_time:.2f}s")
    print(f"   Total: {total_time:.2f}s ({total_time/60:.1f} minutes)")
    print()
    print(f"   📦 Installer: {final_installer_path}")
    print()
    print("=" * 80)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        print("❌ Build cancelled by user")
        sys.exit(1)
    except Exception as e:
        print()
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
