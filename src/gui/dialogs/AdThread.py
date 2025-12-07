# src/gui/dialogs/AdThread.py

import yaml
from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QPixmap
from src.utils.HttpManager import fetch_url_content
from src.utils.LogManager import get_logger

logger = get_logger()

class AdThread(QThread):
    """
    A worker thread to fetch all advertisement data from a unified YAML index.
    It fetches the YAML, then processes the popup ads section to download images.
    """
    finished = Signal(dict)  # Signal emitting the entire parsed ad data dictionary

    INDEX_URL = "https://z.clash.ink/chfs/shared/MinecraftFRP/Data/ads/ads_index.yaml"
    IMAGE_BASE_URL = "https://z.clash.ink/chfs/shared/MinecraftFRP/Data/ads/photos/"

    def run(self):
        """The main entry point for the thread's execution."""
        try:
            logger.info("后台广告线程启动，开始获取统一广告索引...")
            
            # 1. Fetch YAML index file
            yaml_content = fetch_url_content(self.INDEX_URL)
            if not yaml_content:
                logger.warning("统一广告索引文件下载失败或为空。")
                return

            # 2. Parse YAML
            ad_data = yaml.safe_load(yaml_content)
            if not isinstance(ad_data, dict):
                logger.error("统一广告索引文件格式错误，根节点应为字典。")
                return
            
            logger.info(f"成功解析统一广告索引。")
            
            # 3. Process popup ads to fetch images
            popup_ads = ad_data.get('popup_ads', [])
            if not isinstance(popup_ads, list):
                logger.error("YAML格式错误: 'popup_ads' 应为一个列表。")
                popup_ads = []

            processed_popup_ads = []
            for ad_item in popup_ads:
                if not all(k in ad_item for k in ['image', 'url', 'remark', 'duration']):
                    logger.warning(f"跳过格式不完整的弹窗广告条目: {ad_item}")
                    continue

                image_name = ad_item['image']
                # Append cache-busting query parameter
                image_url = f"{self.IMAGE_BASE_URL}{image_name}?v=1"
                
                try:
                    logger.info(f"正在下载弹窗广告图片: {image_url}")
                    from src.utils.HttpManager import get_session
                    session = get_session()
                    response = session.get(image_url, timeout=20, verify=True)
                    response.raise_for_status()
                    image_data = response.content

                    if not image_data:
                        logger.warning(f"下载图片失败或为空: {image_url}")
                        continue
                    
                    pixmap = QPixmap()
                    if not pixmap.loadFromData(image_data):
                        logger.warning(f"无法从数据加载图片: {image_url}")
                        continue
                    
                    # Create a new dictionary with the pixmap
                    processed_ad = ad_item.copy()
                    processed_ad['pixmap'] = pixmap
                    processed_popup_ads.append(processed_ad)

                except Exception as e:
                    logger.error(f"处理弹窗广告图片 {image_url} 时出错: {e}")
            
            # Replace the original popup_ads with the processed ones (with pixmaps)
            ad_data['popup_ads'] = processed_popup_ads

            if ad_data.get('popup_ads') or ad_data.get('scrolling_ads'):
                logger.info("广告资源处理完毕，发射信号。")
                self.finished.emit(ad_data)

        except yaml.YAMLError as e:
            logger.error(f"解析统一广告索引YAML时出错: {e}")
        except Exception as e:
            logger.error(f"获取统一广告数据时发生未知错误: {e}")

