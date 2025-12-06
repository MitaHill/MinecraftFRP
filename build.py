import os
import sys
import subprocess
import yaml
import hashlib
import json
import getpass
from src.utils.Crypto import calculate_sha256
try:
    import paramiko
except ImportError:
    print("ERROR: Paramiko library not found. Please install it using: pip install paramiko")
    sys.exit(1)

def run_command(command, cwd=None, cache_dir=None):
    """Runs a command with a specific environment and prints its output."""
    print(f"Executing: {' '.join(command)}\n")
    
    my_env = os.environ.copy()
    if cache_dir:
        my_env["NUITKA_CACHE_DIR"] = cache_dir
        print(f"INFO: Using Nuitka cache directory: {cache_dir}")

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
    while True:
        output = process.stdout.readline()
        if output == '' and process.poll() is not None:
            break
        if output:
            print(output.strip(), flush=True)
    rc = process.poll()
    return rc

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

def run_nuitka_build(python_exe, script_path, output_dir, options, cache_dir):
    """Constructs and runs a Nuitka command with a specific cache directory."""
    command = [python_exe, "-m", "nuitka", script_path] + options + [f"--output-dir={output_dir}"]
    print("\n" + "-"*80)
    print(f"Running Nuitka for '{os.path.basename(script_path)}' (This may take several minutes)...")
    print("-"*80)
    return run_command(command, cache_dir=cache_dir)

def main():
    """Main build and deploy script logic."""
    print("="*80); print(" MinecraftFRP Build & Deploy Script"); print("="*80)

    try:
        with open('cicd.yaml', 'r', encoding='utf-8') as f: config = yaml.safe_load(f)
        print("OK: Loaded cicd.yaml config.")
    except Exception as e:
        print(f"ERROR: Could not load cicd.yaml: {e}"); sys.exit(1)

    ssh_user, ssh_pass, deploy_choice = None, None, 'n'
    fast_build_choice = input("Enable fast build mode (faster compile, slower exe)? (y/n): ").lower().strip()
    deploy_choice = input("Will this run include deployment to SSH server? (y/n): ").lower().strip()
    if deploy_choice == 'y':
        default_user = config.get('ssh', {}).get('user', '')
        ssh_user = input(f"Enter SSH username [{default_user}]: ").strip() or default_user
        print("\n" + "!"*80); print("! WARNING: Your password will be displayed on screen..."); print("!"*80)
        ssh_pass = input("Enter SSH password: ")
    
    print("\nStarting build process...")
    python_exe = sys.executable
    nuitka_cache_dir = os.path.join(config['nuitka']['output_dir'], ".nuitka-cache")
    print(f"OK: Nuitka cache directory set to: {nuitka_cache_dir}")

    # --- Common Nuitka options ---
    lto_option = ["--lto=no"] if fast_build_choice == 'y' else []
    if lto_option:
        print("\nINFO: Fast build mode enabled. Executable will be less optimized.")

    # --- Stage 1: Build Updater ---
    updater_build_dir = os.path.join(config['nuitka']['output_dir'], "temp_updater")
    updater_exe_path = os.path.join(updater_build_dir, "updater.exe")
    updater_options = [
        "--onefile", 
        "--windows-console-mode=force", 
        "--output-filename=updater.exe",
        "--enable-plugin=tk-inter",
        "--show-progress",
        "--show-scons",
        "--assume-yes-for-downloads"
    ] + lto_option
    if run_nuitka_build(python_exe, "src/tools/updater.py", updater_build_dir, updater_options, nuitka_cache_dir) != 0:
        print("\n" + "="*80); print(" BUILD FAILED: Updater compilation failed."); print("="*80); sys.exit(1)
    print(f"\nOK: Updater built successfully at {updater_exe_path}")

    # --- Stage 2: Build Main Application ---
    ver_info = config['version']
    major, minor, patch = ver_info['major'], ver_info['minor'], ver_info['patch']
    current_version = f"{major}.{minor}.{patch}"
    print(f"\nOK: Building main application version: {current_version}")

    try:
        with open("src/_version.py", "w", encoding="utf-8") as f:
            f.write(f'__version__ = "{current_version}"\n')
        print(f"OK: Wrote version {current_version} to src/_version.py")
    except Exception as e:
        print(f"ERROR: Could not write to src/_version.py: {e}"); sys.exit(1)

    main_app_build_dir = os.path.join(config['nuitka']['output_dir'], f"MinecraftFRP_{current_version}")
    final_exe_name = "MinecraftFRP.exe"
    final_exe_path = os.path.join(main_app_build_dir, final_exe_name)
    main_app_options = [
        "--onefile", "--windows-disable-console", "--plugin-enable=pyside6",
        "--windows-icon-from-ico=logo.ico", f"--output-filename={final_exe_name}",
        "--include-data-file=frpc.exe=frpc.exe",
        "--include-data-file=tracert_gui.exe=tracert_gui.exe",
        "--include-data-file=logo.ico=logo.ico",
        f"--include-data-file={updater_exe_path}=updater.exe",
        "--assume-yes-for-downloads",
        "--show-progress",
        "--show-scons"
    ] + lto_option
    if run_nuitka_build(python_exe, "app.py", main_app_build_dir, main_app_options, nuitka_cache_dir) != 0:
        print("\n" + "="*80); print(" BUILD FAILED: Main application compilation failed."); print("="*80); sys.exit(1)
    print("\nOK: Main application built successfully.")

    try:
        print("\nOK: Calculating SHA256 checksum...")
        exe_sha256 = calculate_sha256(final_exe_path)
        print(f"OK: SHA256 is {exe_sha256}")
    except Exception as e:
        print(f"ERROR: Failed during post-build processing: {e}"); sys.exit(1)

    try:
        git_hash = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD']).decode('ascii').strip()
    except Exception: git_hash = "unknown"
    version_data = {
        "version": current_version, "git_hash": git_hash, "release_notes": "Automated build.",
        "download_url": "https://z.clash.ink/chfs/shared/MinecraftFRP/lastet/MinecraftFRP.exe", "sha256": exe_sha256
    }
    version_json_path = os.path.join(main_app_build_dir, "version.json")
    with open(version_json_path, 'w', encoding='utf-8') as f: json.dump(version_data, f, indent=4)
    print(f"OK: Generated version.json at {version_json_path}")
    
    deployment_successful = False
    if deploy_choice == 'y':
        deployment_successful = upload_artifacts(config['ssh'], ssh_user, ssh_pass, final_exe_path, version_json_path)
    else:
        print("\nSkipping deployment.")

    if deploy_choice != 'y' or (deploy_choice == 'y' and deployment_successful):
        print("\nOK: Updating version for next build...")
        config['version']['patch'] += 1
        if config['version']['patch'] > 99:
            config['version']['patch'] = 0
            config['version']['minor'] += 1
        with open('cicd.yaml', 'w', encoding='utf-8') as f: yaml.dump(config, f)
        print(f"OK: Updated cicd.yaml for next version: {config['version']['major']}.{config['version']['minor']}.{config['version']['patch']}")

    print("\n" + "="*80)
    if deploy_choice == 'y' and not deployment_successful:
        print(" BUILD SUCCESSFUL, BUT DEPLOYMENT FAILED!")
    else:
        print(" ALL TASKS COMPLETED SUCCESSFULLY!")
    print(f"Generated artifacts in: {main_app_build_dir}")
    print("="*80)

if __name__ == "__main__":
    main()
