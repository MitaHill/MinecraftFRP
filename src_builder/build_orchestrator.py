"""
Build Orchestrator - 构建流程协调器
负责协调整个构建流程的各个阶段
"""
import sys
import time
import shutil
from pathlib import Path
from typing import Optional, Tuple

from .config import BuildConfig
from .builder import NuitkaBuilder
from .deployer import Deployer
from .version_manager import VersionManager
from .utils import verify_dependencies, clean_cache


class BuildOrchestrator:
    """构建流程协调器，负责管理整个构建生命周期"""
    
    def __init__(self, args):
        """
        初始化构建协调器
        
        Args:
            args: 命令行参数对象
        """
        self.args = args
        self.config = BuildConfig()
        self.start_time = time.time()
        
        # 路径配置
        self.dist_dir = Path("dist")
        self.build_dir = Path("build")
        self.nuitka_cache_dir = self.build_dir / ".nuitka-cache"
        
        # 组件
        self.builder: Optional[NuitkaBuilder] = None
        self.deployer: Optional[Deployer] = None
        self.version_manager: Optional[VersionManager] = None
        
        # 构建结果
        self.updater_exe_path: Optional[str] = None
        self.final_exe_path: Optional[Path] = None
        self.version_json_path: Optional[Path] = None
        self.final_dist_dir: Optional[Path] = None
        self.updater_build_time: float = 0
        self.main_build_time: float = 0
    
    def print_header(self):
        """打印构建脚本标题"""
        print("="*80)
        print(" 🚀 MinecraftFRP Build & Deploy Script (Modular)")
        print("="*80)
    
    def verify_environment(self) -> bool:
        """
        验证构建环境
        
        Returns:
            bool: 验证是否成功
        """
        if not verify_dependencies():
            return False
        
        if self.args.verify_only:
            print("\n✅ Verification complete. Exiting.")
            return False
        
        return True
    
    def setup_cache(self):
        """设置缓存目录"""
        if self.args.clean:
            clean_cache(str(self.nuitka_cache_dir))
    
    def print_configuration(self):
        """打印构建配置"""
        print(f"\n📦 Build Configuration:")
        print(f"   Fast Build: {'Yes (no LTO)' if self.args.fast else 'No (with LTO)'}")
        print(f"   Deploy: {'Yes' if self.args.upload else 'No'}")
        print(f"   Skip Updater: {'Yes' if self.args.skip_updater else 'No'}")
        print(f"\n✅ Python: {sys.executable}")
        print(f"✅ Nuitka cache: {self.nuitka_cache_dir}")
    
    def initialize_components(self):
        """初始化各个构建组件"""
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
    
    def build_updater(self) -> bool:
        """
        构建更新器
        
        Returns:
            bool: 构建是否成功
        """
        updater_build_dir = self.build_dir / "temp_updater"
        self.updater_exe_path, self.updater_build_time = self.builder.build_updater(
            str(updater_build_dir),
            skip=self.args.skip_updater
        )
        return self.updater_exe_path is not None
    
    def build_main_application(self) -> bool:
        """
        构建主应用程序
        
        Returns:
            bool: 构建是否成功
        """
        current_version = self.config.get_version_string()
        temp_main_build_dir = self.build_dir / f"MinecraftFRP_{current_version}"
        temp_main_build_dir.mkdir(parents=True, exist_ok=True)
        
        self.final_exe_path, self.main_build_time = self.builder.build_main_app(
            current_version,
            str(temp_main_build_dir),
            self.updater_exe_path
        )
        
        if not self.final_exe_path:
            return False
        
        # 暂存临时目录路径
        self._temp_main_build_dir = temp_main_build_dir
        return True
    
    def post_build_processing(self) -> bool:
        """
        构建后处理（生成元数据、移动文件）
        
        Returns:
            bool: 处理是否成功
        """
        print("\n" + "="*80)
        print("📋 Post-Build Processing")
        print("="*80)
        
        print(f"\n🔒 Calculating SHA256 and generating metadata...")
        print(f"✅ Git: {self.version_manager.git_branch}@{self.version_manager.git_hash}")
        
        # 生成版本信息（先生成发布说明，再移动产物，最后在 dist 中生成 version.json）
        version_url = "https://z.clash.ink/chfs/shared/MinecraftFRP/Data/version.json"
        release_notes = self.version_manager.generate_release_notes(version_url)

        # 先移动到 dist 目录，确保后续路径一致
        if not self._move_to_dist():
            return False

        # 在 dist 目录中生成 version.json，避免移动过程中丢失
        self.version_json_path = self.final_dist_dir / "version.json"
        download_url = "https://z.clash.ink/chfs/shared/MinecraftFRP/lastet/MinecraftFRP.exe"
        if not self.version_manager.create_version_json(
            self.final_exe_path,
            download_url,
            str(self.version_json_path),
            release_notes,
            channel=getattr(self.args, 'channel', 'stable')
        ):
            return False
        
        return True
    
    def _move_to_dist(self) -> bool:
        """
        将构建产物移动到dist目录
        
        Returns:
            bool: 移动是否成功
        """
        print(f"\n📦 Moving artifacts to dist/...")
        current_version = self.config.get_version_string()
        self.final_dist_dir = self.dist_dir / f"MinecraftFRP_{current_version}"
        
        # 删除旧的dist
        if self.final_dist_dir.exists():
            try:
                shutil.rmtree(self.final_dist_dir)
            except Exception as e:
                print(f"⚠️  Warning: Could not remove old dist: {e}")
        
        # 移动到dist
        try:
            shutil.move(str(self._temp_main_build_dir), str(self.final_dist_dir))
            print(f"✅ Artifacts moved to: {self.final_dist_dir}")
        except Exception as e:
            print(f"❌ ERROR: Failed to move artifacts: {e}")
            return False
        
        # 更新路径指向
        self.final_exe_path = self.final_dist_dir / "MinecraftFRP.exe"
        self.version_json_path = self.final_dist_dir / "version.json"
        
        return True
    
    def deploy(self) -> bool:
        """
        部署到服务器 (客户端/服务端)
        
        Returns:
            bool: 部署是否成功
        """
        # 如果既没有上传客户端也没有部署服务端，跳过
        if not self.args.upload and not getattr(self.args, 'server_on', False):
            print("\n⏭️  Skipping deployment (use --upload or --server-on).")
            return True
        
        # 获取SSH凭据
        ssh_cfg = self.config.get_ssh_config()
        ssh_user = self.args.ssh_user or ssh_cfg.get('user')
        ssh_pass = self.args.ssh_pass or ssh_cfg.get('password')
        
        if not ssh_user or not ssh_pass:
            print("\n❌ ERROR: SSH credentials missing. Provide via cicd.yaml or --ssh-user/--ssh-pass.")
            return False
        
        self.deployer = Deployer(ssh_cfg, ssh_user, ssh_pass)
        
        success = True
        
        # 部署服务端
        if getattr(self.args, 'server_on', False):
            if not self.deployer.deploy_server("server"):
                success = False
        
        # 部署客户端 (上传)
        if self.args.upload:
            if not self.deployer.deploy(self.final_exe_path, str(self.version_json_path)):
                success = False
                
        return success
    
    def increment_version(self):
        """递增版本号"""
        if not self.args.upload or (self.args.upload and hasattr(self, '_deployment_successful') and self._deployment_successful):
            print("\n📝 Updating version for next build...")
            next_version = self.config.increment_version()
            self.config.save_config()
            print(f"✅ Next version: {next_version}")
    
    def cleanup(self):
        """清理构建目录"""
        print(f"\n🧹 Cleaning build directory...")
        if self.build_dir.exists():
            try:
                shutil.rmtree(self.build_dir)
                print(f"✅ Build directory cleaned: {self.build_dir}")
            except Exception as e:
                print(f"⚠️  Warning: Could not fully clean build directory: {e}")
    
    def print_summary(self, deployment_successful: bool):
        """
        打印构建总结
        
        Args:
            deployment_successful: 部署是否成功
        """
        overall_time = time.time() - self.start_time
        print("\n" + "="*80)
        if self.args.upload and not deployment_successful:
            print(" ⚠️  BUILD SUCCESSFUL, BUT DEPLOYMENT FAILED!")
        else:
            print(" ✅ ALL TASKS COMPLETED SUCCESSFULLY!")
        print("="*80)
        print(f"📊 Build Summary:")
        print(f"   Updater: {self.updater_build_time:.2f}s")
        print(f"   Main App: {self.main_build_time:.2f}s")
        print(f"   Total: {overall_time:.2f}s ({overall_time/60:.1f} minutes)")
        print(f"   Output: {self.final_dist_dir}")
        print("="*80)
    
    def run(self) -> int:
        """
        执行完整的构建流程
        
        Returns:
            int: 退出码（0表示成功）
        """
        self.print_header()
        
        # 检查是否为仅服务端部署模式
        if getattr(self.args, 'server_on', False) and not self.args.upload:
            print("\n🚀 Mode: Server Deployment Only")
            print("="*80)
            
            # 初始化以获取配置（不执行版本递增逻辑）
            # 注意：initialize_components 会调用 VersionManager 并可能尝试写文件
            # 但为了获取 SSH 配置，我们至少需要 self.config
            # 这里我们手动加载配置，跳过 initialize_components 中的版本更新逻辑
            try:
                # 获取 SSH 配置用于验证
                ssh_cfg = self.config.get_ssh_config()
                if not ssh_cfg:
                     print("❌ Failed to load SSH config")
                     return 1
            except Exception as e:
                print(f"❌ Configuration error: {e}")
                return 1

            # 直接执行部署
            if self.deploy():
                print("\n✅ Server deployment complete.")
                return 0
            else:
                return 1

        # 环境验证
        if not self.verify_environment():
            return 0 if self.args.verify_only else 1
        
        # 缓存设置
        self.setup_cache()
        
        # 打印配置
        self.print_configuration()
        
        # 初始化组件
        if not self.initialize_components():
            return 1
        
        # 构建更新器
        if not self.build_updater():
            return 1
        
        # 构建主应用
        if not self.build_main_application():
            return 1
        
        # 构建后处理
        if not self.post_build_processing():
            return 1
        
        # 部署
        deployment_successful = self.deploy()
        self._deployment_successful = deployment_successful
        
        # 版本递增
        self.increment_version()
        
        # 清理
        self.cleanup()
        
        # 总结
        self.print_summary(deployment_successful)
        
        return 0 if (not self.args.upload or deployment_successful) else 1
