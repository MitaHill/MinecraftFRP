from PySide6.QtCore import QMutexLocker
from PySide6.QtWidgets import QApplication
from src.core.ConfigManager import ConfigManager

def handle_close_event(window, event):
    """处理窗口关闭事件，确保资源被安全释放"""
    window.is_closing = True
    
    # 停止所有定时器
    window.ping_timer.stop()
    
    # 停止所有正在运行的线程
    stop_all_threads(window)

    # 清理特定配置文件（如果存在）
    if hasattr(window, '_current_config_path') and window._current_config_path:
        # ConfigManager is a static class, call method directly on it.
        ConfigManager.delete_config(window._current_config_path)
    
    # 清理所有ConfigManager追踪的临时文件 (old behavior, just in case)
    ConfigManager.cleanup_temp_dir()
    
    # 退出应用程序
    QApplication.quit()

def stop_all_threads(window):
    """优雅地停止所有后台线程"""
    with QMutexLocker(window.app_mutex):
        # 停止滚动广告定时器
        if hasattr(window, 'scrolling_ad_timer'):
            window.scrolling_ad_timer.stop()

        # 停止 frpc 线程
        if window.th and window.th.isRunning():
            window.log("正在关闭frpc进程...", "orange")
            window.th.stop()
            window.th.wait() # 等待线程完全终止

        # 停止 LAN 轮询线程
        if window.lan_poller and window.lan_poller.isRunning():
            window.lan_poller.stop()
            window.lan_poller.wait() # 等待线程完全终止

        # 停止其他后台线程
        threads_to_stop = [
            'server_update_thread',
            'update_checker_thread',
            'download_thread',
            'ping_thread',
            'ad_thread',
            'tunnel_monitor'
        ]
        
        # 优先处理 SecurityCheckThread，必须等待其自然结束
        if hasattr(window, 'security_check_thread'):
            thread = window.security_check_thread
            if thread and thread.isRunning():
                window.log("等待安全检查完成...", "orange")
                thread.wait() # 无限等待，直到线程结束
        
        for thread_name in threads_to_stop:
            if hasattr(window, thread_name):
                thread = getattr(window, thread_name)
                try:
                    if thread and thread.isRunning():
                        # 大多数QThread子类默认没有stop方法，使用terminate不安全，wait即可
                        # 如果有特定的stop方法（如ServerUpdateThread），应该调用它
                        # 这里尝试通用处理：如果有stop则调用，否则等待
                        if hasattr(thread, 'stop') and callable(thread.stop):
                            thread.stop()
                        thread.wait(2000) # 最多等待2秒
                        if thread.isRunning():
                            thread.terminate() # 强制终止（防止挂起关闭流程）
                except RuntimeError:
                    # C++对象已删除，忽略
                    pass
                except Exception as e:
                    print(f"Error stopping thread {thread_name}: {e}")
