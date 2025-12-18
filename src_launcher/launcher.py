"""
MinecraftFRP Launcher (无界面、单文件)
职责：
1. 读取本地安装信息
2. 检查远程版本（支持 channel 字段：dev/stable）
3. 如需更新：将安装包下载到 Documents\MitaHillFRP\downloads，并写入配置指示下次启动时应用更新
4. 如无需更新：启动主程序
"""

import sys
import os
import json
import traceback
import requests
import subprocess
import hashlib
from pathlib import Path
import locale

# 配置（尽量避免硬编码，保留可替换点）
VERSION_JSON_URL = "https://z.clash.ink/chfs/shared/MinecraftFRP/Data/version.json"

# 路径配置
DOCUMENTS_PATH = Path.home() / "Documents" / "MitaHillFRP"
CONFIG_FILE = DOCUMENTS_PATH / "install_info.json"   # 安装器写入的安装信息与待处理的更新任务
DOWNLOADS_PATH = DOCUMENTS_PATH / "downloads"
LOGS_DIR = DOCUMENTS_PATH / "logs"
LOG_FILE = LOGS_DIR / "launcher.log"


def _safe_log(msg: str):
    try:
        print(msg)
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(str(msg) + "\n")
    except Exception:
        pass


def _show_toast(message: str, silent: bool = True):
    """显示 Windows 10/11 气泡通知（Toast Notification），静音模式"""
    try:
        # 使用 Windows Toast Notification (需要 win10toast-click 或系统原生API)
        # 为避免额外依赖，使用 PowerShell 调用系统通知
        import subprocess
        
        # PowerShell 脚本：显示 Toast（无声音）
        ps_script = f'''
        [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
        [Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null
        
        $template = @"
        <toast>
            <visual>
                <binding template="ToastText02">
                    <text id="1">MinecraftFRP 更新</text>
                    <text id="2">{message}</text>
                </binding>
            </visual>
            <audio silent="true"/>
        </toast>
"@
        
        $xml = New-Object Windows.Data.Xml.Dom.XmlDocument
        $xml.LoadXml($template)
        $toast = [Windows.UI.Notifications.ToastNotification]::new($xml)
        [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("MinecraftFRP").Show($toast)
        '''
        
        subprocess.run(
            ['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', ps_script],
            capture_output=True,
            timeout=2,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        )
    except Exception as e:
        # 降级方案：使用系统托盘气泡（需要GUI，launcher是无界面的，所以跳过）
        _safe_log(f"Toast notification failed: {e}")


def calculate_sha256(file_path: str) -> str:
    """计算文件的SHA256哈希值"""
    try:
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest().lower()
    except Exception as e:
        _safe_log(f"SHA256 calculation failed: {e}")
        return ""


def _load_install_info() -> dict:
    """
    加载安装信息JSON文件，增加编码容错。
    首先尝试UTF-8，如果失败，则回退到系统默认编码。
    """
    if not CONFIG_FILE.exists():
        return {}
    
    try:
        # 1. 尝试用 UTF-8 读取
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except UnicodeDecodeError as e_utf8:
        _safe_log(f"load_install_info with utf-8 failed: {e_utf8}. Retrying with system default encoding...")
        try:
            # 2. 回退到系统默认编码
            with open(CONFIG_FILE, 'r', encoding=None) as f:
                return json.load(f)
        except Exception as e_fallback:
            _safe_log(f"load_install_info with fallback encoding failed: {e_fallback}")
            return {}
    except Exception as e_general:
        _safe_log(f"load_install_info error: {e_general}")
        return {}


def _save_install_info(info: dict):
    try:
        DOCUMENTS_PATH.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(info, f, ensure_ascii=False, indent=2)
    except Exception as e:
        _safe_log(f"save_install_info error: {e}")


def _compare_version(v1: str, v2: str) -> int:
    try:
        parts1 = [int(x) for x in v1.split('.')]
        parts2 = [int(x) for x in v2.split('.')]
        for i in range(max(len(parts1), len(parts2))):
            p1 = parts1[i] if i < len(parts1) else 0
            p2 = parts2[i] if i < len(parts2) else 0
            if p1 > p2:
                return 1
            elif p1 < p2:
                return -1
        return 0
    except Exception:
        return 0


