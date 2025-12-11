"""
Version and release notes management.
"""

import os
import json
import subprocess
import urllib.request
from datetime import datetime
from src.utils.Crypto import calculate_sha256

class VersionManager:
    """Manages version information and release notes."""
    
    def __init__(self, version_string, git_hash=None, git_branch=None):
        self.version = version_string
        self.git_hash = git_hash or self._get_git_hash()
        self.git_branch = git_branch or self._get_git_branch()
    
    def _fetch_url(self, url):
        """Simple URL fetcher to avoid dependency on app logging."""
        try:
            with urllib.request.urlopen(url, timeout=10) as response:
                if response.status == 200:
                    return response.read().decode('utf-8')
        except Exception as e:
            print(f"   [Debug] Fetch failed: {e}")
        return None

    def _get_git_hash(self):
        """Get current Git commit hash."""
        try:
            return subprocess.check_output(
                ['git', 'rev-parse', '--short', 'HEAD'],
                stderr=subprocess.DEVNULL
            ).decode('ascii').strip()
        except:
            return "unknown"
    
    def _get_git_branch(self):
        """Get current Git branch name."""
        try:
            return subprocess.check_output(
                ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                stderr=subprocess.DEVNULL
            ).decode('ascii').strip()
        except:
            return "unknown"
    
    def generate_release_notes(self, version_url=None):
        """
        严格模式生成发布说明（仅本地仓库）：
        - 不再依赖远程 version.json
        - 使用本地 Git 标签确定范围：<last_tag>..HEAD
        - 若找不到任何标签，则报错并提示如何创建标签
        """
        print("\nINFO: Generating release notes from local Git...")
        
        # 1) 获取最近的标签
        try:
            last_tag = subprocess.check_output(
                ['git', 'describe', '--tags', '--abbrev=0'],
                stderr=subprocess.DEVNULL
            ).decode('utf-8').strip()
        except subprocess.CalledProcessError:
            raise RuntimeError(
                "本地仓库未找到任何 Git 标签，无法确定发布说明范围。请创建一个标签，例如：\n"
                "  git tag v0.5.31 && git push --tags\n"
                "然后重试构建。"
            )
        
        log_range = f"{last_tag}..HEAD"
        
        # 2) 生成提交信息
        try:
            print(f"INFO: Generating logs for range: '{log_range}'")
            commit_messages = subprocess.check_output(
                ['git', 'log', log_range, '--pretty=format:* %s'],
                stderr=subprocess.DEVNULL
            ).decode('utf-8').strip()
            
            if not commit_messages:
                raise RuntimeError("指定范围内无提交记录，无法生成发布说明。")
            
            print("OK: Successfully generated release notes.")
            return commit_messages
        except Exception as e:
            raise RuntimeError(f"生成发布说明失败: {e}")
    
    def create_version_json(self, exe_path, download_url, output_path, release_notes, channel: str = "stable"):
        """
        Create version.json file with build metadata using download-merge-save strategy.
        channel: 'dev' or 'stable'
        """
        try:
            exe_sha256 = calculate_sha256(exe_path)
            exe_size = os.path.getsize(exe_path)
            exe_size_mb = exe_size / (1024 * 1024)
            
            print(f"✅ SHA256: {exe_sha256}")
            print(f"✅ Size: {exe_size_mb:.2f} MB")
            
            # 1. 构造当前通道的数据
            current_build_data = {
                "version": self.version,
                "git_hash": self.git_hash,
                "git_branch": self.git_branch,
                "build_time": datetime.utcnow().isoformat() + "Z",
                "release_notes": release_notes,
                "download_url": download_url,
                "sha256": exe_sha256,
                "size_bytes": exe_size
            }
            
            # 2. 尝试获取线上现有的 version.json
            remote_url = "https://z.clash.ink/chfs/shared/MinecraftFRP/Data/version.json"
            print(f"🌍 Fetching existing version.json from {remote_url}...")
            
            final_data = {"channels": {}}
            try:
                existing_content = self._fetch_url(remote_url)
                if existing_content:
                    existing_json = json.loads(existing_content)
                    # 检查是否为新结构
                    if "channels" in existing_json:
                        final_data = existing_json
                    else:
                        print("⚠️  Remote version.json is old format. Migrating to new structure.")
                        final_data["legacy"] = existing_json
                else:
                    print("⚠️  Remote version.json not found or empty.")
            except Exception as e:
                print(f"⚠️  Could not fetch/parse remote version.json: {e}")
                print("   Creating new version.json structure.")

            # 3. 更新对应通道的数据
            if "channels" not in final_data:
                final_data["channels"] = {}
            
            final_data["channels"][channel] = current_build_data
            final_data["updated_at"] = datetime.utcnow().isoformat() + "Z"
            
            # 4. 保存到文件
            # 确保输出目录存在
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
                print(f"✅ Created directory: {output_dir}")
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(final_data, f, indent=4, ensure_ascii=False)
            
            print(f"✅ Generated version.json at {output_path}")
            print(f"   Channel '{channel}' updated.")
            return True
            
        except Exception as e:
            print(f"❌ ERROR: Failed to create version.json: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def update_version_file(self, version_string):
        """Update src/version.py with build information."""
        try:
            version_content = f'''"""
Application version information.
This file is auto-generated during build process.
"""

VERSION = "{version_string}"
GIT_HASH = "{self.git_hash}"
GIT_BRANCH = "{self.git_branch}"
BUILD_DATE = "{datetime.utcnow().isoformat()}Z"

def get_version_info():
    """Get formatted version information."""
    return {{
        "version": VERSION,
        "git_hash": GIT_HASH,
        "git_branch": GIT_BRANCH,
        "build_date": BUILD_DATE
    }}

def get_version_string():
    """Get version string for display."""
    return f"MinecraftFRP v{{VERSION}} ({{GIT_HASH}})"
'''
            with open("src/version.py", "w", encoding="utf-8") as f:
                f.write(version_content)
            print(f"✅ Updated src/version.py to {version_string} ({self.git_hash})")
            return True
        except Exception as e:
            print(f"❌ ERROR: Could not write to src/version.py: {e}")
            return False
