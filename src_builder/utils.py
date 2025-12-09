"""
Utility functions for build system.
"""

import os
import sys
import subprocess
import time

def run_command(command, cwd=None, cache_dir=None, verbose=True):
    """Runs a command with a specific environment and prints its output."""
    if verbose:
        print(f"Executing: {' '.join(command)}\n")
    
    my_env = os.environ.copy()
    if cache_dir:
        my_env["NUITKA_CACHE_DIR"] = cache_dir
        if verbose:
            print(f"INFO: Using Nuitka cache directory: {cache_dir}")

    start_time = time.time()
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding='utf-8',
        errors='replace',
        cwd=cwd,
        env=my_env
    )
    
    output_lines = []
    while True:
        output = process.stdout.readline()
        if output == '' and process.poll() is not None:
            break
        if output:
            output_lines.append(output.strip())
            if verbose:
                print(output.strip(), flush=True)
    
    rc = process.poll()
    elapsed = time.time() - start_time
    
    if verbose:
        print(f"\n⏱️  Command completed in {elapsed:.2f}s with exit code {rc}")
    
    return rc, elapsed, output_lines

def verify_dependencies():
    """Verify required dependencies and files exist."""
    print("\n📋 Verifying dependencies...")
    
    required_files = [
        "base/frpc.exe",
        "base/new-frpc.exe", 
        "base/tracert_gui.exe",
        "base/logo.ico",
        "config/special_nodes.json",
        "src_updater/main.py",
        "app.py"
    ]
    
    missing = []
    for file in required_files:
        if not os.path.exists(file):
            missing.append(file)
            print(f"   ❌ Missing: {file}")
        else:
            print(f"   ✅ Found: {file}")
    
    if missing:
        print(f"\n❌ ERROR: {len(missing)} required file(s) missing!")
        return False
    
    print("✅ All dependencies verified.\n")
    return True

def clean_cache(cache_dir):
    """Clean Nuitka cache directory."""
    print(f"\n🧹 Cleaning Nuitka cache: {cache_dir}")
    try:
        import shutil
        if os.path.exists(cache_dir):
            shutil.rmtree(cache_dir)
            print("✅ Cache cleaned successfully")
        else:
            print("ℹ️  Cache directory doesn't exist, nothing to clean")
        return True
    except Exception as e:
        print(f"⚠️  Warning: Could not clean cache: {e}")
        return False