def _fetch_remote_version() -> dict:
    try:
        resp = requests.get(VERSION_JSON_URL, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        # 规范期望字段：version, installer_url, channel(dev|stable)
        return data
    except Exception as e:
        _safe_log(f"fetch remote version error: {e}")
        return {}


def _download_installer(url: str, version: str, channel: str) -> Path:
    """下载安装包，带进度提示（气泡通知，静音）"""
    try:
        DOWNLOADS_PATH.mkdir(parents=True, exist_ok=True)
        base_name = "MitaHill_FRP_Stable_Installer.exe" if channel == "stable" else "MitaHill_FRP_Dev_Install.exe"
        save_path = DOWNLOADS_PATH / f"{version}_{base_name}"
        if not url:
            _safe_log("remote version missing installer_url; skip update")
            return Path()
        
        # 开始下载前提示
        try:
            _show_toast(f"正在开始下载更新包 (v{version})，请稍候...", silent=True)
        except:
            pass

        # 开始下载
        with requests.get(url, stream=True, timeout=30) as r:
            r.raise_for_status()
            total_size = int(r.headers.get('content-length', 0))
            downloaded = 0
            last_reported = -1  # 上次报告的进度阈值
            
            import time
            start_time = time.time()
            
            with open(save_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # 计算进度百分比
                        if total_size > 0:
                            progress = int((downloaded / total_size) * 100)
                            
                            # 检查是否达到下一个报告点（20%, 40%, 60%, 80%, 100%）
                            report_threshold = (progress // 20) * 20
                            if report_threshold > last_reported and report_threshold > 0:
                                last_reported = report_threshold
                                
                                # 计算下载速度
                                elapsed = time.time() - start_time
                                speed_kbps = (downloaded / 1024 / elapsed) if elapsed > 0 else 0
                                
                                # 气泡通知（静音模式）
                                try:
                                    _show_toast(
                                        f"正在下载新版本。当前进度：{progress}%，当前速度：{speed_kbps:.1f}KB/s",
                                        silent=True
                                    )
                                    _safe_log(f"Download progress: {progress}% ({speed_kbps:.1f}KB/s)")
                                except Exception:
                                    pass
        
        # 下载完成气泡
        try:
            _show_toast("下载已完成。更新将在下一次联机工具启动时进行。", silent=True)
            _safe_log("Download completed successfully.")
        except Exception:
            pass
        
        return save_path
    except Exception as e:
        _safe_log(f"download installer error: {e}")
        return Path()


def _cleanup_old_installers():
    """清理下载目录中的旧安装包"""
    try:
        if not DOWNLOADS_PATH.exists():
            return
        
        # 获取所有安装包文件
        installers = list(DOWNLOADS_PATH.glob("*.exe"))
        
        if not installers:
            _safe_log("No old installers found.")
            return
        
        # 清理所有安装包
        cleaned_count = 0
        for installer in installers:
            try:
                installer.unlink()
                cleaned_count += 1
                _safe_log(f"Deleted old installer: {installer.name}")
            except Exception as e:
                _safe_log(f"Failed to delete {installer.name}: {e}")
        
        if cleaned_count > 0:
            _safe_log(f"Cleaned up {cleaned_count} old installer(s).")
            
            # 气泡提示
            try:
                _show_toast(f"已清理 {cleaned_count} 个旧版本安装包，释放磁盘空间。", silent=True)
            except Exception:
                pass
        
    except Exception as e:
        _safe_log(f"Cleanup old installers error: {e}")


def _apply_pending_update(info: dict) -> bool:
    """如配置中存在待处理更新任务，校验并执行安装包。静默模式：弹系统消息框提示。"""
    try:
        pending = info.get('pending_update', {})
        installer = pending.get('installer_path')
        version = pending.get('version')
        expected_sha256 = pending.get('sha256', '').lower()
        
        if installer and Path(installer).exists():
            # 校验 SHA256
            if expected_sha256:
                _safe_log(f"Verifying SHA256 for {installer}...")
                actual_sha256 = calculate_sha256(installer)
                if actual_sha256 != expected_sha256:
                    msg = f"更新包校验失败！\n期望: {expected_sha256}\n实际: {actual_sha256}\n文件可能已损坏，将自动删除。"
                    _safe_log(msg)
                    try:
                        import ctypes
                        ctypes.windll.user32.MessageBoxW(0, msg, "MinecraftFRP 更新错误", 16) # MB_ICONERROR=16
                    except:
                        pass
                    # 清理损坏文件和任务
                    try:
                        os.remove(installer)
                    except:
                        pass
                    info.pop('pending_update', None)
                    _save_install_info(info)
                    return False
                _safe_log("SHA256 verification passed.")
            else:
                _safe_log("Warning: No SHA256 provided for verification.")

            # 执行更新
            try:
                import ctypes
                msg = f"检测到待应用更新到版本 {version}，是否现在安装？(将弹出安装程序)"
                res = ctypes.windll.user32.MessageBoxW(0, msg, "MinecraftFRP 更新", 4)  # MB_YESNO=4
                if res == 6:  # IDYES
                    subprocess.Popen([installer])
                    # 清理任务，避免反复提示
                    info.pop('pending_update', None)
                    _save_install_info(info)
                    return True
            except Exception:
                # 如系统消息框失败，直接执行更新
                subprocess.Popen([installer])
                info.pop('pending_update', None)
                _save_install_info(info)
                return True
    except Exception as e:
        _safe_log(f"apply pending update error: {e}")
    return False


def _launch_main_app(info: dict) -> tuple[bool, int]:
    """
    启动主程序，并监控其初始状态。
    返回 (是否成功启动, 退出码)
    """
    app_path_str = info.get('app_path', '')
    app_path = Path(app_path_str) if app_path_str else None
    
    # 如果配置中的路径不存在，尝试推断
    if not app_path or not app_path.exists():
        install_path_str = info.get('install_path')
        if install_path_str:
            base_dir = Path(install_path_str)
            # 尝试新结构
            candidate1 = base_dir / 'MitaHill-FRP-APP' / 'MinecraftFRP.exe'
            # 尝试旧结构
            candidate2 = base_dir / 'MinecraftFRP.exe'
            
            if candidate1.exists():
                app_path = candidate1
            elif candidate2.exists():
                app_path = candidate2
                
    if not app_path or not app_path.exists():
        _safe_log(f"main app missing: {app_path}")
        return False, -1

    try:
        # 设置工作目录为可执行文件所在目录，避免路径问题
        cwd = app_path.parent
        # 添加启动参数 --launched-by-launcher 以便主程序验证
        process = subprocess.Popen([str(app_path), "--launched-by-launcher"], cwd=str(cwd))
        
        # 启动后监控几秒，检测是否发生“启动即崩”
        try:
            exit_code = process.wait(timeout=5)
            # 如果5秒内进程结束了，说明启动失败
            _safe_log(f"Main app exited prematurely with code: {exit_code} (Hex: {hex(exit_code)})")
            return False, exit_code
        except subprocess.TimeoutExpired:
            # 5秒后还在运行，说明启动成功
            _safe_log("Main app started successfully (running > 5s).")
            return True, 0
            
    except Exception as e:
        _safe_log(f"launch app error: {e}")
        return False, -1


def _show_fatal_error_dialog(exit_code: int):
    """根据退出码显示包含常见解决方案的致命错误对话框"""
    
    hex_code = hex(exit_code)
    # 将负数转为 Windows 风格的无符号十六进制
    if exit_code < 0:
        hex_code = hex(exit_code & 0xFFFFFFFF)

    code_info = f"退出码: {exit_code} ({hex_code})"
    specific_cause = ""

    # 智能诊断
    if exit_code in (-1073741819, -1073741515) or hex_code in ('0xc0000005', '0xc0000135'):
        specific_cause = (
            "智能诊断：检测到特定错误代码，这极有可能意味着您的系统缺少必要的【VC++ 运行库】。\n"
            "请优先尝试解决方案 2。\n"
        )

    msg = (
        f"MinecraftFRP 启动失败\n\n"
        f"{specific_cause}"
        f"启动器无法启动主程序。({code_info})\n"
        "这可能是由以下常见原因导致的：\n\n"
        "1. 杀毒软件拦截：请检查 Windows Defender 或其他杀毒软件的隔离区，将 MinecraftFRP.exe 和 frpc.exe 添加到信任列表。\n"
        "2. 缺少运行库：请尝试安装微软官方的 VC++ 运行库。\n"
        "3. 文件损坏：请尝试重新安装本工具。\n\n"
        "如果问题仍然存在，请携带 Documents\\MitaHillFRP\\logs 目录下的日志文件联系开发者。"
    )
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(0, msg, "MinecraftFRP 启动失败", 16) # MB_ICONERROR
    except:
        pass

def main():
    try:
        info = _load_install_info()
        current_version = info.get('version', '0.0.0')
        local_channel = info.get('channel', 'stable')
        _safe_log(f"Launcher started. Version: {current_version}, Channel: {local_channel}")

        # 1. 先处理待更新任务 (阻塞)
        if _apply_pending_update(info):
            return 0

        # 2. 立即启动主程序
        _safe_log("Launching main app...")
        app_launched, exit_code = _launch_main_app(info)
        
        if not app_launched:
            _safe_log(f"Failed to launch main app with exit code {exit_code}.")
            _show_fatal_error_dialog(exit_code)
            return 1

        # 3. 延迟500毫秒后再进行更新检查（避免阻塞主程序启动）
        import time
        time.sleep(0.5)
        
        # 4. 后台检查更新 (此时主程序已在运行)
        _safe_log("Checking for updates in background...")
        remote_data = _fetch_remote_version()
        
        # 解析新版结构
        target_info = {}
        target_channel = "stable"
        
        if "channels" in remote_data:
            channels = remote_data["channels"]
            stable_info = channels.get("stable", {})
            dev_info = channels.get("dev", {})
            
            if local_channel == "dev":
                v_stable = stable_info.get("version", "0.0.0")
                v_dev = dev_info.get("version", "0.0.0")
                
                if _compare_version(v_dev, v_stable) >= 0:
                    target_info = dev_info
                    target_channel = "dev"
                else:
                    target_info = stable_info
                    target_channel = "stable"
            else:
                target_info = stable_info
                target_channel = "stable"
        else:
            target_info = remote_data
            target_channel = remote_data.get("channel", "stable")

        remote_version = target_info.get('version', '0.0.0')
        installer_url = target_info.get('download_url')
        remote_sha256 = target_info.get('sha256', '')
        
        _safe_log(f"Remote version: {remote_version}, Channel: {target_channel} (Local: {local_channel})")

        # 5. 版本比较与处理
        version_comparison = _compare_version(remote_version, current_version)
        
        if version_comparison > 0:
            # 有新版本，后台下载
            if installer_url:
                _safe_log("Update found. Downloading in background...")
                installer_path = _download_installer(installer_url, remote_version, target_channel)
                
                if installer_path and installer_path.exists():
                    info = _load_install_info()
                    info['pending_update'] = {
                        'version': remote_version,
                        'installer_path': str(installer_path).replace('\\', '/'),
                        'channel': target_channel,
                        'sha256': remote_sha256,
                        'created_at': "2025-12-10T13:41:52.657Z",
                    }
                    _save_install_info(info)
                    _safe_log("Update downloaded and pending for next startup.")
                else:
                    _safe_log("Installer download failed")
            else:
                _safe_log("Remote version missing installer_url")
        elif version_comparison == 0:
            _safe_log("Already on latest version. Cleaning up old installers...")
            _cleanup_old_installers()
        else:
            _safe_log(f"Local version ({current_version}) is newer than remote ({remote_version}). Skipping update.")
        
        return 0
        
    except Exception:
        _safe_log("FATAL:\n" + traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main())
