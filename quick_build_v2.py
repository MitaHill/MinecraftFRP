#!/usr/bin/env python3
"""
Quick Build V2 Script
快速构建 V2 架构的启动脚本
"""
import sys
import subprocess

if __name__ == "__main__":
    print("=" * 80)
    print("🚀 Starting V2 Build (Inno Setup)")
    print("=" * 80)
    
    # 调用 build.py --v2
    result = subprocess.run(
        [sys.executable, "build.py", "--v2"],
        cwd="."
    )
    
    sys.exit(result.returncode)
