import json
from src.utils.HttpManager import fetch_url_content
import threading
from pathlib import Path
from src.utils.LogManager import get_logger

logger = get_logger()

class AdManager:
    def __init__(self):
        self.ads = []
        self.current_ad_index = 0
        
        # 确保config目录存在
        self.config_dir = Path("config")
        self.config_dir.mkdir(exist_ok=True)
        self.ads_file = self.config_dir / "ads.json"
        
        self._start_download_thread()

    def _start_download_thread(self):
        thread = threading.Thread(target=self.download_ads, daemon=True)
        thread.start()

    def download_ads(self):
        try:
            content = fetch_url_content("https://z.clash.ink/chfs/shared/MinecraftFRP/Data/ads.json")
            with open(self.ads_file, "w", encoding="utf-8") as f:
                f.write(content)
            
            if self.parse_ads():
                logger.info("成功下载并更新了 ads.json。")

        except Exception as e:
            logger.error(f"下载ads.json时出错: {e}")
            self.try_load_local_ads()

    def parse_ads(self):
        try:
            with open(self.ads_file, "r", encoding="utf-8") as f:
                self.ads = json.load(f)
            return True
        except Exception as e:
            logger.error(f"解析ads.json时出错: {e}")
            self.load_default_ads()
            return False

    def try_load_local_ads(self):
        if self.ads_file.exists():
            logger.info(f"发现本地ads.json在{self.ads_file}，尝试读取。")
            self.parse_ads()
        else:
            logger.info("本地没有ads.json，使用默认广告。")
            self.load_default_ads()

    def load_default_ads(self):
        self.ads = [
            {"show": "请更新到最新版本，此版本可能有一些问题。", "url": "https://example.com"}
        ]

    def get_next_ad(self):
        if not self.ads:
            return None
        ad = self.ads[self.current_ad_index]
        self.current_ad_index = (self.current_ad_index + 1) % len(self.ads)
        return ad
