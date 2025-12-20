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
import subprocess

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
        """构建启动器 (使用 PyInstaller)"""
        print("\n" + "="*80)
        print("🔧 Building Launcher with PyInstaller (Launcher.exe)")
        print("="*80)
        
        start_time = time.time()
        
        launcher_script = Path("src_launcher/launcher.py")
        app_name = "Launcher"
        icon_path = Path("base/logo.ico")
        build_path = self.build_dir / "launcher_build" # 独立的构建缓存

        if not launcher_script.exists():
            print(f"❌ 错误: 启动器脚本未找到: {launcher_script}", file=sys.stderr)
            return False

        icon_option = f"--icon={icon_path}" if icon_path.exists() else ""

        # 清理旧的构建文件
        print("🧹 正在清理旧的启动器构建文件...")
        if self.dist_dir.exists():
            for f in self.dist_dir.glob(f"{app_name}*"):
                print(f"  - 删除 {f}")
                if f.is_dir():
                    shutil.rmtree(f)
                else:
                    f.unlink()
        if build_path.exists():
            print(f"  - 删除目录 {build_path}")
            shutil.rmtree(build_path)

        print(f"\n🚀 开始使用 PyInstaller 构建 {app_name}.exe (onedir mode)...")

        command = [
            sys.executable, "-m", "PyInstaller",
            "--noconfirm", "--onedir", "--windowed",
            f"--name={app_name}",
            icon_option,
            f"--distpath={self.dist_dir}",
            f"--workpath={build_path}",
            f"--specpath={build_path}",
            "--contents-directory=launcher_internal", 
            str(launcher_script)
        ]
        command = [arg for arg in command if arg]

        print(" ".join(command))

        try:
            result = subprocess.run(
                command, check=True, capture_output=True, text=True, encoding='utf-8'
            )
            print(result.stdout)
            
            # check dist/Launcher directory
            launcher_dist_dir = self.dist_dir / app_name
            launcher_exe = launcher_dist_dir / f"{app_name}.exe"
            
            if not launcher_exe.exists():
                print("❌ ERROR: Launcher.exe not found in dist/Launcher/ after build!", file=sys.stderr)
                return False
            
            self.launcher_exe_path = launcher_exe
            self.launcher_dir = launcher_dist_dir
            self.launcher_build_time = time.time() - start_time
            
            exe_size_mb = launcher_exe.stat().st_size / (1024 * 1024)
            print(f"✅ Launcher built successfully in {self.launcher_build_time:.2f}s ({exe_size_mb:.2f} MB)")
            print(f"   Location: {self.launcher_exe_path}")
            
            return True
            
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print("❌ ERROR: Launcher build failed!", file=sys.stderr)
            if isinstance(e, subprocess.CalledProcessError):
                print(e.stdout, file=sys.stdout)
                print(e.stderr, file=sys.stderr)
            else:
                print("PyInstaller 未安装或未在 PATH 中。请运行: pip install pyinstaller", file=sys.stderr)
            return False

    def build_main_app(self) -> bool:
        """构建主应用（使用 PyInstaller + 防破解加密）"""
        print("\n" + "="*80)
        print("🔧 Building Main Application with PyInstaller (Secured)")
        print("="*80)
        
        start_time = time.time()
        current_version = self.config.get_version_string()
        
        # PyInstaller 工作目录
        work_path = self.build_dir / "temp_main_app_build"
        # PyInstaller 输出目录 (dist)
        dist_path = self.build_dir / "temp_main_app_dist"
        
        # 清理
        if work_path.exists(): shutil.rmtree(work_path)
        if dist_path.exists(): shutil.rmtree(dist_path)
        
        work_path.mkdir(parents=True, exist_ok=True)
        dist_path.mkdir(parents=True, exist_ok=True)
        
        # 生成加密密钥 (16 chars)
        import secrets
        import string
        key = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(16))
        print(f"🔐 Generated Bytecode Encryption Key: {key}")
        
        app_name = "MinecraftFRP"
        script_path = "app.py"
        icon_path = Path("base/logo.ico")
        
        print(f"⏳ Building main application...")
        
        # 构建 PyInstaller 命令
        cmd = [
            sys.executable, "-m", "PyInstaller",
            "--noconfirm",
            "--onedir",
            "--windowed",  # 无控制台
            f"--name={app_name}",
            # f"--key={key}",  # 字节码加密 - Removed as per PyInstaller v6.0+
            f"--workpath={work_path}",
            f"--distpath={dist_path}",
            "--clean",
            f"--contents-directory=MinecraftFRP_internal",
            
            # 数据文件 (Windows separators ;)
            # base 目录 -> base
            "--add-data=base;base",
            # 配置文件
            "--add-data=config/app_config.yaml;config",
            "--add-data=config/special_nodes.json;config", 
             
            # 隐藏导入 (防止漏掉)
            "--hidden-import=requests",
            "--hidden-import=yaml",
            "--hidden-import=PySide6",
            "--hidden-import=packaging",
            "--hidden-import=paramiko",
            
            # 排除不必要的模块 (减少体积/干扰)
            "--exclude-module=tkinter",
            "--exclude-module=matplotlib",
            
            # 版本信息 (如果有version file的话，这里暂时略过，或者可以动态生成一个version file)
        ]
        
        if icon_path.exists():
            cmd.append(f"--icon={icon_path}")
            
        cmd.append(script_path)
        
        print("📝 PyInstaller command:")
        # Hide key in logs
        log_cmd = [c if not c.startswith("--key=") else "--key=********" for c in cmd]
        print("   " + " ".join(log_cmd))
        
        # 执行构建
        import subprocess
        print("\n▶️  Starting PyInstaller compilation...")
        try:
            result = subprocess.run(cmd, check=True, text=True, capture_output=True, encoding='utf-8')
            print("✅ PyInstaller completed successfully.")
            # print(result.stdout) # Output might be too long, show only if needed or error
        except subprocess.CalledProcessError as e:
            print(f"❌ ERROR: PyInstaller failed with code {e.returncode}")
            print("STDERR:", e.stderr)
            return False
            
        # 处理输出目录
        # PyInstaller 输出在 dist_path / app_name
        generated_dir = dist_path / app_name
        
        if not generated_dir.exists():
            print(f"❌ ERROR: Output directory not found: {generated_dir}")
            return False
            
        # 我们需要将其重命名/移动为 MitaHill-FRP-APP 并在 build/temp_main_app 下
        # 为了兼容后续 create_app_package 的逻辑 (它寻找 self.main_app_dir)
        
        target_parent = self.build_dir / "temp_main_app"
        target_dir = target_parent / "MitaHill-FRP-APP"
        
        if target_parent.exists(): shutil.rmtree(target_parent)
        target_parent.mkdir(parents=True, exist_ok=True)
        
        print(f"📋 Moving build artifact to {target_dir}...")
        try:
            shutil.move(str(generated_dir), str(target_dir))
        except Exception as e:
            print(f"❌ ERROR: Failed to move output directory: {e}")
            return False
            
        self.main_app_dir = target_dir
        
        # 验证
        main_exe = self.main_app_dir / f"{app_name}.exe"
        if not main_exe.exists():
            print(f"❌ ERROR: Main executable not found: {main_exe}")
            return False
            
        exe_size_mb = main_exe.stat().st_size / (1024 * 1024)
        print(f"✅ Found {main_exe.name} ({exe_size_mb:.2f} MB)")
        
        # 统计文件
        file_count = sum(1 for _ in self.main_app_dir.rglob('*') if _.is_file())
        print(f"✅ MitaHill-FRP-APP contains {file_count} files")
        
        self.main_build_time = time.time() - start_time
        print(f"✅ Main app built successfully in {self.main_build_time:.2f}s")
        
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
            # 1. 复制 launcher (目录模式)
            print(f"📋 Copying launcher from {self.launcher_dir} to {output_dir}")
            shutil.copytree(self.launcher_dir, output_dir, dirs_exist_ok=True)
            print(f"✅ Copied Launcher directory contents")
            
            # 2. 复制主应用目录 (合并到根目录，而不是子目录)
            # app_dest = output_dir / "MitaHill-FRP-APP"
            # shutil.copytree(self.main_app_dir, app_dest, dirs_exist_ok=True, ignore=shutil.ignore_patterns("logs"))
            print(f"📋 Copying main app from {self.main_app_dir} to {output_dir}")
            shutil.copytree(self.main_app_dir, output_dir, dirs_exist_ok=True, ignore=shutil.ignore_patterns("logs"))
            
            # 统计文件
            file_count = sum(1 for _ in output_dir.rglob('*') if _.is_file())
            print(f"✅ Merged MitaHill-FRP-APP ({file_count} files total)")
            
            # 3. 验证关键文件
            main_exe = output_dir / "MinecraftFRP.exe"
            if not main_exe.exists():
                print(f"❌ ERROR: MinecraftFRP.exe not found!")
                return False
            
            print(f"✅ Verified MinecraftFRP.exe")
            
            # 保存路径供后续使用
            self.build_output_dir = output_dir
            
            print(f"\n✅ Build output organized:")
            print(f"   Location: {output_dir}")
            print(f"   - Launcher.exe")
            print(f"   - MinecraftFRP.exe")
            
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
            # AppDist 指向 build_output_dir，因为文件已经合并
            "AppDist": str(build_output_dir.resolve()),
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
        if getattr(self.args, 'update-messages', None):
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
