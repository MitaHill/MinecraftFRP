from datetime import datetime
import random
from src.utils.LogManager import get_logger

logger = get_logger()

class EasterEggs:
    """
    Logic layer for Easter Eggs / Special Events.
    Interacts with the GUI through an abstraction interface (window).
    """
    def __init__(self, interface):
        self.interface = interface

    def check_and_run(self):
        """Run all startup easter egg checks"""
        try:
            now = datetime.now()
            self._check_1226(now)
            self._check_new_year_2026(now)
            self._check_2026_welcome(now)
        except Exception as e:
            logger.error(f"Easter egg check failed: {e}")

    def _get_config(self):
        return getattr(self.interface, 'app_config', {})

    def _save_config(self):
        if hasattr(self.interface, '_save_app_config'):
            self.interface._save_app_config()

    def _check_1226(self, now):
        """Dec 26: Play EastRed-1226.mp3 once per day"""
        if now.month == 12 and now.day == 26:
            config = self._get_config()
            last_played = config.get("easter_egg", {}).get("1226_played_year", 0)
            
            if last_played != now.year:
                # self.interface.play_sound("EastRed-1226.mp3") # 暂时禁用声音播放，需要SoundManager
                
                # Save state
                if "easter_egg" not in config:
                    config["easter_egg"] = {}
                config["easter_egg"]["1226_played_year"] = now.year
                self._save_config()
        else:
            # Clean up config if not today
            config = self._get_config()
            if "easter_egg" in config and "1226_played_year" in config["easter_egg"]:
                del config["easter_egg"]["1226_played_year"]
                self._save_config()

    def _check_new_year_2026(self, now):
        """2026.1.1 00:00 - Fireworks & Goodbye 2025"""
        if now.year == 2026 and now.month == 1 and now.day == 1 and now.hour == 0 and now.minute == 0:
            # self.interface.play_sound("fireworks-sound.mp3")
            if hasattr(self.interface, 'show_toast'):
                self.interface.show_toast("再见2025年")

    def _check_2026_welcome(self, now):
        """2026.1.1 04:00 - 1.6 17:00: Welcome 2026 (Once)"""
        start = datetime(2026, 1, 1, 4, 0)
        end = datetime(2026, 1, 6, 17, 0)
        
        if start <= now <= end:
            config = self._get_config()
            played = config.get("easter_egg", {}).get("2026_welcome_shown", False)
            
            if not played:
                if hasattr(self.interface, 'show_toast'):
                    self.interface.show_toast("欢迎来到2026年")
                
                if "easter_egg" not in config:
                    config["easter_egg"] = {}
                config["easter_egg"]["2026_welcome_shown"] = True
                self._save_config()

    def check_64_log(self):
        """Check for June 4th random log"""
        now = datetime.now()
        if now.month == 6 and now.day == 4:
            if random.random() < 0.03: # 3% chance
                self.interface.log("REMEMBER IT", "red")
