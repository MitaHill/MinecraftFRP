import os
import sys
import argparse
import subprocess
import yaml
import hashlib
import json
import getpass
import time
from pathlib import Path
from datetime import datetime
from src.utils.Crypto import calculate_sha256
from src.utils.HttpManager import fetch_url_content
try:
    import paramiko
except ImportError:
    print("ERROR: Paramiko library not found. Please install it using: pip install paramiko")
    sys.exit(1)

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

def get_release_notes_from_git(version_url):
    """
    Fetches commit messages from Git to generate release notes.
    It prioritizes fetching the git_hash from the live version.json.
    """
    print("\nINFO: Generating release notes from Git history...")
    log_range = None
    
    # --- Primary Strategy: Fetch from live version.json ---
    try:
        print(f"INFO: Attempting to fetch live version info from {version_url}")
        content = fetch_url_content(version_url, timeout=5)
        live_version_data = json.loads(content)
        server_git_hash = live_version_data.get("git_hash")
        
        if server_git_hash:
            print(f"OK: Found server git_hash: {server_git_hash}")
            log_range = f"{server_git_hash}..HEAD"
        else:
            print("WARNING: 'git_hash' not found in live version.json. Proceeding to fallback strategy.")
            
    except Exception as e:
        print(f"WARNING: Could not fetch or parse live version.json: {e}. Proceeding to fallback strategy.")

    # --- Fallback Strategy 1: Use latest Git tag ---
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

    # --- Fallback Strategy 2: Use last 5 commits ---
    if not log_range:
        print("WARNING: Fallback - Using last 5 commits for release notes.")
        log_range = "HEAD~5..HEAD"

    # --- Generate the commit messages ---
    try:
        print(f"INFO: Generating logs for range: '{log_range}'")
        commit_messages = subprocess.check_output(
            ['git', 'log', log_range, '--pretty=format:* %s'],
            stderr=subprocess.DEVNULL
        ).decode('utf-8').strip()
        
        if not commit_messages:
            print("WARNING: No new commits found in the specified range. Using a default message.")
            return "No new changes in this version."
            
        print("OK: Successfully generated release notes.")
        return commit_messages
        
    except Exception as e:
        print(f"ERROR: Failed to generate release notes from Git: {e}")
        return "Failed to generate release notes."

def upload_artifacts(ssh_config, user, password, local_exe_path, local_version_path):
    """Connects to SSH and uploads build artifacts with optimized parameters."""
    print("\n" + "-"*80)
    print("Starting deployment via SSH (Optimized)...")
    print(f"Connecting to {user}@{ssh_config['host']}...")
    print("-"*80)

    try:
        with paramiko.SSHClient() as ssh:
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(
                hostname=ssh_config['host'],
                username=user,
                password=password,
                port=ssh_config.get('port', 22),
                timeout=15
            )
            print("OK: SSH connection successful.")

            transport = ssh.get_transport()
            transport.window_size = 3 * 1024 * 1024
            transport.default_max_packet_size = 32768
            
            with ssh.open_sftp() as sftp:
                print("OK: SFTP session opened with optimized parameters.")
                def progress_callback(sent, total):
                    percent = 100.0 * sent / total
                    sys.stdout.write(f"\rUploading: {sent/1024/1024:.2f}MB / {total/1024/1024:.2f}MB ({percent:.2f}%)")
                    sys.stdout.flush()

                remote_exe_path = ssh_config['exe_path']
                print(f"Uploading {os.path.basename(local_exe_path)} to {remote_exe_path}...")
                sftp.put(local_exe_path, remote_exe_path, callback=progress_callback)
                print("\nOK: Executable uploaded.")

                remote_version_path = ssh_config['version_json_path']
                print(f"Uploading {os.path.basename(local_version_path)} to {remote_version_path}...")
                sftp.put(local_version_path, remote_version_path)
                print("OK: version.json uploaded.")

            print("\n" + "="*80); print(" DEPLOYMENT SUCCESSFUL!"); print("="*80)
            return True
    except Exception as e:
        print(f"\nERROR: An error occurred during deployment: {e}")
    return False

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

def run_nuitka_build(python_exe, script_path, output_dir, options, cache_dir):
    """Constructs and runs a Nuitka command with a specific cache directory."""
    command = [python_exe, "-m", "nuitka", script_path] + options + [f"--output-dir={output_dir}"]
    print("\n" + "-"*80)
    print(f"🔨 Building '{os.path.basename(script_path)}' (This may take several minutes)...")
    print("-"*80)
    rc, elapsed, _ = run_command(command, cache_dir=cache_dir)
    return rc, elapsed

