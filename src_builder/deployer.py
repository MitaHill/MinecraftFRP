"""
SSH deployment module for uploading build artifacts.
"""

import os
import sys

try:
    import paramiko
except ImportError:
    print("ERROR: Paramiko library not found. Please install it: pip install paramiko")
    sys.exit(1)

class Deployer:
    """Handles SSH deployment of build artifacts."""
    
    def __init__(self, ssh_config, username, password):
        self.host = ssh_config['host']
        self.port = ssh_config.get('port', 22)
        self.username = username
        self.password = password
        self.exe_remote_path = ssh_config['exe_path']
        self.version_remote_path = ssh_config['version_json_path']
    
    def deploy(self, local_exe_path, local_version_path):
        """Deploy artifacts to remote server via SSH/SFTP."""
        print("\n" + "-"*80)
        print("Starting deployment via SSH (Optimized)...")
        print(f"Connecting to {self.username}@{self.host}...")
        print("-"*80)
        
        try:
            with paramiko.SSHClient() as ssh:
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(
                    hostname=self.host,
                    username=self.username,
                    password=self.password,
                    port=self.port,
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
                        sys.stdout.write(
                            f"\rUploading: {sent/1024/1024:.2f}MB / "
                            f"{total/1024/1024:.2f}MB ({percent:.2f}%)"
                        )
                        sys.stdout.flush()
                    
                    # Upload executable
                    print(f"Uploading {os.path.basename(local_exe_path)} to {self.exe_remote_path}...")
                    sftp.put(local_exe_path, self.exe_remote_path, callback=progress_callback)
                    print("\nOK: Executable uploaded.")
                    
                    # Upload version.json
                    print(f"Uploading {os.path.basename(local_version_path)} to {self.version_remote_path}...")
                    sftp.put(local_version_path, self.version_remote_path)
                    print("OK: version.json uploaded.")
                
                print("\n" + "="*80)
                print(" DEPLOYMENT SUCCESSFUL!")
                print("="*80)
                return True
                
        except Exception as e:
            print(f"\n❌ ERROR: Deployment failed: {e}")
            return False

    def deploy_server(self, local_server_dir):
        """Deploy server directory to remote server."""
        remote_root = "/root/MitaHillFRP-Server"
        print("\n" + "-"*80)
        print("Starting SERVER deployment via SSH...")
        print(f"Connecting to {self.username}@{self.host}...")
        print("-"*80)
        
        try:
            with paramiko.SSHClient() as ssh:
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(
                    hostname=self.host,
                    username=self.username,
                    password=self.password,
                    port=self.port,
                    timeout=15
                )
                
                # 1. Stop the service
                print("Stopping 'mapi' service...")
                stdin, stdout, stderr = ssh.exec_command("systemctl stop mapi")
                exit_status = stdout.channel.recv_exit_status()
                if exit_status != 0:
                    err = stderr.read().decode().strip()
                    print(f"⚠️ Warning: Service stop returned code {exit_status}. ({err})")
                else:
                    print("OK: Service stopped.")

                with ssh.open_sftp() as sftp:
                    # Helper to recursively upload
                    def upload_dir(local_path, remote_path):
                        # Ensure remote dir exists
                        try:
                            sftp.stat(remote_path)
                        except IOError:
                            sftp.mkdir(remote_path)
                            print(f"Created remote dir: {remote_path}")
                        
                        for item in os.listdir(local_path):
                            if item in ["__pycache__", ".git", ".venv", ".idea"]:
                                continue
                                
                            l_item = os.path.join(local_path, item)
                            r_item = f"{remote_path}/{item}"
                            
                            if os.path.isdir(l_item):
                                upload_dir(l_item, r_item)
                            else:
                                print(f"Uploading {item}...")
                                sftp.put(l_item, r_item)

                    print(f"Uploading {local_server_dir} to {remote_root}...")
                    upload_dir(local_server_dir, remote_root)
                
                # 2. Install Dependencies
                print("Installing dependencies...")
                pip_cmd = "/root/MitaHillFRP-Server/.venv/bin/pip install -r /root/MitaHillFRP-Server/requirements.txt"
                stdin, stdout, stderr = ssh.exec_command(pip_cmd)
                exit_status = stdout.channel.recv_exit_status()
                if exit_status != 0:
                    err = stderr.read().decode().strip()
                    print(f"⚠️ Warning: Dependency installation failed with code {exit_status}. ({err})")
                else:
                    print("OK: Dependencies installed.")

                # 3. Start the service
                print("Starting 'mapi' service...")
                stdin, stdout, stderr = ssh.exec_command("systemctl start mapi")
                exit_status = stdout.channel.recv_exit_status()
                if exit_status != 0:
                    err = stderr.read().decode().strip()
                    print(f"❌ Error: Service start failed with code {exit_status}. ({err})")
                else:
                    print("OK: Service started.")
                
                print("\n" + "="*80)
                print(" SERVER DEPLOYMENT SUCCESSFUL!")
                print("="*80)
                return True
        except Exception as e:
            print(f"\n❌ ERROR: Server deployment failed: {e}")
            return False
