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
        
        # 构建命令 - 单文件、去除 PySide6 插件，静默后台
        cmd = [
            sys.executable, "-m", "nuitka",
            "--standalone",
            "--onefile",
            f"--output-dir={launcher_build_dir}",
            "--output-filename=launcher.exe",
            "--nofollow-import-to=OpenSSL",
            "--nofollow-import-to=cryptography",
            "--windows-console-mode=disable",
            "--company-name=MitaHill",
            "--product-name=MinecraftFRP Launcher",
            "--file-version=" + self.config.get_version_string(),
            "--product-version=" + self.config.get_version_string(),
            "--copyright=Copyright (c) 2025 MitaHill",
            "--assume-yes-for-downloads",
            "--disable-cache=ccache",
        ]

        # 可选：设置EXE图标
        ico = Path("base") / "logo.ico"
        if ico.exists():
            cmd.append(f"--windows-icon-from-ico={ico}")

        cmd.append(str(launcher_script))
        
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
        
        # 查找生成的exe（onefile 输出在构建目录根）
        launcher_exe = launcher_build_dir / "launcher.exe"
        print(f"\n🔍 Looking for launcher.exe at: {launcher_exe.absolute()}")
        if not launcher_exe.exists():
            print(f"❌ ERROR: launcher.exe not found in build directory!")
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
            "--include-data-files=config/app_config.yaml=config/app_config.yaml",
            "--windows-console-mode=disable",
            "--company-name=MitaHill",
            "--product-name=MinecraftFRP",
            "--file-version=" + current_version,
            "--product-version=" + current_version,
            "--copyright=Copyright (c) 2025 MitaHill",
            "--assume-yes-for-downloads",
            "--disable-cache=ccache",
        ]

        ico = Path("base") / "logo.ico"
        if ico.exists():
            cmd.append(f"--windows-icon-from-ico={ico}")

        cmd.append("app.py")
        
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
        dist_dirs = list(main_build_dir.glob("*.dist"))
        if not dist_dirs:
            print(f"❌ ERROR: No .dist directory found in {main_build_dir}!")
            return False
        
        # 重命名为 MitaHill-FRP-APP
        source_dist = dist_dirs[0]
        target_dist = main_build_dir / "MitaHill-FRP-APP"
        
        if target_dist.exists():
            shutil.rmtree(target_dist)
            
        source_dist.rename(target_dist)
        app_dist = target_dist
        
        print(f"\n🔍 Renamed {source_dist.name} to MitaHill-FRP-APP")
        
        if not app_dist.exists() or not app_dist.is_dir():
            print(f"❌ ERROR: MitaHill-FRP-APP directory not found!")
            print(f"📁 Contents of {main_build_dir}:")
            for item in main_build_dir.iterdir():
                print(f"   - {item.name}")
            return False
        
        # 检查主程序exe
        main_exe = app_dist / "MinecraftFRP.exe"
        if not main_exe.exists():
            print(f"❌ ERROR: MinecraftFRP.exe not found in MitaHill-FRP-APP!")
            return False
        
        exe_size_mb = main_exe.stat().st_size / (1024 * 1024)
        print(f"✅ Found MinecraftFRP.exe ({exe_size_mb:.2f} MB)")
        
        # 统计文件数量
        file_count = sum(1 for _ in app_dist.rglob('*') if _.is_file())
        print(f"✅ MitaHill-FRP-APP contains {file_count} files")
        
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
        # 构建缓存目录放在 build/，避免 dist/ 的同步锁定
        output_dir = self.build_dir / "MinecraftFRP_build"
        
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

            # 1.5 单文件模式下无依赖目录，跳过
            
            # 2. 复制主应用目录
            app_dest = output_dir / "MitaHill-FRP-APP"
            shutil.copytree(self.main_app_dir, app_dest, dirs_exist_ok=True, ignore=shutil.ignore_patterns("logs"))
            
            # 统计文件
            file_count = sum(1 for _ in app_dest.rglob('*') if _.is_file())
            print(f"✅ Copied MitaHill-FRP-APP ({file_count} files)")
            
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
            print(f"   - nuitka_launcher/ (if present)")
            print(f"   - MitaHill-FRP-APP/ ({file_count} files)")
            
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
        
        # 确保所有构建产物都在正确位置（使用 build/ 作为缓存目录）
        build_output_dir = getattr(self, 'build_output_dir', None) or (self.build_dir / "MinecraftFRP_build")
        if not build_output_dir.exists():
            print(f"❌ ERROR: Build output directory not found: {build_output_dir}")
            return False
        
        print(f"📁 Build output: {build_output_dir.absolute()}")
        print(f"📦 Launcher: {self.launcher_exe_path}")
        print(f"📦 Main app: {self.main_app_dir}")
        
        # 使用 Inno Setup 编译，传入动态路径定义
        defines = {
            "BuildOutput": str(build_output_dir.resolve()),
            "AppDist": str((build_output_dir / "MitaHill-FRP-APP").resolve()),
            "MyAppVersion": self.config.get_version_string(),
            "Channel": getattr(self.args, "channel", "dev"),
        }
        # 将 Inno 输出放在 build/installer_output
        installer_out_dir = self.build_dir / "installer_output"
        installer_out_dir.mkdir(parents=True, exist_ok=True)
        if not inno.build(script_path, output_dir=installer_out_dir, defines=defines):
            print("❌ ERROR: Inno Setup compilation failed!")
            return False
        
        # 查找生成的安装器
        output_filename = inno.get_output_filename(script_path)
        version_str = self.config.get_version_string()
        if output_filename:
            # 将脚本中的宏占位符替换为实际版本号
            output_filename = output_filename.replace("{#MyAppVersion}", version_str)
        else:
            output_filename = f"MinecraftFRP_Setup_{version_str}"
        
        installer_exe = installer_out_dir / f"{output_filename}.exe"
        
        print(f"\n🔍 Looking for installer at: {installer_exe.absolute()}")
        
        if not installer_exe.exists():
            print(f"❌ ERROR: Installer exe not found! Fallback to pattern search.")
            # 回退：按模式在输出目录中查找安装器
            candidates = list(installer_out_dir.glob(f"MinecraftFRP_Setup_{version_str}*.exe"))
            if candidates:
                installer_exe = candidates[0]
        
        if not installer_exe.exists():
            print("❌ ERROR: Could not find generated installer!")
            return False
        
        installer_size_mb = installer_exe.stat().st_size / (1024 * 1024)
        print(f"✅ Found {installer_exe.name} ({installer_size_mb:.2f} MB)")
        
        self.installer_exe_path = installer_exe
        self.installer_build_time = time.time() - start_time
        
        print(f"✅ Installer built successfully in {self.installer_build_time:.2f}s")
        print(f"   Location: {installer_exe}")
        
        # Dev通道命名为 *_installer_dev.exe（仅在最终拷贝前改名使用）
        self._channel = getattr(self.args, 'channel', 'dev')
        
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
        # 最终发布目录改为 dist/MinecraftFRP_<version>/
        final_dist_dir = self.dist_dir / f"MinecraftFRP_{current_version}"
        # 供总结与后续步骤使用
        self.final_dist_dir = final_dist_dir
        
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
            # 根据通道命名 (固定文件名)
            if getattr(self, '_channel', 'dev') == 'dev':
                final_name = "MitaHill_Dev_FRP.exe"
            else:
                final_name = "MitaHill_Stable_FRP.exe"
                
            final_installer = final_dist_dir / final_name
            
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
    
    def generate_version_json(self) -> bool:
        """生成version.json"""
        print("\n" + "="*80)
        print("📋 Generating version.json")
        print("="*80)
        
        # 生成发布说明：优先使用 --update-messages/-u 指定的内容；否则生成默认信息（不依赖 Git 提交范围）
        if getattr(self.args, 'update_messages', None):
            release_notes = self.args.update_messages
            print("INFO: Using manual update messages (-u/--update-messages). Ignoring Git logs.")
        else:
            # 默认更新日志：使用当前日期时间与当前分支名
            try:
                import subprocess, datetime
                branch = subprocess.check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], stderr=subprocess.DEVNULL).decode('utf-8').strip()
            except Exception:
                branch = 'unknown-branch'
            now_iso = __import__('datetime').datetime.utcnow().isoformat(timespec='milliseconds') + 'Z'
            release_notes = f"{now_iso} 根据git分支创建了 ({branch})"
            print("INFO: Using default update message from current branch and time.")
        
        # 创建version.json（指向installer），放入最终发布目录
        version_json_dir = getattr(self, 'final_dist_dir', (self.dist_dir / f"MinecraftFRP_{self.config.get_version_string()}"))
        version_json_dir.mkdir(parents=True, exist_ok=True)
        
        self.version_json_path = version_json_dir / "version.json"
        
        # 根据通道设置下载URL（固定URL）
        channel = getattr(self, '_channel', 'dev')
        if channel == 'dev':
            download_url = "https://z.clash.ink/chfs/shared/MinecraftFRP/Dev/MitaHill_Dev_FRP.exe"
        else:
            download_url = "https://z.clash.ink/chfs/shared/MinecraftFRP/Stable/MitaHill_Stable_FRP.exe"
        
        # 调用 VersionManager 的新逻辑（包含下载-合并-保存）
        if not self.version_manager.create_version_json(
            self.installer_exe_path,
            download_url,
            str(self.version_json_path),
            release_notes,
            channel=channel
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
        
        # 根据通道动态设置远程路径
        channel = getattr(self, '_channel', 'dev')
        base_remote_path = "/root/chfs/share/MinecraftFRP"
        
        if channel == 'dev':
            remote_exe_path = f"{base_remote_path}/Dev/MitaHill_Dev_FRP.exe"
        else:
            remote_exe_path = f"{base_remote_path}/Stable/MitaHill_Stable_FRP.exe"
            
        # 临时修改 Deployer 实例的路径配置
        # 注意：这里我们重新实例化 Deployer 或修改 config 传入
        # 为了简单，我们手动更新 ssh_config 字典的副本
        deploy_config = ssh_cfg.copy()
        deploy_config['exe_path'] = remote_exe_path
        # version.json 路径保持不变
        deploy_config['version_json_path'] = f"{base_remote_path}/Data/version.json"
        
        self.deployer = Deployer(deploy_config, ssh_user, ssh_pass)
        
        # 上传installer和version.json
        return self.deployer.deploy(self.installer_exe_path, str(self.version_json_path))
    
    def cleanup(self):
        """清理build目录"""
        print(f"\n⏭️  Skipping cleanup for debugging purposes.")
        return

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
        
        # 在开始编译前，清空 build/ 目录中的所有缓存
        try:
            if self.build_dir.exists():
                print("\n🧹 Pre-cleaning build directory before compilation...")
                print(f"📁 Removing: {self.build_dir.absolute()}")
                import shutil
                shutil.rmtree(self.build_dir)
                print("✅ Build directory cleared")
        except Exception as e:
            print(f"⚠️  Warning: Failed to pre-clean build directory: {e}")
        
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
        
        # 按要求移除Git写操作，仅保留信息获取（已删除自动打标签）
        
        deployment_successful = self.deploy()
        
        self.cleanup()
        self.print_summary(deployment_successful)
        
        return 0 if (not self.args.upload or deployment_successful) else 1
