"""
测试 Windows Toast 通知功能
用于验证 launcher 的气泡提示是否正常工作
"""
import sys
import subprocess
import time


def show_toast(message: str, silent: bool = True):
    """显示 Windows 10/11 气泡通知（Toast Notification），静音模式"""
    try:
        # PowerShell 脚本：显示 Toast（无声音）
        ps_script = f'''
        [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
        [Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null
        
        $template = @"
        <toast>
            <visual>
                <binding template="ToastText02">
                    <text id="1">MinecraftFRP 更新</text>
                    <text id="2">{message}</text>
                </binding>
            </visual>
            <audio silent="true"/>
        </toast>
"@
        
        $xml = New-Object Windows.Data.Xml.Dom.XmlDocument
        $xml.LoadXml($template)
        $toast = [Windows.UI.Notifications.ToastNotification]::new($xml)
        [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("MinecraftFRP").Show($toast)
        '''
        
        result = subprocess.run(
            ['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', ps_script],
            capture_output=True,
            timeout=2,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        )
        
        if result.returncode == 0:
            print(f"✅ 气泡通知已发送: {message}")
        else:
            print(f"❌ 气泡通知失败: {result.stderr.decode('utf-8', errors='ignore')}")
            
    except Exception as e:
        print(f"❌ Toast notification failed: {e}")


def test_download_progress():
    """模拟下载进度通知"""
    print("\n🧪 测试下载进度通知（每20%一次）...\n")
    
    for progress in [20, 40, 60, 80, 100]:
        speed = 1024.5  # 模拟速度
        message = f"正在下载新版本。当前进度：{progress}%，当前速度：{speed:.1f}KB/s"
        show_toast(message, silent=True)
        time.sleep(2)  # 每隔2秒发送一次
    
    print("\n🧪 测试下载完成通知...\n")
    show_toast("下载已完成。更新将在下一次联机工具启动时进行。", silent=True)
    print("\n✅ 测试完成！")


if __name__ == "__main__":
    print("=" * 60)
    print("MinecraftFRP Launcher Toast 通知测试")
    print("=" * 60)
    print("注意：此测试需要在 Windows 10/11 系统上运行")
    print("气泡通知将以静音模式显示在屏幕右下角")
    print("=" * 60)
    
    test_download_progress()
