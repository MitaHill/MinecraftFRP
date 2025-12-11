import subprocess
import re
import ipaddress
import platform
import logging

logger = logging.getLogger(__name__)

def is_private_ip(ip_str: str) -> bool:
    try:
        ip = ipaddress.ip_address(ip_str)
        # Check standard private ranges
        if ip.is_private:
            return True
        # Check CGNAT (100.64.0.0/10) - strictly speaking not "private" in ipaddress module < 3.9.5? 
        # Actually ipaddress.is_private includes 100.64.0.0/10 in newer python versions?
        # Let's check manually to be safe.
        # 100.64.0.0/10 => 100.64.0.0 - 100.127.255.255
        if isinstance(ip, ipaddress.IPv4Address):
            # 100.64.0.0 = 1681915904
            # 100.127.255.255 = 1686110207
            ip_int = int(ip)
            if 1681915904 <= ip_int <= 1686110207:
                return True
        return False
    except ValueError:
        return False

def get_first_hop_ip() -> str:
    """
    Executes traceroute to a public target (max 1 hop) and returns the IP of the first hop.
    Returns None if failed.
    """
    # Use a solid IPv4 address for Baidu to enforce IPv4 path
    # 110.242.68.3 is one of the IPs for www.baidu.com
    target = "110.242.68.3" 
    try:
        if platform.system().lower() == "windows":
            # -d: no dns, -h 1: max 1 hop, -w 2000: timeout 2s per hop
            cmd = ["tracert", "-d", "-h", "1", "-w", "2000", target]
            # Use default system encoding (likely cp936 on CN Windows), rely on Python's auto-detection
            encoding = None 
        else:
            # Linux/Mac
            cmd = ["traceroute", "-n", "-m", "1", "-w", "2", target]
            encoding = "utf-8"

        # Create subprocess, hide window on Windows
        startupinfo = None
        if platform.system().lower() == "windows":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE

        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            startupinfo=startupinfo,
            text=True,
            encoding=encoding,
            errors='replace' # More robust than ignore
        )
        try:
            # Increase total timeout to 60s to be safe, though 1 hop should be fast
            stdout, _ = process.communicate(timeout=60)
        except subprocess.TimeoutExpired:
            try:
                process.kill()
            except Exception:
                pass
            logger.warning("Traceroute command timed out.")
            return None
        except Exception as e:
            logger.error(f"Traceroute communication error: {e}")
            try:
                process.kill()
            except Exception:
                pass
            return None
            
        # Parse output
        # Windows: "  1    <1 ms    <1 ms    <1 ms  192.168.1.1"
        # Linux: " 1  192.168.1.1  0.123 ms"
        
        for line in stdout.splitlines():
            line = line.strip()
            if line.startswith("1") or line.startswith("1 "):
                # Extract IP
                # Simple regex for IPv4
                match = re.search(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', line)
                if match:
                    return match.group(1)
                    
        return None
        
    except Exception as e:
        logger.error(f"Traceroute failed: {e}")
        return None

def check_network_environment() -> tuple[bool, str]:
    """
    Checks if the network environment is "Residential" (First hop is private).
    Returns (is_safe, message_or_ip)
    """
    target = "110.242.68.3"
    ip = get_first_hop_ip()
    
    if not ip:
        # If traceroute fails (e.g. offline), we assume safe or skip check
        return True, "Traceroute failed"
        
    # Special Case: Proxy/VPN Interception
    if ip == target:
        # If the first hop IS the target, traffic is likely being intercepted by a local proxy (TUN mode)
        # We cannot determine the real physical network environment.
        # Decision: Allow it (Assume it's a player using VPN), but maybe log a warning.
        logger.info(f"Traceroute returned target IP {ip} as first hop. Proxy/VPN detected.")
        return True, f"Proxy/VPN Detected ({ip})"
        
    if is_private_ip(ip):
        return True, ip
    else:
        return False, ip
