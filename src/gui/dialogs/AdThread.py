# src/gui/dialogs/AdThread.py

import yaml
from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QPixmap
from src.utils.HttpManager import fetch_url_content
from src.utils.LogManager import get_logger
from src.config.SecretConfig import SecretConfig

logger = get_logger()

class AdThread(QThread):
    """
    A worker thread to fetch all advertisement data from a unified YAML index.
    It fetches the YAML, then processes the popup ads section to download images.
    """
    finished = Signal(dict)  # Signal emitting the entire parsed ad data dictionary

    INDEX_URL = SecretConfig.AD_INDEX_URL
    IMAGE_BASE_URL = SecretConfig.AD_IMAGE_BASE_URL
    CACHE_DIR = "config/ads"
    LOCAL_INDEX = "config/ads/ads_index.yaml"

    def run(self):
        """The main entry point for the thread's execution."""
        try:
            logger.info("后台广告线程启动，开始获取统一广告索引...")
            
            # 确保本地缓存目录存在
            import os
            os.makedirs(self.CACHE_DIR, exist_ok=True)

            # 1. Fetch YAML index file（失败则使用本地缓存）
            yaml_content = fetch_url_content(self.INDEX_URL)
            if not yaml_content:
                logger.warning("统一广告索引文件下载失败或为空。尝试使用本地缓存索引。")
                try:
                    with open(self.LOCAL_INDEX, 'r', encoding='utf-8') as f:
                        yaml_content = f.read()
                except Exception:
                    return

            # 读取旧索引以判断差异（在覆盖前读取）
            old_index = None
            try:
                with open(self.LOCAL_INDEX, 'r', encoding='utf-8') as f:
                    old_index = yaml.safe_load(f.read())
            except Exception:
                old_index = None

            # 2. Parse YAML & 保存到本地缓存
            ad_data = yaml.safe_load(yaml_content)
            if not isinstance(ad_data, dict):
                logger.error("统一广告索引文件格式错误，根节点应为字典。")
                return
            try:
                with open(self.LOCAL_INDEX, 'w', encoding='utf-8') as f:
                    f.write(yaml_content)
            except Exception:
                logger.warning("写入本地广告索引失败，但继续运行。")
            
            logger.info(f"成功解析统一广告索引。")
            
            # 3. Process popup ads
            popup_ads = ad_data.get('popup_ads', [])
            if not isinstance(popup_ads, list):
                logger.error("YAML格式错误: 'popup_ads' 应为一个列表。")
                popup_ads = []

            def eq_index(a, b):
                try:
                    return a == b
                except Exception:
                    return False

            processed_popup_ads = []
            if old_index and eq_index(old_index, ad_data):
                # 无差异：直接加载本地图片
                logger.info("广告索引未变化，使用本地缓存图片。")
                for ad_item in popup_ads:
                    image_name = ad_item.get('image', '')
                    img_path = os.path.abspath(os.path.join(self.CACHE_DIR, image_name))
                    try:
                        pixmap = QPixmap()
                        if not pixmap.load(img_path):
                            logger.warning(f"本地图片无效: {img_path}，尝试重新下载...")
                            # 回退：下载并缓存
                            fetched = None
                            try:
                                from src.utils.HttpManager import get_session
                                session = get_session()
                                url = f"{self.IMAGE_BASE_URL}{image_name}?v=1"
                                resp = session.get(url, timeout=20, verify=True)
                                resp.raise_for_status()
                                data = resp.content
                                if data:
                                    with open(img_path, 'wb') as f:
                                        f.write(data)
                                    pixmap = QPixmap()
                                    if not pixmap.loadFromData(data):
                                        logger.warning(f"重新下载后仍无法加载图片: {url}")
                                        continue
                                else:
                                    continue
                            except Exception as e2:
                                logger.warning(f"下载图片失败 {image_name}: {e2}")
                                continue
                        processed = ad_item.copy()
                        processed['pixmap'] = pixmap
                        processed_popup_ads.append(processed)
                    except Exception as e:
                        logger.warning(f"加载本地图片失败 {img_path}: {e}")
            else:
                # 有差异：删除多余，下载新增
                try:
                    existing_files = set(os.listdir(self.CACHE_DIR))
                except Exception:
                    existing_files = set()
                index_files = set([ad.get('image', '') for ad in popup_ads if ad.get('image')])
                # 删除多余
                for fname in existing_files:
                    if fname.endswith('.png') or fname.endswith('.jpg') or fname.endswith('.jpeg'):
                        if fname not in index_files:
                            try:
                                os.remove(os.path.join(self.CACHE_DIR, fname))
                            except Exception:
                                pass
                
                # 并行下载缺失
                def fetch_one(ad_item):
                    if not all(k in ad_item for k in ['image', 'url', 'remark', 'duration']):
                        logger.warning(f"跳过格式不完整的弹窗广告条目: {ad_item}")
                        return None
                    image_name = ad_item['image']
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
                            return None
                        # 写入本地缓存文件
                        try:
                            with open(os.path.join(self.CACHE_DIR, image_name), 'wb') as f:
                                f.write(image_data)
                        except Exception:
                            pass
                        pixmap = QPixmap()
                        if not pixmap.loadFromData(image_data):
                            logger.warning(f"无法从数据加载图片: {image_url}")
                            return None
                        processed_ad = ad_item.copy()
                        processed_ad['pixmap'] = pixmap
                        return processed_ad
                    except Exception as e:
                        logger.error(f"处理弹窗广告图片 {image_url} 时出错: {e}")
                        return None
                try:
                    from concurrent.futures import ThreadPoolExecutor, as_completed
                    need_download = [item for item in popup_ads if item.get('image') and item.get('image') not in existing_files]
                    with ThreadPoolExecutor(max_workers=4) as ex:
                        futures = [ex.submit(fetch_one, item) for item in need_download]
                        for fut in as_completed(futures):
                            res = fut.result()
                            if res:
                                processed_popup_ads.append(res)
                    # 对于已有的，直接从本地读
                    for item in popup_ads:
                        if item.get('image') in existing_files:
                            p = os.path.join(self.CACHE_DIR, item.get('image'))
                            pix = QPixmap(p)
                            if not pix.isNull():
                                proc = item.copy(); proc['pixmap'] = pix
                                processed_popup_ads.append(proc)
                except Exception:
                    # 回退：串行处理
                    for item in popup_ads:
                        res = fetch_one(item)
                        if res:
                            processed_popup_ads.append(res)
            ad_data['popup_ads'] = processed_popup_ads

            if ad_data.get('popup_ads') or ad_data.get('scrolling_ads'):
                logger.info("广告资源处理完毕，发射信号。")
                self.finished.emit(ad_data)

        except yaml.YAMLError as e:
            logger.error(f"解析统一广告索引YAML时出错: {e}")
        except Exception as e:
            logger.error(f"获取统一广告数据时发生未知错误: {e}")

