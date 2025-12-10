"""
V2 Architecture Builder
构建v2安装器架构（installer-based）
"""
import sys
import time
import zipfile
import shutil
from pathlib import Path
from typing import Optional, Tuple

from .config import BuildConfig
from .builder import NuitkaBuilder
from .deployer import Deployer
from .version_manager import VersionManager
from .utils import verify_dependencies, clean_cache


class V2Builder:
    """V2架构构建器"""
    
    def __init__(self, args):
        self.args = args
        self.config = BuildConfig()
        self.start_time = time.time()
        
        # 路径
        self.dist_dir = Path("dist")
        self.build_dir = Path("build")
        self.nuitka_cache_dir = self.build_dir / ".nuitka-cache"
        
        # 组件
        self.builder: Optional[NuitkaBuilder] = None
        self.version_manager: Optional[VersionManager] = None
        self.deployer: Optional[Deployer] = None
        
        # 构建结果
        self.launcher_exe_path: Optional[Path] = None
        self.main_app_dir: Optional[Path] = None
        self.installer_exe_path: Optional[Path] = None
        self.version_json_path: Optional[Path] = None
        
        self.launcher_build_time: float = 0
        self.main_build_time: float = 0
        self.installer_build_time: float = 0
    
    def print_header(self):
        """打印标题"""
        print("="*80)
        print(" 🚀 MinecraftFRP Build Script - V2 Installer Architecture")
        print("="*80)
    
    def verify_environment(self) -> bool:
        """验证环境"""
        if not verify_dependencies():
            return False
        if self.args.verify_only:
            print("\n✅ Verification complete. Exiting.")
            return False
        return True
    
    def setup_cache(self):
        """设置缓存"""
        if self.args.clean:
            clean_cache(str(self.nuitka_cache_dir))
    
    def print_configuration(self):
        """打印配置"""
        print(f"\n📦 V2 Build Configuration:")
        print(f"   Fast Build: {'Yes' if self.args.fast else 'No'}")
        print(f"   Deploy: {'Yes' if self.args.upload else 'No'}")
        print(f"\n✅ Python: {sys.executable}")
        print(f"✅ Nuitka cache: {self.nuitka_cache_dir}")
    
    def initialize_components(self) -> bool:
        """初始化组件"""
        current_version = self.config.get_version_string()
        self.version_manager = VersionManager(current_version)
        
        if not self.version_manager.update_version_file(current_version):
            return False
        
        self.builder = NuitkaBuilder(
            sys.executable,
            str(self.nuitka_cache_dir),
            fast_build=self.args.fast
        )
        
        return True
    
    def build_launcher(self) -> bool:
        """构建启动器"""
        print("\n" + "="*80)
        print("🔧 Building Launcher (launcher.exe)")
        print("="*80)
        
        start_time = time.time()
        launcher_build_dir = self.build_dir / "temp_launcher"
        launcher_build_dir.mkdir(parents=True, exist_ok=True)
        
        launcher_script = Path("src_launcher") / "launcher.py"
        
        if not launcher_script.exists():
            print(f"❌ ERROR: Launcher script not found: {launcher_script}")
            return False
        
        print(f"⏳ Building launcher from {launcher_script}...")
        print(f"📁 Build directory: {launcher_build_dir.absolute()}")
        
        # 构建命令 - 添加必要的插件和排除选项
        cmd = [
            sys.executable, "-m", "nuitka",
            "--standalone",
            "--onefile",
            f"--output-dir={launcher_build_dir}",
            "--output-filename=launcher.exe",
            "--enable-plugin=pyside6",
            "--nofollow-import-to=OpenSSL",  # 不要深度跟踪 OpenSSL
            "--nofollow-import-to=cryptography",  # 不要深度跟踪 cryptography
            "--windows-console-mode=disable",
            "--company-name=MitaHill",
            "--product-name=MinecraftFRP Launcher",
            "--file-version=" + self.config.get_version_string(),
            "--product-version=" + self.config.get_version_string(),
            "--copyright=Copyright (c) 2025 MitaHill",
            "--assume-yes-for-downloads",  # 自动确认下载
            str(launcher_script)
        ]
        
        if not self.args.fast:
            cmd.append("--lto=yes")
        
        print("📝 Nuitka command:")
        print("   " + " ".join(cmd))
        
        # 执行构建
        import subprocess
        print("\n▶️  Starting Nuitka compilation...")
        result = subprocess.run(cmd, capture_output=False)
        
        if result.returncode != 0:
            print(f"❌ ERROR: Launcher build failed with exit code {result.returncode}")
            return False
        
        # 查找生成的exe
        launcher_exe = launcher_build_dir / "launcher.exe"
        print(f"\n🔍 Looking for launcher.exe at: {launcher_exe.absolute()}")
        
        if not launcher_exe.exists():
            print(f"❌ ERROR: launcher.exe not found!")
            print(f"📁 Contents of {launcher_build_dir}:")
            for item in launcher_build_dir.iterdir():
                print(f"   - {item.name}")
            return False
        
        exe_size_mb = launcher_exe.stat().st_size / (1024 * 1024)
        print(f"✅ Found launcher.exe ({exe_size_mb:.2f} MB)")
        
        self.launcher_exe_path = launcher_exe
        self.launcher_build_time = time.time() - start_time
        
        print(f"✅ Launcher built successfully in {self.launcher_build_time:.2f}s")
        print(f"   Location: {self.launcher_exe_path}")
        
        return True
    
    def build_main_app(self) -> bool:
        """构建主应用（目录形式，非单文件）"""
        print("\n" + "="*80)
        print("🔧 Building Main Application (Directory Mode)")
        print("="*80)
        
        start_time = time.time()
        current_version = self.config.get_version_string()
        main_build_dir = self.build_dir / f"temp_main_app"
        main_build_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"⏳ Building main application...")
        print(f"📁 Build directory: {main_build_dir.absolute()}")
        
        # 构建命令（目录模式，不是onefile）
        cmd = [
            sys.executable, "-m", "nuitka",
            "--standalone",  # 只standalone，不onefile
            f"--output-dir={main_build_dir}",
            "--output-filename=MinecraftFRP.exe",
            "--enable-plugin=pyside6",
            "--include-data-dir=base=base",
            "--include-data-files=config/app_config.yaml=config/app_config.yaml",
            "--windows-console-mode=disable",
            "--company-name=MitaHill",
            "--product-name=MinecraftFRP",
            "--file-version=" + current_version,
            "--product-version=" + current_version,
            "--copyright=Copyright (c) 2025 MitaHill",
            "--assume-yes-for-downloads",
            "app.py"
        ]
        
        if not self.args.fast:
            cmd.append("--lto=yes")
        
        print("📝 Nuitka command:")
        print("   " + " ".join(cmd))
        
        # 执行构建
        import subprocess
        print("\n▶️  Starting Nuitka compilation...")
        result = subprocess.run(cmd, capture_output=False)
        
        if result.returncode != 0:
            print(f"❌ ERROR: Main app build failed with exit code {result.returncode}")
            return False
        
        # 查找生成的目录
        app_dist = main_build_dir / "app.dist"
        print(f"\n🔍 Looking for app.dist at: {app_dist.absolute()}")
        
        if not app_dist.exists() or not app_dist.is_dir():
            print(f"❌ ERROR: app.dist directory not found!")
            print(f"📁 Contents of {main_build_dir}:")
            for item in main_build_dir.iterdir():
                print(f"   - {item.name}")
            return False
        
        # 检查主程序exe
        main_exe = app_dist / "MinecraftFRP.exe"
        if not main_exe.exists():
            print(f"❌ ERROR: MinecraftFRP.exe not found in app.dist!")
            return False
        
        exe_size_mb = main_exe.stat().st_size / (1024 * 1024)
        print(f"✅ Found MinecraftFRP.exe ({exe_size_mb:.2f} MB)")
        
        # 统计文件数量
        file_count = sum(1 for _ in app_dist.rglob('*') if _.is_file())
        print(f"✅ app.dist contains {file_count} files")
        
        self.main_app_dir = app_dist
        self.main_build_time = time.time() - start_time
        
        print(f"✅ Main app built successfully in {self.main_build_time:.2f}s")
        print(f"   Location: {self.main_app_dir}")
        
        return True
    
    def create_app_package(self) -> bool:
        """组织构建产物到 Inno Setup 期望的目录结构"""
        print("\n" + "="*80)
        print("📦 Organizing Build Output for Inno Setup")
        print("="*80)
        
        current_version = self.config.get_version_string()
        output_dir = self.dist_dir / "MinecraftFRP_build"
        
        # 清理旧的输出目录
        if output_dir.exists():
            print(f"🧹 Cleaning old output directory...")
            shutil.rmtree(output_dir)
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"⏳ Organizing files to {output_dir}...")
        
        try:
            # 1. 复制 launcher.exe
            launcher_dest = output_dir / "launcher.exe"
            shutil.copy2(self.launcher_exe_path, launcher_dest)
            print(f"✅ Copied launcher.exe")
            
            # 2. 复制主应用目录
            app_dest = output_dir / "app.dist"
            shutil.copytree(self.main_app_dir, app_dest, dirs_exist_ok=True)
            
            # 统计文件
            file_count = sum(1 for _ in app_dest.rglob('*') if _.is_file())
            print(f"✅ Copied app.dist ({file_count} files)")
            
            # 3. 验证关键文件
            main_exe = app_dest / "MinecraftFRP.exe"
            if not main_exe.exists():
                print(f"❌ ERROR: MinecraftFRP.exe not found!")
                return False
            
            print(f"✅ Verified MinecraftFRP.exe")
            
            # 保存路径供后续使用
            self.build_output_dir = output_dir
            
            print(f"\n✅ Build output organized:")
            print(f"   Location: {output_dir}")
            print(f"   - launcher.exe")
            print(f"   - app.dist/ ({file_count} files)")
            
            # 注意: base/ 和 config/ 目录已经在项目根目录，Inno Setup 会直接读取
            
            return True
            
        except Exception as e:
            print(f"❌ ERROR: Failed to organize build output: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def build_installer(self) -> bool:
        """使用 Inno Setup 构建安装器"""
        print("\n" + "="*80)
        print("🔧 Building Installer with Inno Setup")
        print("="*80)
        
        start_time = time.time()
        
        # 导入 Inno Setup 构建器
        from .inno_builder import InnoSetupBuilder
        inno = InnoSetupBuilder()
        
        if not inno.is_available():
            print("❌ ERROR: Inno Setup not available!")
            return False
        
        # 检查 setup.iss 脚本
        script_path = Path("setup.iss")
        if not script_path.exists():
            print(f"❌ ERROR: Inno Setup script not found: {script_path}")
            return False
        
        print(f"⏳ Building installer with Inno Setup...")
        
        # 确保所有构建产物都在正确位置
        build_output_dir = self.dist_dir / "MinecraftFRP_build"
        if not build_output_dir.exists():
            print(f"❌ ERROR: Build output directory not found: {build_output_dir}")
            return False
        
        print(f"📁 Build output: {build_output_dir.absolute()}")
        print(f"📦 Launcher: {self.launcher_exe_path}")
        print(f"📦 Main app: {self.main_app_dir}")
        
        # 使用 Inno Setup 编译
        if not inno.build(script_path, output_dir=self.dist_dir):
            print("❌ ERROR: Inno Setup compilation failed!")
            return False
        
        # 查找生成的安装器
        output_filename = inno.get_output_filename(script_path)
        if not output_filename:
            output_filename = f"MinecraftFRP_Setup_{self.config.get_version_string()}"
        
        installer_exe = self.dist_dir / f"{output_filename}.exe"
        
        print(f"\n🔍 Looking for installer at: {installer_exe.absolute()}")
        
        if not installer_exe.exists():
            print(f"❌ ERROR: Installer exe not found!")
            # 尝试查找 dist 目录中的 exe 文件
            print(f"📁 Contents of {self.dist_dir}:")
            if self.dist_dir.exists():
                for item in self.dist_dir.iterdir():
                    if item.suffix == '.exe':
                        print(f"  Found: {item.name}")
                        installer_exe = item
                        break
        
        if not installer_exe.exists():
            print("❌ ERROR: Could not find generated installer!")
            return False
        
        installer_size_mb = installer_exe.stat().st_size / (1024 * 1024)
        print(f"✅ Found {installer_exe.name} ({installer_size_mb:.2f} MB)")
        
        self.installer_exe_path = installer_exe
        self.installer_build_time = time.time() - start_time
        
        print(f"✅ Installer built successfully in {self.installer_build_time:.2f}s")
        print(f"   Location: {installer_exe}")
        
        return True
        
        if not installer_exe.exists():
            print(f"❌ ERROR: Installer exe not found!")
            print(f"📁 Contents of {installer_build_dir}:")
            for item in installer_build_dir.iterdir():
                print(f"   - {item.name}")
            return False
        
        exe_size_mb = installer_exe.stat().st_size / (1024 * 1024)
        print(f"✅ Found Minecraft_FRP_Installer.exe ({exe_size_mb:.2f} MB)")
        
        self.installer_exe_path = installer_exe
        self.installer_build_time = time.time() - start_time
        
        print(f"✅ Installer built successfully in {self.installer_build_time:.2f}s")
        print(f"   Location: {self.installer_exe_path}")
        
        return True
    
    def move_to_dist(self) -> bool:
        """移动installer到最终dist目录"""
        print("\n" + "="*80)
        print("📦 Finalizing Installer Location")
        print("="*80)
        
        current_version = self.config.get_version_string()
        final_dist_dir = self.dist_dir / f"MinecraftFRP_{current_version}_installer"
        
        print(f"📁 Target directory: {final_dist_dir.absolute()}")
        print(f"📄 Source installer: {self.installer_exe_path.absolute()}")
        
        # 验证源文件存在
        if not self.installer_exe_path.exists():
            print(f"❌ ERROR: Source installer not found at {self.installer_exe_path}")
            return False
        
        source_size_mb = self.installer_exe_path.stat().st_size / (1024 * 1024)
        print(f"📊 Source file size: {source_size_mb:.2f} MB")
        
        # 清理并创建目标目录
        if final_dist_dir.exists():
            shutil.rmtree(final_dist_dir)
        final_dist_dir.mkdir(parents=True, exist_ok=True)
        
        # 复制installer并改名
        try:
            final_installer = final_dist_dir / f"MinecraftFRP_Setup_{current_version}.exe"
            print(f"📋 Copying installer...")
            print(f"   From: {self.installer_exe_path}")
            print(f"   To:   {final_installer}")
            
            shutil.copy2(self.installer_exe_path, final_installer)
            
            # 验证
            if not final_installer.exists():
                print(f"❌ ERROR: Installer not found after copy!")
                return False
            
            copied_size_mb = final_installer.stat().st_size / (1024 * 1024)
            print(f"✅ Copied successfully ({copied_size_mb:.2f} MB)")
            
            # 更新引用
            self.installer_exe_path = final_installer
            
            print(f"✅ Installer: {final_installer.name}")
            
            return True
            
        except Exception as e:
            print(f"❌ ERROR: Failed to copy installer: {e}")
            return False
            
            # 再次验证文件存在
            print(f"🔍 Final verification: {self.installer_exe_path.exists()}")
            
        except Exception as e:
            print(f"❌ ERROR: Failed to copy installer: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        self.final_dist_dir = final_dist_dir
        print(f"✅ Artifacts moved successfully")
        return True
    
    def generate_version_json(self) -> bool:
        """生成version.json"""
        print("\n" + "="*80)
        print("📋 Generating version.json")
        print("="*80)
        
        # 生成发布说明
        version_url = "https://z.clash.ink/chfs/shared/MinecraftFRP/Data/version.json"
        release_notes = self.version_manager.generate_release_notes(version_url)
        
        # 创建version.json（指向installer）
        version_json_dir = self.dist_dir / "minecraft_version_index"
        version_json_dir.mkdir(parents=True, exist_ok=True)
        
        self.version_json_path = version_json_dir / "version.json"
        download_url = "https://z.clash.ink/chfs/shared/MinecraftFRP/lastet/Minecraft_FRP_Installer.exe"
        
        if not self.version_manager.create_version_json(
            self.installer_exe_path,
            download_url,
            str(self.version_json_path),
            release_notes
        ):
            return False
        
        print(f"✅ version.json: {self.version_json_path}")
        return True
    
    def deploy(self) -> bool:
        """部署到服务器"""
        if not self.args.upload:
            print("\n⏭️  Skipping deployment (use --upload to deploy).")
            return True
        
        # 获取SSH配置
        ssh_cfg = self.config.get_ssh_config()
        ssh_user = self.args.ssh_user or ssh_cfg.get('user')
        ssh_pass = self.args.ssh_pass or ssh_cfg.get('password')
        
        if not ssh_user or not ssh_pass:
            print("\n❌ ERROR: SSH credentials missing.")
            return False
        
        print("\n" + "="*80)
        print("🚀 Deploying to Server")
        print("="*80)
        
        self.deployer = Deployer(ssh_cfg, ssh_user, ssh_pass)
        
        # 上传installer和version.json
        return self.deployer.deploy(self.installer_exe_path, str(self.version_json_path))
    
    def cleanup(self):
        """清理build目录"""
        print(f"\n🧹 Cleaning build directory...")
        print(f"📁 Build directory: {self.build_dir.absolute()}")
        
        # 再次确认installer已经移动到dist
        if hasattr(self, 'installer_exe_path'):
            print(f"🔍 Verifying installer location before cleanup...")
            print(f"   Installer path: {self.installer_exe_path}")
            print(f"   Exists: {self.installer_exe_path.exists()}")
            if not self.installer_exe_path.exists():
                print(f"⚠️  WARNING: Installer not found! Aborting cleanup to preserve files.")
                return
        
        if self.build_dir.exists():
            try:
                print(f"🗑️  Removing build directory...")
                shutil.rmtree(self.build_dir)
                print(f"✅ Build directory cleaned: {self.build_dir}")
            except Exception as e:
                print(f"⚠️  Warning: Could not fully clean: {e}")
                import traceback
                traceback.print_exc()
    
    def print_summary(self, deployment_successful: bool):
        """打印总结"""
        overall_time = time.time() - self.start_time
        print("\n" + "="*80)
        if self.args.upload and not deployment_successful:
            print(" ⚠️  BUILD SUCCESSFUL, BUT DEPLOYMENT FAILED!")
        else:
            print(" ✅ V2 BUILD COMPLETED SUCCESSFULLY!")
        print("="*80)
        print(f"📊 Build Summary:")
        print(f"   Launcher: {self.launcher_build_time:.2f}s")
        print(f"   Main App: {self.main_build_time:.2f}s")
        print(f"   Installer: {self.installer_build_time:.2f}s")
        print(f"   Total: {overall_time:.2f}s ({overall_time/60:.1f} minutes)")
        print(f"   Output: {self.final_dist_dir}")
        print("="*80)
    
    def run(self) -> int:
        """执行构建流程"""
        self.print_header()
        
        if not self.verify_environment():
            return 0 if self.args.verify_only else 1
        
        self.setup_cache()
        self.print_configuration()
        
        if not self.initialize_components():
            return 1
        
        if not self.build_launcher():
            return 1
        
        if not self.build_main_app():
            return 1
        
        if not self.create_app_package():
            return 1
        
        if not self.build_installer():
            return 1
        
        if not self.move_to_dist():
            return 1
        
        if not self.generate_version_json():
            return 1
        
        deployment_successful = self.deploy()
        
        self.cleanup()
        self.print_summary(deployment_successful)
        
        return 0 if (not self.args.upload or deployment_successful) else 1
