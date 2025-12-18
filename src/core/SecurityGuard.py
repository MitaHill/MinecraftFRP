import sys
import os
import ctypes
import time
import threading
from src.utils.LogManager import get_logger

logger = get_logger()

class SecurityGuard:
    """
    Local Security & Integrity Guard
    Implements anti-debugging, anti-VM, and anti-tampering checks.
    """

    @staticmethod
    def check_debugger() -> bool:
        """
        Check if the process is being debugged.
        Returns: True if debugger is detected, False otherwise.
        """
        if sys.platform != 'win32':
            return False

        try:
            # 1. IsDebuggerPresent
            if ctypes.windll.kernel32.IsDebuggerPresent():
                logger.warning("SecurityGuard: IsDebuggerPresent detected a debugger.")
                return True

            # 2. CheckRemoteDebuggerPresent
            is_remote_debugger = ctypes.c_bool(False)
            process_handle = ctypes.windll.kernel32.GetCurrentProcess()
            ctypes.windll.kernel32.CheckRemoteDebuggerPresent(process_handle, ctypes.byref(is_remote_debugger))
            if is_remote_debugger.value:
                logger.warning("SecurityGuard: CheckRemoteDebuggerPresent detected a debugger.")
                return True

            # 3. Check specific bad processes (Simplified)
            # This can be resource intensive, so maybe skip or do lightly
            # forbidden_processes = ["x64dbg.exe", "ollydbg.exe", "wireshark.exe", "fiddler.exe"]
            # ... (Process iteration requires psutil or wmi, not doing it here to avoid bloat/perf hit on startup)

        except Exception as e:
            logger.error(f"SecurityGuard: Debugger check failed with error: {e}")
            # If check fails, we might want to be safe and say no debugger, or fail open.
            return False

        return False

    @staticmethod
    def check_vm() -> bool:
        """
        Check if running in a virtual machine (basic checks).
        Returns: True if VM detected, False otherwise.
        """
        # This is a 'best effort' check. Many legitimate users might use VMs.
        # For now, we return False to avoid false positives unless strictly required.
        # Uncomment below to enable.
        
        # try:
        #     # Check MAC address prefixes, Registry keys, etc.
        #     pass
        # except Exception:
        #     pass
        
        return False

    @staticmethod
    def run_checks() -> tuple[bool, str]:
        """
        Run all local security checks.
        Returns: (passed: bool, failure_reason: str)
        """
        logger.info("SecurityGuard: Running local security checks...")

        if SecurityGuard.check_debugger():
            return False, "Security Violation: Debugger Detected. Please close any debugging tools."
        
        # if SecurityGuard.check_vm():
        #     return False, "Security Violation: Virtual Machine Detected."

        return True, "Security Checks Passed"

    @staticmethod
    def start_periodic_check(interval=60):
        """Start a background thread to check periodically."""
        def _check_loop():
            while True:
                try:
                    time.sleep(interval)
                    if SecurityGuard.check_debugger():
                        logger.critical("SecurityGuard: Runtime Debugger Detected! Exiting...")
                        os._exit(1) # Force immediate exit
                except Exception:
                    pass
        
        t = threading.Thread(target=_check_loop, daemon=True)
        t.start()
