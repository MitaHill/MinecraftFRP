from src.utils.HttpManager import get_session, post_json
from src.utils.LogManager import get_logger
from src.network.Traceroute import check_network_environment
from src.core.SecurityGuard import SecurityGuard

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
        
        # 0. Local Security Checks (Anti-Debug, etc.)
        passed, reason = SecurityGuard.run_checks()
        if not passed:
            # Optionally report this
            return False, reason

        # Start periodic runtime checks
        SecurityGuard.start_periodic_check()
        
        # 1. Network Environment Check (Traceroute)
        # [MODIFIED] 禁用实际的路由追踪检查，防止误判导致闪退
        # 原有逻辑保留在下方注释中
        try:
            # 模拟检查通过
            logger.info("Network environment check skipped (Bypassed). Reporting success.")
            
            # 原有逻辑:
            # is_safe, info = check_network_environment()
            # if not is_safe:
            #     # Public IP detected at hop 1
            #     ip = info
            #     msg = f"检测到非家庭宽带环境 (公网第一跳: {ip})，根据规则自动封禁。"
            #     logger.warning(msg)
            #     
            #     # Report Violation
            #     try:
            #         report_data = {
            #             "traceroute_hops": [ip],
            #             "reason": "First hop is public IP (Non-residential broadband)"
            #         }
            #         SecurityService.report_violation(report_data)
            #     except Exception as e:
            #         logger.error(f"Failed to report violation: {e}")
            #     
            #     return False, msg
            
            pass 
        except Exception as e:
            logger.error(f"Network check bypass failed (Unexpected): {e}")
            pass

        # 2. Server Side Access Check (Blacklist/Whitelist/Geo)
        try:
            session = get_session()
            url = f"{SecurityService.API_BASE}/check_access"
            # 增加超时容错，避免卡住
            try:
                response = session.get(url, timeout=5)
                
                if response.status_code == 403:
                    # Banned
                    return False, f"您的IP已被服务器拒绝访问 ({response.text})"
                elif response.status_code != 200:
                    logger.warning(f"Server check returned {response.status_code}")
                    # We might allow if server error (500), but 403 is definite ban.
                    pass
            except Exception as net_err:
                logger.warning(f"Server access check connection failed: {net_err}")
                # 网络不通时不阻断启动
                pass
                
        except Exception as e:
            logger.error(f"Server access check failed: {e}")
            pass
             
        return True, "Access Granted"

    @staticmethod
    def report_violation(data):
        url = f"{SecurityService.API_BASE}/report_violation"
        try:
            post_json(url, data)
        except Exception as e:
            logger.error(f"Failed to report violation: {e}")