def parse_args(config):
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
    print("="*80); print(" 🚀 MinecraftFRP Build & Deploy Script"); print("="*80)

    try:
        with open('cicd.yaml', 'r', encoding='utf-8') as f: config = yaml.safe_load(f)
        print("✅ Loaded cicd.yaml config.")
    except Exception as e:
        print(f"❌ ERROR: Could not load cicd.yaml: {e}"); sys.exit(1)

    args = parse_args(config)
    
    # Verify dependencies first
    if not verify_dependencies():
        sys.exit(1)
    
    if args.verify_only:
        print("\n✅ Verification complete. Exiting.")
        sys.exit(0)
    
    python_exe = sys.executable
    nuitka_cache_dir = os.path.join(config['nuitka']['output_dir'], ".nuitka-cache")

    # Clean cache if requested
    if args.clean:
        print(f"\n🧹 Cleaning Nuitka cache: {nuitka_cache_dir}")
        try:
            import shutil
            if os.path.exists(nuitka_cache_dir):
                shutil.rmtree(nuitka_cache_dir)
                print("✅ Cache cleaned successfully")
            else:
                print("ℹ️  Cache directory doesn't exist, nothing to clean")
        except Exception as e:
            print(f"⚠️  Warning: Could not clean cache: {e}")
    ssh_cfg = config.get('ssh', {})
    ssh_user = args.ssh_user or ssh_cfg.get('user')
    ssh_pass = args.ssh_pass or ssh_cfg.get('password')
    deploy_choice = 'y' if args.upload else 'n'
    fast_build_choice = 'y' if args.fast else 'n'
    
    print(f"\n📦 Build Configuration:")
    print(f"   Fast Build: {'Yes (no LTO)' if fast_build_choice == 'y' else 'No (with LTO)'}")
    print(f"   Deploy: {'Yes' if deploy_choice == 'y' else 'No'}")
    print(f"   Skip Updater: {'Yes' if args.skip_updater else 'No'}")
    
    python_exe = sys.executable
    nuitka_cache_dir = os.path.join(config['nuitka']['output_dir'], ".nuitka-cache")
    print(f"\n✅ Python: {python_exe}")
    print(f"✅ Nuitka cache: {nuitka_cache_dir}")

    # --- Common Nuitka options ---
    lto_option = ["--lto=no"] if fast_build_choice == 'y' else []

    # --- Stage 1: Build Updater ---
    if args.skip_updater:
        print("\n" + "="*80)
        print("⏭️  Stage 1/2: Skipping Updater (using existing)")
        print("="*80)
        updater_build_dir = os.path.join(config['nuitka']['output_dir'], "temp_updater")
        updater_exe_path = os.path.join(updater_build_dir, "updater.exe")
        if not os.path.exists(updater_exe_path):
            print(f"❌ ERROR: Updater not found at {updater_exe_path}")
            print("   Build without --skip-updater first.")
            sys.exit(1)
        print(f"✅ Using existing updater: {updater_exe_path}")
        updater_time = 0
    else:
        print("\n" + "="*80)
        print("📦 Stage 1/2: Building Updater")
        print("="*80)
        
        updater_build_dir = os.path.join(config['nuitka']['output_dir'], "temp_updater")
        updater_exe_path = os.path.join(updater_build_dir, "updater.exe")
        updater_options = [
            "--onefile", 
            "--windows-disable-console", 
            "--output-filename=updater.exe",
            "--plugin-enable=pyside6",
            "--show-progress",
            "--show-scons",
            "--assume-yes-for-downloads",
            "--jobs=20"
        ] + lto_option
        
        rc, updater_time = run_nuitka_build(python_exe, "src_updater/main.py", updater_build_dir, updater_options, nuitka_cache_dir)
        if rc != 0:
            print("\n" + "="*80); print(" ❌ BUILD FAILED: Updater compilation failed."); print("="*80); sys.exit(1)
        print(f"\n✅ Updater built successfully in {updater_time:.2f}s")
        print(f"   Location: {updater_exe_path}")

    # --- Stage 2: Build Main Application ---
    print("\n" + "="*80)
    print("📦 Stage 2/2: Building Main Application")
    print("="*80)
    
    ver_info = config['version']
    major, minor, patch = ver_info['major'], ver_info['minor'], ver_info['patch']
    current_version = f"{major}.{minor}.{patch}"
    print(f"\n📌 Version: {current_version}")

    try:
        with open("src/_version.py", "w", encoding="utf-8") as f:
            f.write(f'__version__ = "{current_version}"\n')
        print(f"✅ Updated src/_version.py")
    except Exception as e:
        print(f"❌ ERROR: Could not write to src/_version.py: {e}"); sys.exit(1)

    main_app_build_dir = os.path.join(config['nuitka']['output_dir'], f"MinecraftFRP_{current_version}")
    final_exe_name = "MinecraftFRP.exe"
    final_exe_path = os.path.join(main_app_build_dir, final_exe_name)
    main_app_options = [
        "--onefile", "--windows-disable-console", "--plugin-enable=pyside6",
        "--windows-icon-from-ico=base\\logo.ico", f"--output-filename={final_exe_name}",
        "--include-data-file=base\\frpc.exe=base\\frpc.exe",
        "--include-data-file=base\\new-frpc.exe=base\\new-frpc.exe",
        "--include-data-file=base\\tracert_gui.exe=base\\tracert_gui.exe",
        "--include-data-file=base\\logo.ico=base\\logo.ico",
        "--include-data-file=config/special_nodes.json=config/special_nodes.json",
        f"--include-data-file={updater_exe_path}=updater.exe",
        "--assume-yes-for-downloads",
        "--show-progress",
        "--show-scons",
        "--jobs=20"
    ] + lto_option
    
    rc, main_time = run_nuitka_build(python_exe, "app.py", main_app_build_dir, main_app_options, nuitka_cache_dir)
    if rc != 0:
        print("\n" + "="*80); print(" ❌ BUILD FAILED: Main application compilation failed."); print("="*80); sys.exit(1)
    print(f"\n✅ Main application built successfully in {main_time:.2f}s")
    print(f"   Location: {final_exe_path}")

    # --- Post-build processing ---
    print("\n" + "="*80)
    print("📋 Post-Build Processing")
    print("="*80)
    
    try:
        print("\n🔒 Calculating SHA256 checksum...")
        exe_sha256 = calculate_sha256(final_exe_path)
        exe_size_mb = os.path.getsize(final_exe_path) / (1024 * 1024)
        print(f"✅ SHA256: {exe_sha256}")
        print(f"✅ Size: {exe_size_mb:.2f} MB")
    except Exception as e:
        print(f"❌ ERROR: Failed during post-build processing: {e}"); sys.exit(1)

    try:
        git_hash = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'], stderr=subprocess.DEVNULL).decode('ascii').strip()
        git_branch = subprocess.check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], stderr=subprocess.DEVNULL).decode('ascii').strip()
        print(f"✅ Git: {git_branch}@{git_hash}")
    except Exception: 
        git_hash = "unknown"
        git_branch = "unknown"
    
    version_url = "https://z.clash.ink/chfs/shared/MinecraftFRP/Data/version.json"
    release_notes = get_release_notes_from_git(version_url)
    
    version_data = {
        "version": current_version, 
        "git_hash": git_hash,
        "git_branch": git_branch,
        "build_time": datetime.utcnow().isoformat() + "Z",
        "release_notes": release_notes,
        "download_url": "https://z.clash.ink/chfs/shared/MinecraftFRP/lastet/MinecraftFRP.exe",
        "sha256": exe_sha256,
        "size_bytes": os.path.getsize(final_exe_path)
    }
    version_json_path = os.path.join(main_app_build_dir, "version.json")
    with open(version_json_path, 'w', encoding='utf-8') as f: 
        json.dump(version_data, f, indent=4, ensure_ascii=False)
    print(f"✅ Generated version.json")
    
    # --- Deployment ---
    deployment_successful = False
    if deploy_choice == 'y':
        if not ssh_user or not ssh_pass:
            print("\n❌ ERROR: SSH credentials missing. Provide via cicd.yaml or --ssh-user/--ssh-pass.")
            deployment_successful = False
        else:
            deployment_successful = upload_artifacts(config['ssh'], ssh_user, ssh_pass, final_exe_path, version_json_path)
    else:
        print("\n⏭️  Skipping deployment (use --upload to deploy).")

    # --- Version increment ---
    if deploy_choice != 'y' or (deploy_choice == 'y' and deployment_successful):
        print("\n📝 Updating version for next build...")
        config['version']['patch'] += 1
        if config['version']['patch'] > 99:
            config['version']['patch'] = 0
            config['version']['minor'] += 1
        with open('cicd.yaml', 'w', encoding='utf-8') as f: 
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
        next_ver = f"{config['version']['major']}.{config['version']['minor']}.{config['version']['patch']}"
        print(f"✅ Next version: {next_ver}")

    # --- Final Summary ---
    overall_time = time.time() - overall_start
    print("\n" + "="*80)
    if deploy_choice == 'y' and not deployment_successful:
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
