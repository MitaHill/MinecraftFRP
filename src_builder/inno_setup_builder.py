"""
Inno Setup Builder - 负责使用 Inno Setup 打包安装程序
"""
import shutil
import subprocess
from pathlib import Path
from typing import Optional, Tuple


class InnoSetupBuilder:
    """Inno Setup 构建器"""
    
    def __init__(self, version: str):
        """
        初始化 Inno Setup 构建器
        
        Args:
            version: 版本号 (如 "0.5.32")
        """
        self.version = version
        self.root_dir = Path.cwd()
        
        # 路径配置
        self.build_dir = self.root_dir / "build"
        self.dist_dir = self.root_dir / "dist"
        
        # Inno Setup 相关
        self.setup_script = self.root_dir / "setup.iss"
        self.iscc_path = Path(r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe")
        
        # 构建产物路径
        self.build_output_dir = self.build_dir / "MinecraftFRP_build"
        self.installer_output_dir = self.build_dir / "installer_output"
        self.installer_filename = f"MinecraftFRP_Setup_{self.version}.exe"
        self.installer_path = self.installer_output_dir / self.installer_filename
        
        # 最终发布路径
        self.release_dir = self.dist_dir / self.version
        
    def check_inno_setup(self) -> bool:
        """检查 Inno Setup 是否安装"""
        if not self.iscc_path.exists():
            print(f"❌ ERROR: Inno Setup not found at {self.iscc_path}")
            print("   Please install Inno Setup 6 from https://jrsoftware.org/isinfo.php")
            return False
        return True
    
    def organize_build_files(self, launcher_path: Path, app_dist_path: Path) -> bool:
        """
        组织构建文件到 build/MinecraftFRP_build/
        
        Args:
            launcher_path: launcher.exe 路径
            app_dist_path: app.dist 目录路径
            
        Returns:
            bool: 是否成功
        """
        print()
        print("=" * 80)
        print("📦 Organizing Build Output for Inno Setup")
        print("=" * 80)
        
        try:
            # 清理旧的构建目录
            if self.build_output_dir.exists():
                print("🧹 Cleaning old output directory...")
                shutil.rmtree(self.build_output_dir)
            
            # 创建新目录
            self.build_output_dir.mkdir(parents=True, exist_ok=True)
            print(f"⏳ Organizing files to {self.build_output_dir.relative_to(self.root_dir)}...")
            
            # 复制 launcher.exe
            launcher_dest = self.build_output_dir / "launcher.exe"
            shutil.copy2(launcher_path, launcher_dest)
            print("✅ Copied launcher.exe")
            
            # 复制 app.dist 目录
            app_dist_dest = self.build_output_dir / "app.dist"
            shutil.copytree(app_dist_path, app_dist_dest)
            file_count = sum(1 for _ in app_dist_dest.rglob("*") if _.is_file())
            print(f"✅ Copied app.dist ({file_count} files)")
            
            # 验证主程序
            main_exe = app_dist_dest / "MinecraftFRP.exe"
            if not main_exe.exists():
                print(f"❌ ERROR: MinecraftFRP.exe not found in app.dist")
                return False
            print("✅ Verified MinecraftFRP.exe")
            
            print()
            print("✅ Build output organized:")
            print(f"   Location: {self.build_output_dir.relative_to(self.root_dir)}")
            print(f"   - launcher.exe")
            print(f"   - app.dist/ ({file_count} files)")
            
            return True
            
        except Exception as e:
            print(f"❌ ERROR: Failed to organize build files: {e}")
            return False
    
    def build_installer(self) -> bool:
        """
        使用 Inno Setup 构建安装程序
        
        Returns:
            bool: 是否成功
        """
        print()
        print("=" * 80)
        print("🔧 Building Installer with Inno Setup")
        print("=" * 80)
        
        if not self.check_inno_setup():
            return False
        
        if not self.setup_script.exists():
            print(f"❌ ERROR: Setup script not found: {self.setup_script}")
            return False
        
        if not self.build_output_dir.exists():
            print(f"❌ ERROR: Build output directory not found: {self.build_output_dir}")
            print("   Please run build steps first")
            return False
        
        print("⏳ Building installer with Inno Setup...")
        print(f"📁 Build output: {self.build_output_dir}")
        print(f"📝 Inno Setup script: {self.setup_script}")
        print(f"🔧 Compiler: {self.iscc_path}")
        
        # 确保输出目录存在
        self.installer_output_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # 运行 Inno Setup 编译器
            print()
            print("▶️  Starting Inno Setup compilation...")
            print()
            
            result = subprocess.run(
                [
                    str(self.iscc_path),
                    str(self.setup_script),
                    f"/DBuildOutput={str(self.build_output_dir)}",
                    f"/DAppDist={str(self.build_output_dir / 'app.dist')}",
                    f"/O{str(self.installer_output_dir)}"
                ],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            
            # 显示输出
            if result.stdout:
                print(result.stdout)
            
            if result.returncode != 0:
                print()
                print(f"❌ ERROR: Compilation failed with exit code {result.returncode}")
                if result.stderr:
                    print("Error output:")
                    print(result.stderr)
                return False
            
            # 验证输出文件
            if not self.installer_path.exists():
                print(f"❌ ERROR: Installer not found at {self.installer_path}")
                return False
            
            size_mb = self.installer_path.stat().st_size / (1024 * 1024)
            print()
            print(f"✅ Installer built successfully!")
            print(f"   Location: {self.installer_path.relative_to(self.root_dir)}")
            print(f"   Size: {size_mb:.2f} MB")
            
            return True
            
        except Exception as e:
            print(f"❌ ERROR: Inno Setup compilation failed: {e}")
            return False
    
    def copy_to_release_dir(self) -> Tuple[bool, Optional[Path]]:
        """
        复制安装程序到 dist/版本号/ 目录
        
        Returns:
            Tuple[bool, Optional[Path]]: (是否成功, 最终路径)
        """
        print()
        print("=" * 80)
        print(f"📦 Copying Installer to Release Directory")
        print("=" * 80)
        
        try:
            # 创建发布目录
            self.release_dir.mkdir(parents=True, exist_ok=True)
            print(f"📁 Release directory: {self.release_dir.relative_to(self.root_dir)}")
            
            # 复制安装程序
            final_installer_path = self.release_dir / self.installer_filename
            shutil.copy2(self.installer_path, final_installer_path)
            
            size_mb = final_installer_path.stat().st_size / (1024 * 1024)
            print(f"✅ Installer: {final_installer_path.relative_to(self.root_dir)} ({size_mb:.2f} MB)")
            
            return True, final_installer_path
            
        except Exception as e:
            print(f"❌ ERROR: Failed to copy installer: {e}")
            return False, None
    
    def build_and_release(self, launcher_path: Path, app_dist_path: Path) -> Tuple[bool, Optional[Path]]:
        """
        完整的构建和发布流程
        
        Args:
            launcher_path: launcher.exe 路径
            app_dist_path: app.dist 目录路径
            
        Returns:
            Tuple[bool, Optional[Path]]: (是否成功, 最终安装程序路径)
        """
        # 1. 组织构建文件
        if not self.organize_build_files(launcher_path, app_dist_path):
            return False, None
        
        # 2. 构建安装程序
        if not self.build_installer():
            return False, None
        
        # 3. 复制到发布目录
        success, final_path = self.copy_to_release_dir()
        
        return success, final_path
