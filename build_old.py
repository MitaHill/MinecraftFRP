"""
MinecraftFRP Build & Deploy Script (Modular Version)
Uses modular build system from src_builder package.
"""

import sys
import argparse
import time
from pathlib import Path

from src_builder.config import BuildConfig
from src_builder.builder import NuitkaBuilder
from src_builder.deployer import Deployer
from src_builder.version_manager import VersionManager
from src_builder.utils import verify_dependencies, clean_cache

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="MinecraftFRP build & deploy script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python build.py --fast                    # Fast build without LTO
  python build.py --upload                  # Build and upload to server
  python build.py --fast --upload           # Fast build + upload
  python build.py --clean                   # Clean build cache before building
  python build.py --verify-only             # Only verify dependencies
  python build.py --skip-updater            # Skip updater rebuild
        """
    )
    parser.add_argument("--fast", action="store_true",
                        help="Enable fast build (no LTO optimization)")
    parser.add_argument("--upload", action="store_true",
                        help="Upload artifacts via SSH after build")
    parser.add_argument("--ssh-user", type=str,
                        help="SSH username (overrides cicd.yaml)")
    parser.add_argument("--ssh-pass", type=str,
                        help="SSH password (overrides cicd.yaml)")
    parser.add_argument("--clean", action="store_true",
                        help="Clean Nuitka cache before building")
    parser.add_argument("--verify-only", action="store_true",
                        help="Only verify dependencies and exit")
    parser.add_argument("--skip-updater", action="store_true",
                        help="Skip building updater (reuse existing)")
    return parser.parse_args()

def main():
    """Main build and deploy script logic."""
    overall_start = time.time()
    print("="*80)
    print(" 🚀 MinecraftFRP Build & Deploy Script (Modular)")
    print("="*80)
    
    # Load configuration
    config = BuildConfig()
    args = parse_args()
    
    # Verify dependencies
    if not verify_dependencies():
        sys.exit(1)
    
    if args.verify_only:
        print("\n✅ Verification complete. Exiting.")
        sys.exit(0)
    
    # Setup paths
    python_exe = sys.executable
    nuitka_config = config.get_nuitka_config()
    nuitka_cache_dir = Path(nuitka_config['output_dir']) / ".nuitka-cache"
    
    # Clean cache if requested
    if args.clean:
        clean_cache(str(nuitka_cache_dir))
    
    # Get SSH credentials
    ssh_cfg = config.get_ssh_config()
    ssh_user = args.ssh_user or ssh_cfg.get('user')
    ssh_pass = args.ssh_pass or ssh_cfg.get('password')
    
    # Display build configuration
    print(f"\n📦 Build Configuration:")
    print(f"   Fast Build: {'Yes (no LTO)' if args.fast else 'No (with LTO)'}")
    print(f"   Deploy: {'Yes' if args.upload else 'No'}")
    print(f"   Skip Updater: {'Yes' if args.skip_updater else 'No'}")
    print(f"\n✅ Python: {python_exe}")
    print(f"✅ Nuitka cache: {nuitka_cache_dir}")
    
    # Get version info
    current_version = config.get_version_string()
    version_manager = VersionManager(current_version)
    
    # Update version file
    if not version_manager.update_version_file(current_version):
        sys.exit(1)
    
    # Initialize builder
    builder = NuitkaBuilder(python_exe, str(nuitka_cache_dir), fast_build=args.fast)
    
    # Stage 1: Build Updater
    updater_build_dir = Path(nuitka_config['output_dir']) / "temp_updater"
    updater_exe_path, updater_time = builder.build_updater(
        str(updater_build_dir),
        skip=args.skip_updater
    )
    
    # Stage 2: Build Main Application
    main_app_build_dir = Path(nuitka_config['output_dir']) / f"MinecraftFRP_{current_version}"
    main_app_build_dir.mkdir(parents=True, exist_ok=True)
    
    final_exe_path, main_time = builder.build_main_app(
        current_version,
        str(main_app_build_dir),
        updater_exe_path
    )
    
    # Post-build processing
    print("\n" + "="*80)
    print("📋 Post-Build Processing")
    print("="*80)
    
    print(f"\n🔒 Calculating SHA256 and generating metadata...")
    print(f"✅ Git: {version_manager.git_branch}@{version_manager.git_hash}")
    
    # Generate release notes and version.json
    version_url = "https://z.clash.ink/chfs/shared/MinecraftFRP/Data/version.json"
    release_notes = version_manager.generate_release_notes(version_url)
    
    version_json_path = main_app_build_dir / "version.json"
    download_url = "https://z.clash.ink/chfs/shared/MinecraftFRP/lastet/MinecraftFRP.exe"
    
    if not version_manager.create_version_json(
        final_exe_path,
        download_url,
        str(version_json_path),
        release_notes
    ):
        sys.exit(1)
    
    # Deployment
    deployment_successful = False
    if args.upload:
        if not ssh_user or not ssh_pass:
            print("\n❌ ERROR: SSH credentials missing. Provide via cicd.yaml or --ssh-user/--ssh-pass.")
            deployment_successful = False
        else:
            deployer = Deployer(ssh_cfg, ssh_user, ssh_pass)
            deployment_successful = deployer.deploy(final_exe_path, str(version_json_path))
    else:
        print("\n⏭️  Skipping deployment (use --upload to deploy).")
    
    # Version increment
    if not args.upload or (args.upload and deployment_successful):
        print("\n📝 Updating version for next build...")
        next_version = config.increment_version()
        config.save_config()
        print(f"✅ Next version: {next_version}")
    
    # Final Summary
    overall_time = time.time() - overall_start
    print("\n" + "="*80)
    if args.upload and not deployment_successful:
        print(" ⚠️  BUILD SUCCESSFUL, BUT DEPLOYMENT FAILED!")
    else:
        print(" ✅ ALL TASKS COMPLETED SUCCESSFULLY!")
    print("="*80)
    print(f"📊 Build Summary:")
    print(f"   Updater: {updater_time:.2f}s")
    print(f"   Main App: {main_time:.2f}s")
    print(f"   Total: {overall_time:.2f}s ({overall_time/60:.1f} minutes)")
    print(f"   Output: {main_app_build_dir}")
    print("="*80)

if __name__ == "__main__":
    main()
