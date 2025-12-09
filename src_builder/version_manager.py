"""
Version and release notes management.
"""

import os
import json
import subprocess
from datetime import datetime
from src.utils.Crypto import calculate_sha256
from src.utils.HttpManager import fetch_url_content

class VersionManager:
    """Manages version information and release notes."""
    
    def __init__(self, version_string, git_hash=None, git_branch=None):
        self.version = version_string
        self.git_hash = git_hash or self._get_git_hash()
        self.git_branch = git_branch or self._get_git_branch()
    
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
    
    def generate_release_notes(self, version_url):
        """
        Fetches commit messages from Git to generate release notes.
        Prioritizes fetching the git_hash from the live version.json.
        """
        print("\nINFO: Generating release notes from Git history...")
        log_range = None
        
        # Primary: Fetch from live version.json
        try:
            print(f"INFO: Attempting to fetch live version info from {version_url}")
            content = fetch_url_content(version_url, timeout=5)
            live_version_data = json.loads(content)
            server_git_hash = live_version_data.get("git_hash")
            
            if server_git_hash:
                print(f"OK: Found server git_hash: {server_git_hash}")
                log_range = f"{server_git_hash}..HEAD"
            else:
                print("WARNING: 'git_hash' not found in live version.json. Proceeding to fallback.")
                
        except Exception as e:
            print(f"WARNING: Could not fetch live version.json: {e}. Proceeding to fallback.")

        # Fallback 1: Use latest Git tag
        if not log_range:
            try:
                latest_tag = subprocess.check_output(
                    ['git', 'describe', '--tags', '--abbrev=0'],
                    stderr=subprocess.DEVNULL
                ).decode('ascii').strip()
                print(f"OK: Fallback - Found latest tag: {latest_tag}")
                log_range = f"{latest_tag}..HEAD"
            except subprocess.CalledProcessError:
                print("WARNING: Fallback - No Git tags found.")

        # Fallback 2: Use last 5 commits
        if not log_range:
            print("WARNING: Fallback - Using last 5 commits for release notes.")
            log_range = "HEAD~5..HEAD"

        # Generate commit messages
        try:
            print(f"INFO: Generating logs for range: '{log_range}'")
            commit_messages = subprocess.check_output(
                ['git', 'log', log_range, '--pretty=format:* %s'],
                stderr=subprocess.DEVNULL
            ).decode('utf-8').strip()
            
            if not commit_messages:
                print("WARNING: No new commits found. Using default message.")
                return "No new changes in this version."
                
            print("OK: Successfully generated release notes.")
            return commit_messages
            
        except Exception as e:
            print(f"ERROR: Failed to generate release notes: {e}")
            return "Failed to generate release notes."
    
    def create_version_json(self, exe_path, download_url, output_path, release_notes):
        """Create version.json file with build metadata."""
        try:
            exe_sha256 = calculate_sha256(exe_path)
            exe_size = os.path.getsize(exe_path)
            exe_size_mb = exe_size / (1024 * 1024)
            
            print(f"✅ SHA256: {exe_sha256}")
            print(f"✅ Size: {exe_size_mb:.2f} MB")
            
            version_data = {
                "version": self.version,
                "git_hash": self.git_hash,
                "git_branch": self.git_branch,
                "build_time": datetime.utcnow().isoformat() + "Z",
                "release_notes": release_notes,
                "download_url": download_url,
                "sha256": exe_sha256,
                "size_bytes": exe_size
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(version_data, f, indent=4, ensure_ascii=False)
            
            print(f"✅ Generated version.json at {output_path}")
            return True
            
        except Exception as e:
            print(f"❌ ERROR: Failed to create version.json: {e}")
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
