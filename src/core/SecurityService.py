from src.utils.HttpManager import get_session, post_json
from src.utils.LogManager import get_logger
from src.network.Traceroute import check_network_environment

logger = get_logger()

class SecurityService:
    API_BASE = "https://mapi.clash.ink/api"
    
    @staticmethod
    def perform_startup_check() -> tuple[bool, str]:
        """
        Perform all security checks on startup.
        Returns: (passed: bool, failure_reason: str)
        """
        logger.info("Performing startup security checks...")
        
        # 1. Network Environment Check (Traceroute)
        try:
            is_safe, info = check_network_environment()
            if not is_safe:
                # Public IP detected at hop 1
                ip = info
                msg = f"检测到非家庭宽带环境 (公网第一跳: {ip})，根据规则自动封禁。"
                logger.warning(msg)
                
                # Report Violation
                try:
                    report_data = {
                        "traceroute_hops": [ip],
                        "reason": "First hop is public IP (Non-residential broadband)"
                    }
                    SecurityService.report_violation(report_data)
                except Exception as e:
                    logger.error(f"Failed to report violation: {e}")
                
                return False, msg
        except Exception as e:
            logger.error(f"Network check failed: {e}")
            # Fail safe? Or Fail closed? User wants bans.
            # But if traceroute fails (e.g. no permissions or firewall), maybe warn only?
            # User requirement is strong: "Start traceroute... report and ban".
            # If we can't traceroute, we assume safe for now to avoid false positives on restricted systems.
            pass

        # 2. Server Side Access Check (Blacklist/Whitelist/Geo)
        try:
            session = get_session()
            url = f"{SecurityService.API_BASE}/check_access"
            response = session.get(url, timeout=5)
            
            if response.status_code == 403:
                # Banned
                return False, f"您的IP已被服务器拒绝访问 ({response.text})"
            elif response.status_code != 200:
                logger.warning(f"Server check returned {response.status_code}")
                # We might allow if server error (500), but 403 is definite ban.
                pass
                
        except Exception as e:
            logger.error(f"Server access check failed: {e}")
            # Connection error. We generally allow offline use if it's a tool, 
            # but this is a "Lobby" tool. Without server it might be useless?
            # But core function is FRP. If server is down, can we still use it?
            # Probably yes. So we don't block on connection error, only on explicit 403.
            pass
             
        return True, "Access Granted"

    @staticmethod
    def report_violation(data):
        url = f"{SecurityService.API_BASE}/report_violation"
        try:
            post_json(url, data)
        except Exception as e:
            logger.error(f"Failed to report violation: {e}")
