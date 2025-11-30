from PySide6.QtCore import QMutexLocker
from PySide6.QtWidgets import QApplication

def handle_close_event(window, event):
    """处理窗口关闭事件，确保资源被安全释放"""
    window.is_closing = True
    
    # 停止所有定时器
    window.ad_timer.stop()
    window.ping_timer.stop()
    
    # 停止所有正在运行的线程
    stop_all_threads(window)

    # 清理配置文件
    window.config_manager.delete_config()
    
    # 退出应用程序
    QApplication.quit()

def stop_all_threads(window):
    """优雅地停止所有后台线程"""
    with QMutexLocker(window.app_mutex):
        # 停止 frpc 线程
        if window.th and window.th.isRunning():
            window.log("正在关闭frpc进程...", "orange")
            window.th.stop()
            window.th.wait() # 等待线程完全终止

        # 停止 LAN 轮询线程
        if window.lan_poller and window.lan_poller.isRunning():
            window.lan_poller.stop()
            window.lan_poller.wait() # 等待线程完全终止

        # 停止日志裁剪线程
        if hasattr(window, 'log_trimmer') and window.log_trimmer and window.log_trimmer.isRunning():
            window.log_trimmer.stop()
            window.log_trimmer.wait()
