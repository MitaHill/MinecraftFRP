"""
Nuitka builder module for compiling Python applications.
"""

import os
import sys
from .utils import run_command

class NuitkaBuilder:
    """Handles Nuitka compilation of Python applications."""
    
    def __init__(self, python_exe, cache_dir, fast_build=False):
        self.python_exe = python_exe
        self.cache_dir = cache_dir
        self.fast_build = fast_build
        self.lto_option = ["--lto=no"] if fast_build else []
    
    def build_updater(self, output_dir, skip=False):
        """Build the updater executable."""
        updater_exe_path = os.path.join(output_dir, "updater.exe")
        
        if skip:
            print("\n" + "="*80)
            print("⏭️  Stage 1/2: Skipping Updater (using existing)")
            print("="*80)
            if not os.path.exists(updater_exe_path):
                print(f"❌ ERROR: Updater not found at {updater_exe_path}")
                print("   Build without --skip-updater first.")
                sys.exit(1)
            print(f"✅ Using existing updater: {updater_exe_path}")
            return updater_exe_path, 0
        
        print("\n" + "="*80)
        print("📦 Stage 1/2: Building Updater")
        print("="*80)
        
        options = [
            "--onefile", 
            "--windows-disable-console", 
            "--output-filename=updater.exe",
            "--plugin-enable=pyside6",
            "--show-progress",
            "--show-scons",
            "--assume-yes-for-downloads",
            "--jobs=20"
        ] + self.lto_option
        
        rc, elapsed = self._run_build("src_updater/main.py", output_dir, options)
        
        if rc != 0:
            print("\n" + "="*80)
            print(" ❌ BUILD FAILED: Updater compilation failed.")
            print("="*80)
            sys.exit(1)
        
        print(f"\n✅ Updater built successfully in {elapsed:.2f}s")
        print(f"   Location: {updater_exe_path}")
        
        return updater_exe_path, elapsed
    
    def build_main_app(self, version, output_dir, updater_path):
        """Build the main application executable."""
        print("\n" + "="*80)
        print("📦 Stage 2/2: Building Main Application")
        print("="*80)
        print(f"\n📌 Version: {version}")
        
        final_exe_name = "MinecraftFRP.exe"
        final_exe_path = os.path.join(output_dir, final_exe_name)
        
        options = [
            "--onefile",
            "--windows-disable-console",
            "--plugin-enable=pyside6",
            "--windows-icon-from-ico=base\\logo.ico",
            f"--output-filename={final_exe_name}",
            "--include-data-file=base\\frpc.exe=base\\frpc.exe",
            "--include-data-file=base\\new-frpc.exe=base\\new-frpc.exe",
            "--include-data-file=base\\tracert_gui.exe=base\\tracert_gui.exe",
            "--include-data-file=base\\logo.ico=base\\logo.ico",
            "--include-data-file=config/special_nodes.json=config/special_nodes.json",
            f"--include-data-file={updater_path}=updater.exe",
            "--assume-yes-for-downloads",
            "--show-progress",
            "--show-scons",
            "--jobs=20"
        ] + self.lto_option
        
        rc, elapsed = self._run_build("app.py", output_dir, options)
        
        if rc != 0:
            print("\n" + "="*80)
            print(" ❌ BUILD FAILED: Main application compilation failed.")
            print("="*80)
            sys.exit(1)
        
        print(f"\n✅ Main application built successfully in {elapsed:.2f}s")
        print(f"   Location: {final_exe_path}")
        
        return final_exe_path, elapsed
    
    def _run_build(self, script_path, output_dir, options):
        """Execute Nuitka build command."""
        command = [
            self.python_exe,
            "-m",
            "nuitka",
            script_path
        ] + options + [f"--output-dir={output_dir}"]
        
        print("\n" + "-"*80)
        print(f"🔨 Building '{os.path.basename(script_path)}' (This may take several minutes)...")
        print("-"*80)
        
        rc, elapsed, _ = run_command(command, cache_dir=self.cache_dir)
        return rc, elapsed
