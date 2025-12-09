import os
import re
import subprocess
import sys
import platform
import socket
import time
import random
import string
import threading
import concurrent.futures
import json
from urllib.parse import urlparse
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import ctypes
from ctypes import wintypes
from datetime import datetime
from src.core.heartbeat_manager import HeartbeatManager

# 隐藏启动时的控制台窗口
if platform.system() == "Windows":
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

# 黑白灰主题颜色配置
BW_COLORS = {
    "primary": "#404040",
    "secondary": "#606060", 
    "accent": "#808080",
    "success": "#505050",
    "warning": "#707070",
    "danger": "#303030",
    "dark": "#202020",
    "light": "#f0f0f0",
    "background": "#e8e8e8",
    "card_bg": "#ffffff",
    "text_primary": "#000000",
    "text_secondary": "#404040",
    "border": "#c0c0c0"
}

# 字体配置
BW_FONTS = {
    "title": ("Segoe UI", 16, "bold"),
    "subtitle": ("Segoe UI", 12, "bold"), 
    "normal": ("Segoe UI", 10),
    "small": ("Segoe UI", 9),
    "button": ("Segoe UI", 10, "bold")
}

def create_bw_button(parent, text, command, style="primary", width=None):
    """创建黑白灰风格按钮"""
    btn = tk.Button(
        parent,
        text=text,
        command=command,
        font=BW_FONTS["button"],
        bg=BW_COLORS[style],
        fg="white",
        activebackground=BW_COLORS["accent"],
        activeforeground="white",
        relief="flat",
        bd=0,
        padx=20,
        pady=8,
        cursor="hand2",
        width=width
    )
    
    # 添加悬停效果
    def on_enter(e):
        btn['bg'] = BW_COLORS["accent"]
        
    def on_leave(e):
        btn['bg'] = BW_COLORS[style]
    
    btn.bind("<Enter>", on_enter)
    btn.bind("<Leave>", on_leave)
    
    return btn

def create_bw_frame(parent, **kwargs):
    """创建黑白灰风格框架"""
    return tk.Frame(
        parent,
        bg=BW_COLORS["card_bg"],
        relief="flat",
        bd=1,
        highlightbackground=BW_COLORS["border"],
        highlightthickness=1,
        **kwargs
    )

def create_section_title(parent, text):
    """创建分区标题"""
    title_frame = tk.Frame(parent, bg=BW_COLORS["background"])
    title_frame.pack(fill=tk.X, pady=(10, 5))
    
    title_label = tk.Label(
        title_frame,
        text=text,
        font=BW_FONTS["subtitle"],
        bg=BW_COLORS["background"],
        fg=BW_COLORS["primary"],
        anchor="w"
    )
    title_label.pack(fill=tk.X, padx=15)
    
    # 添加装饰线
    separator = tk.Frame(title_frame, height=2, bg=BW_COLORS["primary"])
    separator.pack(fill=tk.X, padx=15, pady=(2, 0))
    
    return title_frame

def check_cloud_permission():
    """检查云端软件使用许可"""
    def check_permission():
        try:
            url = "https://lytapi.asia/st.txt"
            req = Request(url, headers={'User-Agent': 'LMFP/1.3.1'})
            
            with urlopen(req, timeout=10) as response:
                content = response.read().decode('utf-8').strip().lower()
                return content == "true"
        except Exception as e:
            print(f"检查云端许可失败: {e}")
            return False
    
    return check_permission()

# ==============================================
# 公告检查功能
# ==============================================

def check_announcements():
    """检查云端公告"""
    try:
        # 云端公告版本号文件
        cloud_version_url = "https://lytapi.asia/ggbb.txt"
        
        # 获取云端公告版本号
        req = Request(cloud_version_url, headers={'User-Agent': 'LMFP/1.3.1'})
        with urlopen(req, timeout=10) as response:
            cloud_version_str = response.read().decode('utf-8').strip()
            
            # 验证版本号是否为数字
            if not cloud_version_str.isdigit():
                print("云端公告版本号格式错误")
                return {'has_new_announcements': False}
            
            cloud_version = int(cloud_version_str)
            print(f"云端公告版本号: {cloud_version}")
        
        # 本地公告版本号文件
        local_version_file = "ggbb.txt"
        local_version = 0
        
        # 尝试读取本地版本号
        if os.path.exists(local_version_file):
            try:
                with open(local_version_file, 'r', encoding='utf-8') as f:
                    local_version_str = f.read().strip()
                    if local_version_str.isdigit():
                        local_version = int(local_version_str)
                        print(f"本地公告版本号: {local_version}")
                    else:
                        print("本地公告版本号格式错误，重置为0")
                        local_version = 0
            except Exception as e:
                print(f"读取本地公告版本号失败: {e}")
                local_version = 0
        
        # 比较版本号
        if cloud_version > local_version:
            print(f"发现新公告，云端版本: {cloud_version}, 本地版本: {local_version}")
            
            # 获取所有未读的公告
            announcements = []
            for version in range(local_version + 1, cloud_version + 1):
                try:
                    announcement_url = f"https://lytapi.asia/gg{version}.txt"
                    print(f"获取公告: {announcement_url}")
                    
                    req = Request(announcement_url, headers={'User-Agent': 'LMFP/1.3.1'})
                    with urlopen(req, timeout=10) as response:
                        content = response.read().decode('utf-8').strip()
                        if content:
                            announcements.append({
                                'version': version,
                                'content': content
                            })
                            print(f"✓ 成功获取公告 {version}")
                        else:
                            print(f"⚠ 公告 {version} 内容为空")
                except Exception as e:
                    print(f"✗ 获取公告 {version} 失败: {e}")
            
            # 如果有新公告，展示给用户
            if announcements:
                return {
                    'has_new_announcements': True,
                    'cloud_version': cloud_version,
                    'local_version': local_version,
                    'announcements': announcements
                }
            else:
                print("未获取到有效的公告内容")
                return {'has_new_announcements': False}
        
        print("没有新公告")
        return {'has_new_announcements': False}
        
    except Exception as e:
        print(f"公告检查过程中出错: {e}")
        return {'has_new_announcements': False}

def show_announcements_window(announcements_info):
    """显示黑白灰风格公告窗口"""
    if not announcements_info or not announcements_info['has_new_announcements']:
        return None
    
    announcements = announcements_info['announcements']
    
    announcement_window = tk.Tk()
    announcement_window.title(f"软件公告 ({len(announcements)}条新公告)")
    announcement_window.geometry("800x900")
    announcement_window.resizable(True, True)
    announcement_window.configure(bg=BW_COLORS["background"])
    announcement_window.attributes('-topmost', True)
    
    try:
        icon_path = "lyy.ico"
        if os.path.exists(icon_path):
            announcement_window.iconbitmap(icon_path)
    except:
        pass
    
    main_container = create_bw_frame(announcement_window)
    main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
    
    header_frame = tk.Frame(main_container, bg=BW_COLORS["card_bg"])
    header_frame.pack(fill=tk.X, padx=20, pady=15)
    
    icon_label = tk.Label(
        header_frame,
        text="📢",
        font=("Arial", 24),
        bg=BW_COLORS["card_bg"],
        fg=BW_COLORS["primary"]
    )
    icon_label.pack(side=tk.LEFT)
    
    title_label = tk.Label(
        header_frame,
        text=f"软件公告 ({len(announcements)}条新公告)",
        font=BW_FONTS["title"],
        bg=BW_COLORS["card_bg"],
        fg=BW_COLORS["dark"]
    )
    title_label.pack(side=tk.LEFT, padx=10)
    
    # 创建笔记本控件，用于多公告切换
    notebook = ttk.Notebook(main_container)
    notebook.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 10))
    
    style = ttk.Style()
    style.configure("BW.TNotebook", background=BW_COLORS["card_bg"])
    style.configure("BW.TNotebook.Tab", 
                   background=BW_COLORS["secondary"],
                   foreground="white",
                   padding=[10, 5])
    style.map("BW.TNotebook.Tab", 
             background=[("selected", BW_COLORS["primary"])],
             foreground=[("selected", "white")])
    
    frames = []
    text_widgets = []
    
    for idx, ann in enumerate(announcements):
        # 创建每个公告的标签页
        frame = create_bw_frame(notebook)
        frames.append(frame)
        
        # 公告标题
        title_frame = tk.Frame(frame, bg=BW_COLORS["card_bg"])
        title_frame.pack(fill=tk.X, padx=15, pady=10)
        
        ann_title = tk.Label(
            title_frame,
            text=f"公告 #{ann['version']}",
            font=BW_FONTS["subtitle"],
            bg=BW_COLORS["card_bg"],
            fg=BW_COLORS["primary"]
        )
        ann_title.pack(anchor="w")
        
        date_label = tk.Label(
            title_frame,
            text=f"--- : {datetime.now().strftime('-')}",
            font=BW_FONTS["small"],
            bg=BW_COLORS["card_bg"],
            fg=BW_COLORS["text_secondary"]
        )
        date_label.pack(anchor="w", pady=(2, 0))
        
        # 公告内容
        content_frame = create_bw_frame(frame)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        text_widget = scrolledtext.ScrolledText(
            content_frame,
            width=70,
            height=20,
            font=BW_FONTS["normal"],
            wrap=tk.WORD,
            bg=BW_COLORS["light"],
            fg=BW_COLORS["text_primary"],
            relief="flat",
            bd=0,
            padx=15,
            pady=15
        )
        text_widget.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        text_widget.insert(tk.END, ann['content'])
        text_widget.config(state=tk.DISABLED)
        text_widgets.append(text_widget)
        
        # 添加到笔记本
        notebook.add(frame, text=f"公告{idx+1}")
    
    # 底部按钮
    button_frame = tk.Frame(main_container, bg=BW_COLORS["card_bg"])
    button_frame.pack(fill=tk.X, padx=20, pady=10)
    
    def mark_as_read_and_close():
        try:
            # 更新本地版本号
            with open("ggbb.txt", 'w', encoding='utf-8') as f:
                f.write(str(announcements_info['cloud_version']))
            print(f"✓ 已更新本地公告版本号为: {announcements_info['cloud_version']}")
        except Exception as e:
            print(f"✗ 更新本地公告版本号失败: {e}")
        
        announcement_window.destroy()
    
    def close_without_mark():
        announcement_window.destroy()
    
    # 左对齐按钮组
    left_btn_frame = tk.Frame(button_frame, bg=BW_COLORS["card_bg"])
    left_btn_frame.pack(side=tk.LEFT)
    
    prev_btn = create_bw_button(left_btn_frame, "← 上一条", lambda: show_prev_announcement(), "secondary", width=10)
    prev_btn.pack(side=tk.LEFT, padx=5)
    prev_btn.config(state='disabled')  # 第一条公告时禁用
    
    next_btn = create_bw_button(left_btn_frame, "下一条 →", lambda: show_next_announcement(), "secondary", width=10)
    next_btn.pack(side=tk.LEFT, padx=5)
    if len(announcements) <= 1:
        next_btn.config(state='disabled')  # 只有一条公告时禁用
    
    # 右对齐按钮组
    right_btn_frame = tk.Frame(button_frame, bg=BW_COLORS["card_bg"])
    right_btn_frame.pack(side=tk.RIGHT)
    
    close_btn = create_bw_button(right_btn_frame, "关闭", close_without_mark, "secondary", width=10)
    close_btn.pack(side=tk.RIGHT, padx=5)
    
    mark_read_btn = create_bw_button(right_btn_frame, "✓ 标记为已读并关闭", mark_as_read_and_close, "success", width=18)
    mark_read_btn.pack(side=tk.RIGHT, padx=5)
    
    # 标签页切换函数
    current_tab = [0]  # 使用列表以便在闭包中修改
    
    def show_next_announcement():
        if current_tab[0] < len(announcements) - 1:
            current_tab[0] += 1
            notebook.select(current_tab[0])
            update_nav_buttons()
    
    def show_prev_announcement():
        if current_tab[0] > 0:
            current_tab[0] -= 1
            notebook.select(current_tab[0])
            update_nav_buttons()
    
    def update_nav_buttons():
        # 更新导航按钮状态
        prev_btn.config(state='normal' if current_tab[0] > 0 else 'disabled')
        next_btn.config(state='normal' if current_tab[0] < len(announcements) - 1 else 'disabled')
    
    def on_tab_changed(event):
        selected_index = notebook.index(notebook.select())
        current_tab[0] = selected_index
        update_nav_buttons()
    
    notebook.bind("<<NotebookTabChanged>>", on_tab_changed)
    
    # 添加键盘快捷键
    announcement_window.bind('<Right>', lambda e: show_next_announcement())
    announcement_window.bind('<Left>', lambda e: show_prev_announcement())
    announcement_window.bind('<Escape>', lambda e: close_without_mark())
    announcement_window.bind('<Return>', lambda e: mark_as_read_and_close())
    
    # 窗口居中
    announcement_window.update_idletasks()
    x = (announcement_window.winfo_screenwidth() - announcement_window.winfo_width()) // 2
    y = (announcement_window.winfo_screenheight() - announcement_window.winfo_height()) // 2
    announcement_window.geometry(f"+{x}+{y}")
    
    # 置于顶层
    announcement_window.attributes('-topmost', True)
    announcement_window.after(100, lambda: announcement_window.attributes('-topmost', False))
    
    return announcement_window

def show_cloud_permission_check():
    """显示黑白灰风格云端许可检查窗口"""
    check_window = tk.Tk()
    check_window.title("软件许可检查 - QQ2232908600")
    check_window.geometry("500x600")
    check_window.resizable(False, False)
    check_window.configure(bg=BW_COLORS["background"])
    check_window.attributes('-topmost', True)
    
    try:
        icon_path = "lyy.ico"
        if os.path.exists(icon_path):
            check_window.iconbitmap(icon_path)
    except:
        pass
    
    main_container = create_bw_frame(check_window)
    main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
    
    header_frame = tk.Frame(main_container, bg=BW_COLORS["card_bg"])
    header_frame.pack(fill=tk.X, padx=20, pady=20)
    
    icon_label = tk.Label(
        header_frame,
        text="🔍",
        font=("Arial", 24),
        bg=BW_COLORS["card_bg"],
        fg=BW_COLORS["primary"]
    )
    icon_label.pack(side=tk.LEFT)
    
    title_label = tk.Label(
        header_frame,
        text="软件许可检查",
        font=BW_FONTS["title"],
        bg=BW_COLORS["card_bg"],
        fg=BW_COLORS["text_primary"]
    )
    title_label.pack(side=tk.LEFT, padx=10)
    
    status_frame = tk.Frame(main_container, bg=BW_COLORS["card_bg"])
    status_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
    
    status_label = tk.Label(
        status_frame,
        text="正在检查云端许可...",
        font=BW_FONTS["subtitle"],
        bg=BW_COLORS["card_bg"],
        fg=BW_COLORS["text_secondary"]
    )
    status_label.pack()
    
    progress_frame = tk.Frame(main_container, bg=BW_COLORS["card_bg"])
    progress_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
    
    progress = ttk.Progressbar(progress_frame, mode='indeterminate', length=460)
    progress.pack(fill=tk.X)
    progress.start(10)
    
    detail_frame = create_bw_frame(main_container)
    detail_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
    
    detail_text = scrolledtext.ScrolledText(
        detail_frame,
        width=50,
        height=10,
        font=BW_FONTS["small"],
        wrap=tk.WORD,
        bg=BW_COLORS["light"],
        fg=BW_COLORS["text_primary"],
        relief="flat",
        bd=0,
        padx=10,
        pady=10
    )
    detail_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    detail_text.insert(tk.END, "正在连接服务器检查软件使用许可...\n")
    detail_text.config(state=tk.DISABLED)
    
    button_frame = tk.Frame(main_container, bg=BW_COLORS["card_bg"])
    button_frame.pack(fill=tk.X, padx=20, pady=20)
    
    result = [None]
    
    def update_status(message, is_error=False):
        detail_text.config(state=tk.NORMAL)
        detail_text.insert(tk.END, f"{message}\n")
        detail_text.see(tk.END)
        detail_text.config(state=tk.DISABLED)
        check_window.update()
        
        if is_error:
            status_label.config(text="检查失败", fg=BW_COLORS["danger"])
        else:
            status_label.config(text=message, fg=BW_COLORS["primary"])
    
    def perform_check():
        nonlocal result
        try:
            update_status("正在连接服务器: https://lytapi.asia/st.txt")
            time.sleep(1)
            
            if check_cloud_permission():
                progress.stop()
                progress.configure(mode='determinate', value=100)
                update_status("✓ 云端许可检查通过")
                update_status("软件可以正常使用")
                status_label.config(text="✓ 许可检查通过", fg=BW_COLORS["success"])
                result[0] = True
                check_window.after(2000, lambda: check_window.quit())
            else:
                progress.stop()
                update_status("✗ 云端许可检查失败")
                update_status("当前服务器禁止使用本软件")
                update_status("---------------------------------------------------")
                update_status(f"最新公告： {urlopen('https://lytapi.asia/tfgg.txt').read().decode('utf-8').strip()}", is_error=True)
                update_status("---------------------------------------------------")
                update_status("请尝试刷新许可状态或退出软件")
                status_label.config(text="✗ 许可检查失败", fg=BW_COLORS["danger"])
                result[0] = False
                refresh_btn.config(state='normal')
                exit_btn.config(state='normal')
                
        except Exception as e:
            progress.stop()
            update_status(f"✗ 检查过程中出错: {str(e)}")
            update_status("无法连接到许可服务器")
            update_status("请尝试刷新许可状态或退出软件")
            status_label.config(text="✗ 连接失败", fg=BW_COLORS["danger"])
            result[0] = False
            refresh_btn.config(state='normal')
            exit_btn.config(state='normal')
    
    def refresh_check():
        refresh_btn.config(state='disabled')
        exit_btn.config(state='disabled')
        detail_text.config(state=tk.NORMAL)
        detail_text.delete(1.0, tk.END)
        detail_text.insert(tk.END, "重新检查云端许可...\n")
        detail_text.config(state=tk.DISABLED)
        status_label.config(text="正在重新检查...", fg=BW_COLORS["primary"])
        progress.configure(mode='indeterminate')
        progress.start(10)
        check_window.after(100, perform_check)
    
    def exit_program():
        result[0] = False
        check_window.quit()
    
    refresh_btn = create_bw_button(button_frame, "⟳ 尝试刷新许可状态", refresh_check, "primary", width=20)
    refresh_btn.pack(side=tk.LEFT, padx=5)
    refresh_btn.config(state='disabled')
    
    exit_btn = create_bw_button(button_frame, "✗ 退出软件", exit_program, "danger", width=15)
    exit_btn.pack(side=tk.RIGHT, padx=5)
    exit_btn.config(state='disabled')
    
    check_window.update_idletasks()
    x = (check_window.winfo_screenwidth() - check_window.winfo_width()) // 2
    y = (check_window.winfo_screenheight() - check_window.winfo_height()) // 2
    check_window.geometry(f"+{x}+{y}")
    
    check_window.after(100, perform_check)
    return check_window, result

def show_disclaimer():
    """显示黑白灰风格免责声明窗口"""
    disclaimer_window = tk.Tk()
    disclaimer_window.title("免责声明")
    disclaimer_window.geometry("650x600")
    disclaimer_window.resizable(False, False)
    disclaimer_window.configure(bg=BW_COLORS["background"])
    disclaimer_window.attributes('-topmost', True)
    
    try:
        icon_path = "lyy.ico"
        if os.path.exists(icon_path):
            disclaimer_window.iconbitmap(icon_path)
    except:
        pass
    
    main_container = create_bw_frame(disclaimer_window)
    main_container.pack(fill=tk.BOTH, expand=True, padx=25, pady=25)
    
    header_frame = tk.Frame(main_container, bg=BW_COLORS["card_bg"])
    header_frame.pack(fill=tk.X, padx=20, pady=20)
    
    warning_icon = tk.Label(
        header_frame,
        text="⚠",
        font=("Arial", 28),
        bg=BW_COLORS["card_bg"],
        fg=BW_COLORS["warning"]
    )
    warning_icon.pack(side=tk.LEFT, padx=(0, 15))
    
    title_label = tk.Label(
        header_frame,
        text="免责声明",
        font=BW_FONTS["title"],
        bg=BW_COLORS["card_bg"],
        fg=BW_COLORS["dark"]
    )
    title_label.pack(side=tk.LEFT)
    
    content_frame = create_bw_frame(main_container)
    content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
    
    disclaimer_text = """
重要声明：本软件仅供学习交流网络技术使用

在使用本软件前，请仔细阅读以下内容：

使用条款
• 本软件仅限于学习、研究和测试网络连接技术
• 请勿将本软件用于任何商业用途或非法目的
• 使用者应对自己的行为承担全部法律责任
• 软件作者不对使用者的任何行为负责

安全规范  
• 请确保遵守当地法律法规和网络使用规定
• 禁止使用本软件进行任何形式的网络攻击或破坏
• 本软件不得用于侵犯他人合法权益的行为

版权声明
• 本软件为免费软件，仅供个人学习使用
• 禁止对本软件进行逆向工程、修改或重新分发
• 所有代码和设计均受版权法保护

使用协议
• 请在使用后24小时内删除本软件及相关文件
• 如不同意上述条款，请立即退出并删除本软件
• 继续使用即表示您同意以上所有条款

请慎重考虑后做出选择：
"""
    
    text_widget = scrolledtext.ScrolledText(
        content_frame,
        width=70,
        height=15,
        font=BW_FONTS["normal"],
        wrap=tk.WORD,
        bg=BW_COLORS["light"],
        fg=BW_COLORS["text_primary"],
        relief="flat",
        bd=0,
        padx=15,
        pady=15
    )
    text_widget.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    text_widget.insert(tk.END, disclaimer_text)
    text_widget.config(state=tk.DISABLED)
    
    action_frame = tk.Frame(main_container, bg=BW_COLORS["card_bg"])
    action_frame.pack(fill=tk.X, padx=20, pady=20)
    
    agree_var = tk.BooleanVar(value=False)
    
    def on_agree_changed():
        if agree_var.get():
            agree_btn.config(state='normal', bg=BW_COLORS["success"])
        else:
            agree_btn.config(state='disabled', bg=BW_COLORS["secondary"])
    
    agree_check = tk.Checkbutton(
        action_frame,
        text="我已阅读并同意以上所有条款",
        variable=agree_var,
        command=on_agree_changed,
        font=BW_FONTS["normal"],
        bg=BW_COLORS["card_bg"],
        fg=BW_COLORS["text_primary"],
        selectcolor=BW_COLORS["light"],
        activebackground=BW_COLORS["card_bg"],
        activeforeground=BW_COLORS["text_primary"]
    )
    agree_check.pack(pady=(0, 15))
    
    btn_container = tk.Frame(action_frame, bg=BW_COLORS["card_bg"])
    btn_container.pack(fill=tk.X)
    
    def agree_and_continue():
        disclaimer_window.quit()
        disclaimer_window.destroy()
    
    def disagree_and_exit():
        disclaimer_window.quit()
        disclaimer_window.destroy()
        os._exit(0)
    
    agree_btn = create_bw_button(btn_container, "✓ 同意并继续", agree_and_continue, "success", width=15)
    agree_btn.pack(side=tk.LEFT, padx=10)
    agree_btn.config(state='disabled', bg=BW_COLORS["secondary"])
    
    disagree_btn = create_bw_button(btn_container, "✗ 不同意并退出", disagree_and_exit, "danger", width=15)
    disagree_btn.pack(side=tk.RIGHT, padx=10)
    
    disclaimer_window.bind('<Return>', lambda e: agree_and_continue() if agree_var.get() else None)
    disclaimer_window.bind('<Escape>', lambda e: disagree_and_exit())
    
    disclaimer_window.update_idletasks()
    x = (disclaimer_window.winfo_screenwidth() - disclaimer_window.winfo_width()) // 2
    y = (disclaimer_window.winfo_screenheight() - disclaimer_window.winfo_height()) // 2
    disclaimer_window.geometry(f"+{x}+{y}")
    
    disclaimer_window.mainloop()
    return agree_var.get()

class LMFP_MinecraftTool:
    def __init__(self, root):
        self.root = root
        self.root.title("LMFP - Minecraft联机工具 - Beta 1.3.1 - Lyt_IT")
        self.root.geometry("550x900")
        self.root.resizable(True, True)
        self.root.configure(bg=BW_COLORS["background"])
        
        self.set_window_icon()
        self.is_admin = self.check_admin_privileges()
        self._cloud_warning_shown = False
        self.cloud_permission_granted = False
        
        self.ipv6 = ""
        self.mc_port = None
        self.mc_ports = [25565, 25566, 25567, 19132, 19133]
        self.frp_nodes = []
        self.best_node = None
        
        self.port_mapping_process = None
        self.is_port_mapping_active = False
        self.mapped_port = None
        
        self.frp_process = None
        self.is_frp_running = False
        self.current_room_code = None
        self.current_node_id = None
        self.current_remote_port = None
        
        # TCP隧道相关属性
        self.tunnel_active = False
        self.tunnel_socket = None
        self.tunnel_thread = None
        
        self.server_url = "https://lytapi.asia/api.php"
        self.current_rooms = []
        self.room_refresh_thread = None
        self.is_refreshing = False
        self.heartbeat_manager = HeartbeatManager(
            server_url=self.server_url,
            log_callback=self.log,
            is_frp_running_callback=self._check_frp_running_status
        )
        self.auto_refresh_flag = True
        self.refresh_btn = None
        
        self.create_bw_main_frame()
        self.is_scanning = False
        self.is_connecting = False
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def create_bw_main_frame(self):
        """创建黑白灰风格主界面"""
        main_container = tk.Frame(self.root, bg=BW_COLORS["background"])
        main_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        header_frame = create_bw_frame(main_container)
        header_frame.pack(fill=tk.X, pady=(0, 15))
        
        title_container = tk.Frame(header_frame, bg=BW_COLORS["card_bg"])
        title_container.pack(fill=tk.X, padx=20, pady=15)
        
        title_label = tk.Label(
            title_container,
            text="LMFP - Minecraft联机工具",
            font=BW_FONTS["title"],
            bg=BW_COLORS["card_bg"],
            fg=BW_COLORS["primary"]
        )
        title_label.pack()
        
        version_label = tk.Label(
            title_container,
            text="Beta 1.3.1 - Lyt_IT",
            font=BW_FONTS["small"],
            bg=BW_COLORS["card_bg"],
            fg=BW_COLORS["text_secondary"]
        )
        version_label.pack(pady=(2, 0))
        
        status_container = tk.Frame(header_frame, bg=BW_COLORS["card_bg"])
        status_container.pack(fill=tk.X, padx=20, pady=(0, 15))
        
        admin_status = "✓ 已获取管理员权限" if self.is_admin else "⚠ 未获取管理员权限"
        admin_label = tk.Label(
            status_container,
            text=admin_status,
            font=BW_FONTS["small"],
            bg=BW_COLORS["card_bg"],
            fg=BW_COLORS["success"] if self.is_admin else BW_COLORS["warning"]
        )
        admin_label.pack(anchor="w")
        
        cloud_status = "-------------------------------" 
        self.cloud_status_label = tk.Label(
            status_container,
            text=cloud_status,
            font=BW_FONTS["small"],
            bg=BW_COLORS["card_bg"],
            fg=BW_COLORS["text_secondary"]
        )
        self.cloud_status_label.pack(anchor="w", pady=(2, 0))
        
        author_label = tk.Label(
            status_container,
            text="作者: Lyt_IT | QQ: 2232908600",
            font=BW_FONTS["small"],
            bg=BW_COLORS["card_bg"],
            fg=BW_COLORS["text_secondary"]
        )
        author_label.pack(anchor="w", pady=(5, 0))
        
        functions_frame = create_bw_frame(main_container)
        functions_frame.pack(fill=tk.X, pady=(0, 15))
        
        create_section_title(functions_frame, "联机模式选择")
        
        buttons_container = tk.Frame(functions_frame, bg=BW_COLORS["card_bg"])
        buttons_container.pack(fill=tk.X, padx=15, pady=15)
        
        self.ipv6_btn = create_bw_button(
            buttons_container,
            "IPv6获取联机地址（推荐，速度快，端口自动识别）",
            self.run_ipv6_mode,
            "primary"
        )
        self.ipv6_btn.pack(fill=tk.X, pady=8)
        self.ipv6_btn.config(state='disabled')
        
        self.frp_create_btn = create_bw_button(
            buttons_container,
            "FRP联机 - 创建网络房间",
            self.run_frp_create,
            "secondary"
        )
        self.frp_create_btn.pack(fill=tk.X, pady=8)
        self.frp_create_btn.config(state='disabled')
        
        self.frp_join_btn = create_bw_button(
            buttons_container,
            "FRP联机 - 加入网络房间",
            self.run_frp_join,
            "secondary"
        )
        self.frp_join_btn.pack(fill=tk.X, pady=8)
        self.frp_join_btn.config(state='disabled')
        
        self.port_map_btn = create_bw_button(
            buttons_container,
            "将其他端口映射至25565",
            self.run_port_mapping,
            "primary"
        )
        self.port_map_btn.pack(fill=tk.X, pady=8)
        self.port_map_btn.config(state='disabled')
        
        self.lobby_btn = create_bw_button(
            buttons_container,
            "联机大厅 - 浏览和加入公开房间",
            self.show_lobby,
            "primary"
        )
        self.lobby_btn.pack(fill=tk.X, pady=8)
        self.lobby_btn.config(state='disabled')
        
        self.stop_btn = create_bw_button(
            buttons_container,
            "停止TCP隧道连接",
            self.stop_tcp_tunnel,
            "danger"
        )
        self.stop_btn.pack(fill=tk.X, pady=8)
        self.stop_btn.config(state='disabled')
        
        status_frame = create_bw_frame(main_container)
        status_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        create_section_title(status_frame, "状态信息")
        
        status_text_container = tk.Frame(status_frame, bg=BW_COLORS["card_bg"])
        status_text_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        self.status_text = scrolledtext.ScrolledText(
            status_text_container,
            height=5,
            width=80,
            font=BW_FONTS["normal"],
            bg=BW_COLORS["light"],
            fg=BW_COLORS["text_primary"],
            relief="flat",
            bd=0,
            padx=10,
            pady=10
        )
        self.status_text.pack(fill=tk.BOTH, expand=True)
        
        bottom_frame = tk.Frame(main_container, bg=BW_COLORS["background"])
        bottom_frame.pack(fill=tk.X)
        
        self.clear_btn = create_bw_button(bottom_frame, "清空日志", self.clear_log, "secondary", width=12)
        self.clear_btn.pack(side=tk.LEFT, padx=5)
        self.clear_btn.config(state='disabled')
        
        self.help_btn = create_bw_button(bottom_frame, "使用帮助", self.show_help, "primary", width=12)
        self.help_btn.pack(side=tk.LEFT, padx=5)
        self.help_btn.config(state='disabled')
        
        self.exit_btn = create_bw_button(bottom_frame, "退出程序", self.root.quit, "danger", width=12)
        self.exit_btn.pack(side=tk.RIGHT, padx=5)
        
    def set_window_icon(self):
        try:
            icon_path = "lyy.ico"
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
            else:
                possible_paths = [
                    "./lyy.ico", "lyy.ico",
                    os.path.join(os.path.dirname(__file__), "lyy.ico"),
                    os.path.join(os.path.dirname(sys.executable), "lyy.ico")
                ]
                for path in possible_paths:
                    if os.path.exists(path):
                        self.root.iconbitmap(path)
                        break
                else:
                    print("未找到 lyy.ico 图标文件，使用默认图标")
        except Exception as e:
            print(f"设置图标失败: {e}")
    
    def check_admin_privileges(self):
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False
    
    def lock_buttons(self):
        buttons = [self.ipv6_btn, self.frp_create_btn, self.frp_join_btn, 
                  self.port_map_btn, self.lobby_btn, self.stop_btn,
                  self.clear_btn, self.help_btn]
        
        for btn in buttons:
            btn.config(state='disabled', bg=BW_COLORS["text_secondary"])
        self.root.update()
        
    def unlock_buttons(self):
        buttons_config = [
            (self.ipv6_btn, "primary"),
            (self.frp_create_btn, "secondary"), 
            (self.frp_join_btn, "secondary"),
            (self.port_map_btn, "primary"),
            (self.lobby_btn, "primary"),
            (self.stop_btn, "danger"),
            (self.clear_btn, "secondary"),
            (self.help_btn, "primary")
        ]
        
        for btn, style in buttons_config:
            btn.config(state='normal', bg=BW_COLORS[style])
        self.root.update()
    
    def enable_all_buttons(self):
        self.cloud_permission_granted = True
        self.unlock_buttons()
        self.log("✓ 云端许可验证通过，所有功能已启用")
    
    def disable_all_buttons(self):
        self.cloud_permission_granted = False
        self.lock_buttons()
        self.log("✗ 云端许可验证失败，所有功能已禁用")
    
    def log(self, message):
        self.status_text.insert(tk.END, f"{message}\n")
        self.status_text.see(tk.END)
        self.root.update_idletasks()
    
    def clear_log(self):
        self.status_text.delete(1.0, tk.END)

    def show_help(self):
        help_window = tk.Toplevel(self.root)
        help_window.title("使用帮助")
        help_window.geometry("700x500")
        help_window.configure(bg=BW_COLORS["background"])
        
        try:
            icon_path = "lyy.ico"
            if os.path.exists(icon_path):
                help_window.iconbitmap(icon_path)
        except:
            pass
        
        main_container = create_bw_frame(help_window)
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        title_frame = tk.Frame(main_container, bg=BW_COLORS["card_bg"])
        title_frame.pack(fill=tk.X, padx=20, pady=15)
        
        title_label = tk.Label(
            title_frame,
            text="使用帮助",
            font=BW_FONTS["title"],
            bg=BW_COLORS["card_bg"],
            fg=BW_COLORS["primary"]
        )
        title_label.pack()
        
        content_frame = create_bw_frame(main_container)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        help_text = scrolledtext.ScrolledText(
            content_frame,
            width=80,
            height=20,
            font=BW_FONTS["normal"],
            wrap=tk.WORD,
            bg=BW_COLORS["light"],
            fg=BW_COLORS["text_primary"],
            relief="flat",
            bd=0,
            padx=15,
            pady=15
        )
        help_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        help_content = """
LMFP - Minecraft联机工具使用说明

IPv6联机模式：
• 需要双方都有IPv6网络支持
• 速度快，延迟低  
• 自动检测IPv6地址和Minecraft端口
• 自动复制联机地址到剪贴板

FRP创建房间：
• 无需IPv6，使用中转服务器
• 自动选择最佳节点
• 自动检测Minecraft端口
• 生成房间号：远程端口_FRP服务器号
• 可选择公开或私有房间

FRP进入房间：
• 输入朋友分享的房间号
• 自动从云端获取FRP服务器信息
• 使用TCP隧道将远程服务器映射到127.0.0.1:25565
• 无需启动FRP客户端

端口映射功能：
• 将其他Minecraft端口映射到25565
• 方便使用非标准端口的服务器
• 自动关闭防火墙规则
• 程序退出时自动清理映射

联机大厅：
• 浏览所有公开房间
• 30秒自动刷新房间列表
• 一键加入房间功能
• 显示房间详细信息

停止TCP隧道连接：
• 强制停止当前TCP隧道
• 解决连接冲突问题
• 安全清理网络连接

云端许可验证：
• 软件启动时需要验证云端许可
• 使用过程中会定期检查许可状态
• 如果许可验证失败，所有功能将被锁定
• 需要重新验证通过后才能继续使用

常见问题：
1. 如果无法连接，请检查防火墙设置
2. 确保已开启Minecraft局域网游戏
3. 联机时不要关闭程序窗口
4. 每人只能同时运行一个TCP隧道

技术支持：
QQ: 2232908600
微信: liuyvetong
        """
        
        help_text.insert(1.0, help_content)
        help_text.config(state=tk.DISABLED)
        
        close_frame = tk.Frame(main_container, bg=BW_COLORS["card_bg"])
        close_frame.pack(fill=tk.X, padx=20, pady=15)
        
        close_btn = create_bw_button(close_frame, "关闭", help_window.destroy, "primary", width=12)
        close_btn.pack()
    
    def validate_ipv6(self, ipv6):
        ipv6_pattern = r'^([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$|^::1$|^([0-9a-fA-F]{1,4}:){1,7}:|^:(:[0-9a-fA-F]{1,4}){1,7}$'
        return re.match(ipv6_pattern, ipv6) is not None
    
    def get_ipv6_powershell(self):
        try:
            ps_command = """
            Get-NetIPAddress -AddressFamily IPv6 | 
            Where-Object {
                $_.PrefixOrigin -eq 'RouterAdvertisement' -and 
                $_.SuffixOrigin -ne 'Link' -and 
                $_.IPAddress -notlike 'fe80*' -and 
                $_.IPAddress -notlike 'fc*' -and 
                $_.IPAddress -notlike 'fd*' -and 
                $_.IPAddress -ne '::1'
            } | 
            Select-Object -First 1 -ExpandProperty IPAddress
            """
            
            result = subprocess.run(["powershell", "-Command", ps_command], capture_output=True, text=True, check=True)
            ipv6 = result.stdout.strip()
            if ipv6 and self.validate_ipv6(ipv6):
                return ipv6
        except Exception:
            pass
        return None
    
    def get_ipv6_ipconfig(self):
        try:
            result = subprocess.run(["ipconfig"], capture_output=True, text=True, check=True)
            lines = result.stdout.split('\n')
            
            for line in lines:
                if "IPv6" in line and ":" in line:
                    parts = line.split(":")
                    if len(parts) > 1:
                        ipv6 = parts[1].strip()
                        self.log(f"检查地址: {ipv6}")
                        if re.match(r"^2[0-9a-f][0-9a-f][0-9a-f]:", ipv6) and self.validate_ipv6(ipv6):
                            return ipv6
        except Exception:
            pass
        return None
    
    def copy_to_clipboard(self, text):
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            return True
        except Exception:
            return False
    
    def is_port_occupied(self, port):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                result = s.connect_ex(('127.0.0.1', port))
                return result == 0
        except Exception:
            return False

    def is_port_occupied_by_java_original(self, port):
        try:
            if platform.system() == "Windows":
                result = subprocess.run(["netstat", "-ano"], capture_output=True, text=True, check=True)
                lines = result.stdout.split('\n')
                
                for line in lines:
                    if f":{port}" in line and "LISTENING" in line:
                        parts = line.split()
                        for part in parts:
                            if part.isdigit() and len(part) > 3:
                                pid = part
                                task_result = subprocess.run(
                                    ["tasklist", "/fi", f"pid eq {pid}", "/fo", "csv"], 
                                    capture_output=True, text=True, check=True
                                )
                                if "java.exe" in task_result.stdout:
                                    self.log(f"端口 {port} 被Java进程占用 (PID: {pid})")
                                    return True
                return False
            else:
                result = subprocess.run(["lsof", "-i", f":{port}"], capture_output=True, text=True, check=True)
                return "java" in result.stdout
        except Exception as e:
            self.log(f"检查端口占用时出错: {e}")
            return False

    def is_port_occupied_by_java(self, port):
        if self.is_port_mapping_active and port == 25565 and self.mapped_port:
            self.log(f"端口映射激活中，检查映射源端口 {self.mapped_port}")
            return self.is_port_occupied_by_java_original(self.mapped_port)
        return self.is_port_occupied_by_java_original(port)
    
    def get_java_process_ports(self):
        java_ports = []
        try:
            if platform.system() == "Windows":
                result = subprocess.run(["netstat", "-ano"], capture_output=True, text=True, check=True)
                lines = result.stdout.split('\n')
                
                java_pids = set()
                task_result = subprocess.run(
                    ["tasklist", "/fi", "imagename eq java.exe", "/fo", "csv"], 
                    capture_output=True, text=True, check=True
                )
                for line in task_result.stdout.split('\n'):
                    if 'java.exe' in line:
                        parts = line.split(',')
                        if len(parts) >= 2:
                            pid = parts[1].strip('"')
                            if pid.isdigit():
                                java_pids.add(pid)
                
                for line in lines:
                    if "LISTENING" in line:
                        parts = line.split()
                        for part in parts:
                            if ":" in part and "[" not in part:
                                try:
                                    port_str = part.split(":")[-1]
                                    port = int(port_str)
                                    for p in parts:
                                        if p.isdigit() and len(p) > 3:
                                            if p in java_pids and port not in java_ports:
                                                java_ports.append(port)
                                                self.log(f"发现Java进程监听端口: {port}")
                                                break
                                except ValueError:
                                    continue
            else:
                result = subprocess.run(["lsof", "-i", "-P", "-n"], capture_output=True, text=True, check=True)
                for line in result.stdout.split('\n'):
                    if "java" in line and "LISTEN" in line:
                        parts = line.split()
                        if len(parts) >= 9:
                            port_part = parts[8]
                            if ":" in port_part:
                                try:
                                    port = int(port_part.split(":")[1])
                                    if port not in java_ports:
                                        java_ports.append(port)
                                        self.log(f"发现Java进程监听端口: {port}")
                                except ValueError:
                                    continue
        except Exception as e:
            self.log(f"获取Java进程端口时出错: {e}")
        return java_ports
    
    def tcping_port(self, port):
        actual_port = port
        if self.is_port_mapping_active and port == 25565 and self.mapped_port:
            self.log(f"端口映射激活中，实际检查端口 {self.mapped_port}")
            actual_port = self.mapped_port
        
        self.log(f"正在验证端口 {actual_port} 是否为Minecraft联机端口...")
        
        try:
            with socket.socket(socket.AF_INET6 if self.ipv6 else socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(3)
                target_host = self.ipv6 if self.ipv6 else '127.0.0.1'
                s.connect((target_host, actual_port))
                self.log(f"端口 {actual_port} TCP连接成功")
                
                try:
                    s.settimeout(1)
                    data = s.recv(1024)
                    if data:
                        self.log(f"端口 {actual_port} 有数据响应，可能是Minecraft服务")
                        return True
                    else:
                        self.log(f"端口 {actual_port} 连接成功但无数据响应")
                        return False
                except socket.timeout:
                    self.log(f"端口 {actual_port} 连接成功但读取超时，可能是Minecraft服务")
                    return True
                except Exception as e:
                    self.log(f"端口 {actual_port} 读取数据时出错: {e}")
                    return False
        except socket.timeout:
            self.log(f"端口 {actual_port} 连接超时")
            return False
        except ConnectionRefusedError:
            self.log(f"端口 {actual_port} 连接被拒绝")
            return False
        except Exception as e:
            self.log(f"端口 {actual_port} 连接失败: {e}")
            return False
    
    def check_minecraft_ports(self):
        self.log("正在检测Minecraft端口...")
        
        if self.is_port_mapping_active and self.mapped_port:
            self.log(f"端口映射激活中，直接使用映射端口 {self.mapped_port}")
            if self.tcping_port(self.mapped_port):
                self.log(f"✓ 映射源端口 {self.mapped_port} 验证通过")
                return 25565
            else:
                self.log(f"✗ 映射源端口 {self.mapped_port} 验证失败")
                return None
        
        candidate_ports = []
        
        if not self.is_port_occupied(25565):
            self.log("25565端口未被占用，开始检测Java进程监听的端口...")
            java_ports = self.get_java_process_ports()
            
            if java_ports:
                for port in java_ports:
                    if port in self.mc_ports:
                        candidate_ports.append(port)
                
                if not candidate_ports:
                    candidate_ports = java_ports
            else:
                self.log("未找到Java进程监听的端口")
                return None
        else:
            self.log("25565端口已被占用，添加到候选端口")
            candidate_ports.append(25565)
        
        valid_ports = []
        for port in candidate_ports:
            if self.tcping_port(port):
                valid_ports.append(port)
                self.log(f"✓ 端口 {port} 验证通过，可能是Minecraft联机端口")
            else:
                self.log(f"✗ 端口 {port} 验证失败")
        
        if valid_ports:
            if 25565 in valid_ports:
                return 25565
            else:
                return valid_ports[0]
        else:
            self.log("所有候选端口验证失败")
            return None
    
    def check_java_minecraft_server(self):
        self.log("正在检查25565端口状态...")
        
        if self.is_port_mapping_active and self.mapped_port:
            self.log(f"端口映射激活中，检查映射源端口 {self.mapped_port}")
            if self.is_port_occupied_by_java_original(self.mapped_port):
                self.log(f"✓ 映射源端口 {self.mapped_port} 被Java进程占用")
                return True
            else:
                self.log(f"✗ 映射源端口 {self.mapped_port} 未被Java进程占用")
                return False
        
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                result = s.connect_ex(('127.0.0.1', 25565))
                if result == 0:
                    self.log("✓ 25565端口被占用，可能是Minecraft服务器")
                    return True
                else:
                    self.log("25565端口未被占用")
                    return False
        except Exception:
            self.log("25565端口检查失败")
            return False
    
    def manual_port_selection(self):
        self.log("\n无法确定Minecraft使用的端口，请手动确认：")
        self.log("1. 我已在Minecraft中开启局域网游戏")
        self.log("2. 我还没有开启局域网游戏")
        return None
    
    def generate_random_remote_port(self):
        return random.randint(10000, 60000)
    
    def get_frp_nodes(self):
        """从云端获取FRP节点列表"""
        self.log("正在从云端获取FRP节点列表...")
        
        try:
            url = "https://lytapi.asia/fplt.txt"
            req = Request(url, headers={'User-Agent': 'LMFP/1.3.1'})
            
            with urlopen(req, timeout=10) as response:
                content = response.read().decode('utf-8').strip()
                nodes = []
                
                # 检查内容是否为空
                if not content:
                    self.log("⚠ 云端返回空数据，使用备用节点")
                    return self.get_fallback_nodes()
                
                # 记录原始内容用于调试
                self.log(f"原始节点数据: （不对外公开）")  # 只显示前100字符
                
                for line in content.split('\n'):
                    line = line.strip()
                    if not line:
                        continue
                    
                    
                    if '#' in line and '[' in line and ']' in line:
                        parts = line.split('#', 1)
                        try:
                            node_id = int(parts[0].strip())
                            
                            inner_part = parts[1].strip()[1:-1]  # 去掉方括号
                            if ' ' in inner_part:
                                name_part, addr_part = inner_part.rsplit(' ', 1)
                                node_name = name_part.strip()
                                if ':' in addr_part:
                                    server_addr, server_port = addr_part.split(':')
                                    server_port = int(server_port.strip())
                                    
                                    node_info = {
                                        'node_id': node_id,
                                        'name': node_name,
                                        'server_addr': server_addr.strip(),
                                        'server_port': server_port
                                    }
                                    nodes.append(node_info)
                                    self.log(f"✓ 解析节点 #{node_id}: {node_name} ")
                        except Exception as e:
                            self.log(f"⚠ 解析节点行失败 '{line}': {e}")
                            continue
                
                if nodes:
                    self.log(f"✓ 从云端获取到 {len(nodes)} 个FRP节点")
                    return nodes
                else:
                    self.log("⚠ 云端数据格式异常，使用备用节点")
                    return self.get_fallback_nodes()
                    
        except Exception as e:
            self.log(f"✗ 获取FRP节点列表失败: {e}")
            self.log("✓ 使用备用FRP节点")
            return self.get_fallback_nodes()

    def get_fallback_nodes(self):
        """获取备用FRP节点列表"""
        self.log("正在加载备用FRP节点...")
        
        # 备用节点列表
        fallback_nodes = [
            {
                'node_id': 1,
                'name': 'Lyt_IT官方-青岛阿里云',
                'server_addr': '0.0.0.0',
                'server_port': 15443
            },
            {
                'node_id': 2,
                'name': 'Lyt_IT官方-青岛阿里云备用',
                'server_addr': '0.0.0.0', 
                'server_port': 15444
            },
            {
                'node_id': 3,
                'name': 'Lyt_IT官方-青岛阿里云备用2',
                'server_addr': '0.0.0.0',
                'server_port': 15445
            }
        ]
        
        self.log(f"✓ 加载 {len(fallback_nodes)} 个备用节点")
        for node in fallback_nodes:
            self.log(f"  节点 #{node['node_id']}: {node['name']} - {node['server_addr']}:{node['server_port']}")
        
        return fallback_nodes
    
    def create_frpc_config(self, node, proxy_name, local_port, remote_port):
        """创建frpc.toml配置文件"""
        config_content = f'''serverAddr = "{node['server_addr']}"
serverPort = {node['server_port']}

[[proxies]]
name = "{proxy_name}"
type = "tcp"
localIP = "127.0.0.1"
localPort = {local_port}
remotePort = {remote_port}
'''
        
        try:
            with open('frpc.toml', 'w', encoding='utf-8') as f:
                f.write(config_content)
            self.log("✓ frpc.toml配置文件创建成功")
            return True
        except Exception as e:
            self.log(f"✗ 创建frpc.toml配置文件失败: {e}")
            return False
    
    def is_frp_already_running(self):
        try:
            if platform.system() == "Windows":
                result = subprocess.run(
                    ['tasklist', '/fi', 'imagename eq frpc.exe', '/fo', 'csv'],
                    capture_output=True, text=True, check=True
                )
                return 'frpc.exe' in result.stdout
            else:
                result = subprocess.run(['pgrep', '-f', 'frpc'], capture_output=True, text=True)
                return result.returncode == 0
        except Exception:
            return False

    def cleanup_frp_process(self):
        try:
            if self.frp_process and self.frp_process.poll() is None:
                self.frp_process.terminate()
                self.frp_process.wait(timeout=5)
            
            if platform.system() == "Windows":
                subprocess.run(['taskkill', '/f', '/im', 'frpc.exe'], capture_output=True)
            else:
                subprocess.run(['pkill', '-f', 'frpc'], capture_output=True)
            
            self.is_frp_running = False
            self.frp_process = None
            return True
        except Exception as e:
            self.log(f"✗ 清理FRP进程失败: {e}")
            return False

    def _check_frp_running_status(self):
        """
        检查FRP客户端是否正在运行，包括通过当前进程和系统进程列表。
        """
        return self.is_frp_running or self.is_frp_already_running()

    def check_and_stop_existing_frp(self):
        if self.is_frp_already_running():
            self.log("⚠ 检测到已有FRP进程在运行")
            response = messagebox.askyesno(
                "FRP进程冲突", 
                "检测到已有FRP进程正在运行。\n\n是否停止现有进程并启动新的连接？\n\n注意：停止现有进程会导致当前联机中断。"
            )
            if response:
                if self.cleanup_frp_process():
                    self.log("✓ 已停止现有FRP进程")
                    return True
                else:
                    self.log("✗ 停止现有进程失败")
                    return False
            else:
                self.log("✗ 用户取消操作")
                return False
        return True

    def stop_frp(self):
        if not self.is_frp_running and not self.is_frp_already_running():
            self.log("ℹ 没有正在运行的FRP进程")
            return
        
        if messagebox.askyesno("确认停止", "确定要停止当前FRP连接吗？\n这将中断当前的联机会话。"):
            if self.cleanup_frp_process():
                self.log("✓ FRP进程已停止")
                self.heartbeat_manager.stop_room_heartbeat()
            else:
                self.log("✗ 停止FRP进程失败")

    def check_frp_installation(self):
        try:
            if os.path.exists("frpc.exe"):
                return True
            
            result = subprocess.run(['where', 'frpc.exe'], capture_output=True, text=True)
            if result.returncode == 0:
                return True
                
            self.log("✗ 未找到 frpc.exe")
            self.log("请确保 FRP 已正确安装并在系统PATH中")
            return False
        except Exception as e:
            self.log(f"✗ 检查FRP安装时出错: {e}")
            return False

    def run_frp_command(self):
        """运行FRP客户端"""
        try:
            if not os.path.exists('frpc.toml'):
                self.log("✗ frpc.toml配置文件不存在")
                return False
            
            self.log("正在启动FRP服务...")
            
            if platform.system() == "Windows":
                command = ['frpc.exe', '-c', 'frpc.toml']
                self.frp_process = subprocess.Popen(command, creationflags=subprocess.CREATE_NEW_CONSOLE)
                threading.Thread(target=self.monitor_frp_process, daemon=True).start()
                
                self.log("✓ 已启动FRP服务窗口")
                self.log("提示: FRP窗口应该已经弹出，请查看")
                return True
            else:
                command = ['./frpc', '-c', 'frpc.toml']
                self.frp_process = subprocess.Popen(command)
                threading.Thread(target=self.monitor_frp_process, daemon=True).start()
                self.log("✓ 已启动FRP服务")
                return True
        except Exception as e:
            self.is_frp_running = False
            self.log(f"✗ 启动FRP失败: {e}")
            return False

    def monitor_frp_process(self):
        try:
            if self.frp_process:
                self.frp_process.wait()
                self.is_frp_running = False
                self.frp_process = None
                
                            self.log("■ FRP进程已停止，自动停止心跳包发送")
                            self.heartbeat_manager.stop_room_heartbeat()        except Exception:
            pass

    def collect_room_info(self, remote_port, node_id, full_room_code, server_addr):
        info_window = tk.Toplevel(self.root)
        info_window.title("发布到联机大厅")
        info_window.geometry("500x500")
        info_window.transient(self.root)
        info_window.grab_set()
        info_window.resizable(False, False)
        info_window.configure(bg=BW_COLORS["background"])
        
        try:
            icon_path = "lyy.ico"
            if os.path.exists(icon_path):
                info_window.iconbitmap(icon_path)
        except:
            pass
        
        main_container = create_bw_frame(info_window)
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        title_frame = tk.Frame(main_container, bg=BW_COLORS["card_bg"])
        title_frame.pack(fill=tk.X, padx=20, pady=10)
        
        tk.Label(title_frame, text="房间信息设置", font=BW_FONTS["subtitle"], 
                bg=BW_COLORS["card_bg"], fg=BW_COLORS["primary"]).pack()
        
        room_info_frame = tk.Frame(main_container, bg=BW_COLORS["card_bg"])
        room_info_frame.pack(fill=tk.X, padx=20, pady=5)
        
        tk.Label(room_info_frame, text=f"完整房间号: {full_room_code}", 
                font=BW_FONTS["small"], fg=BW_COLORS["primary"]).pack(anchor="w")
        tk.Label(room_info_frame, text=f"服务器地址: {server_addr}:{remote_port}", 
                font=BW_FONTS["small"], fg=BW_COLORS["primary"]).pack(anchor="w")
        
        form_frame = create_bw_frame(main_container)
        form_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        tk.Label(form_frame, text="房主ID:", font=BW_FONTS["small"], 
                bg=BW_COLORS["card_bg"]).grid(row=0, column=0, sticky=tk.W, pady=8, padx=10)
        host_player_var = tk.StringVar()
        host_player_entry = tk.Entry(form_frame, textvariable=host_player_var, width=25, font=BW_FONTS["small"])
        host_player_entry.grid(row=0, column=1, sticky=tk.W, pady=8)
        host_player_entry.insert(0, "玩家")
        
        tk.Label(form_frame, text="游戏版本:", font=BW_FONTS["small"],
                bg=BW_COLORS["card_bg"]).grid(row=1, column=0, sticky=tk.W, pady=8, padx=10)
        version_var = tk.StringVar()
        version_entry = tk.Entry(form_frame, textvariable=version_var, width=25, font=BW_FONTS["small"])
        version_entry.grid(row=1, column=1, sticky=tk.W, pady=8)
        version_entry.insert(0, "1.20.1")
        
        tk.Label(form_frame, text="房间描述:", font=BW_FONTS["small"],
                bg=BW_COLORS["card_bg"]).grid(row=2, column=0, sticky=tk.NW, pady=8, padx=10)
        description_frame = tk.Frame(form_frame, bg=BW_COLORS["card_bg"])
        description_frame.grid(row=2, column=1, sticky=tk.W+tk.E, pady=8)
        
        description_text = tk.Text(description_frame, width=25, height=3, font=BW_FONTS["small"])
        description_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        description_text.insert("1.0", "欢迎来玩！")
        
        is_public_var = tk.BooleanVar(value=True)
        public_frame = tk.Frame(form_frame, bg=BW_COLORS["card_bg"])
        public_frame.grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=10, padx=10)
        
        public_check = tk.Checkbutton(public_frame, text="公开房间（在联机大厅显示）",
                                     variable=is_public_var, bg=BW_COLORS["card_bg"])
        public_check.pack(side=tk.LEFT)
        
        result = [None]
        
        def confirm_info():
            if not host_player_var.get().strip():
                messagebox.showwarning("输入错误", "请输入房主ID")
                host_player_entry.focus()
                return
            
            if not version_var.get().strip():
                messagebox.showwarning("输入错误", "请输入游戏版本")
                version_entry.focus()
                return
            
            description = description_text.get("1.0", tk.END).strip()
            if not description:
                description = "欢迎来玩！"
            
            room_info = {
                'full_room_code': full_room_code,
                'room_name': f"{host_player_var.get().strip()}的房间",
                'game_version': version_var.get().strip(),
                'player_count': 1,
                'max_players': 20,
                'description': description,
                'is_public': is_public_var.get(),
                'host_player': host_player_var.get().strip(),
                'server_addr': server_addr,
                'remote_port': remote_port
            }
            result[0] = room_info
            info_window.destroy()
        
        def skip_info():
            result[0] = None
            info_window.destroy()
        
        btn_frame = tk.Frame(main_container, bg=BW_COLORS["card_bg"])
        btn_frame.pack(pady=15)
        
        if is_public_var.get():
            btn_text = "发布到联机大厅"
        else:
            btn_text = "创建私有房间"
        
        confirm_btn = create_bw_button(btn_frame, btn_text, confirm_info, "primary", width=18)
        confirm_btn.pack(side=tk.LEFT, padx=5)
        
        cancel_btn = create_bw_button(btn_frame, "取消", skip_info, "secondary", width=10)
        cancel_btn.pack(side=tk.LEFT, padx=5)
        
        def update_btn_text():
            if is_public_var.get():
                confirm_btn.config(text="发布到联机大厅")
            else:
                confirm_btn.config(text="创建私有房间")
        
        is_public_var.trace('w', lambda *args: update_btn_text())
        host_player_entry.focus()
        host_player_entry.select_range(0, tk.END)
        
        info_window.bind('<Return>', lambda e: confirm_info())
        info_window.bind('<Escape>', lambda e: skip_info())
        
        info_window.wait_window()
        return result[0]

    def run_tcp_tunnel(self, server_addr, remote_port, local_port=25565):
        """运行TCP隧道，将远程服务器端口映射到本地端口"""



    def run_tcp_tunnel(self, server_addr, remote_port, local_port=25565):
        """运行TCP隧道，将远程服务器端口映射到本地端口"""
        try:
            self.log(f"启动TCP隧道: {server_addr}:{remote_port} -> 127.0.0.1:{local_port}")
            
            # 使用Python的socket来实现简单的端口转发
            def start_tunnel():
                import socket
                import threading
                
                def handle_client(client_socket, target_host, target_port):
                    try:
                        # 连接到目标服务器
                        target_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        target_socket.settimeout(10)
                        target_socket.connect((target_host, target_port))
                        
                        # 双向数据传输
                        def forward(source, destination, direction):
                            try:
                                while self.tunnel_active:
                                    data = source.recv(4096)
                                    if not data:
                                        break
                                    destination.send(data)
                            except Exception as e:
                                if self.tunnel_active:
                                    self.log(f"隧道数据转发错误 ({direction}): {e}")
                        
                        # 启动两个方向的转发线程
                        client_to_target = threading.Thread(
                            target=forward, 
                            args=(client_socket, target_socket, "客户端→服务器")
                        )
                        target_to_client = threading.Thread(
                            target=forward, 
                            args=(target_socket, client_socket, "服务器→客户端")
                        )
                        
                        client_to_target.daemon = True
                        target_to_client.daemon = True
                        
                        client_to_target.start()
                        target_to_client.start()
                        
                        # 等待任一线程结束
                        client_to_target.join()
                        target_to_client.join()
                        
                    except Exception as e:
                        if self.tunnel_active:
                            self.log(f"隧道连接错误: {e}")
                    finally:
                        try:
                            client_socket.close()
                        except:
                            pass
                        try:
                            target_socket.close()
                        except:
                            pass
                
                # 创建本地监听socket
                server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                server_socket.bind(('127.0.0.1', local_port))
                server_socket.listen(5)
                server_socket.settimeout(1)  # 设置超时以便检查隧道状态
                
                self.log(f"✓ TCP隧道已启动，监听 127.0.0.1:{local_port}")
                self.log(f"→ 转发到 {server_addr}:{remote_port}")
                
                self.tunnel_active = True
                self.tunnel_socket = server_socket
                
                try:
                    while self.tunnel_active:
                        try:
                            client_socket, addr = server_socket.accept()
                            self.log(f"新的连接来自: {addr[0]}:{addr[1]}")
                            
                            # 为每个客户端创建新的处理线程
                            client_thread = threading.Thread(
                                target=handle_client, 
                                args=(client_socket, server_addr, remote_port)
                            )
                            client_thread.daemon = True
                            client_thread.start()
                            
                        except socket.timeout:
                            continue  # 超时是正常的，用于检查隧道状态
                        except Exception as e:
                            if self.tunnel_active:  # 如果不是主动关闭
                                self.log(f"接受连接错误: {e}")
                            break
                            
                except Exception as e:
                    if self.tunnel_active:  # 如果不是主动关闭
                        self.log(f"隧道错误: {e}")
                finally:
                    server_socket.close()
                    self.tunnel_active = False
                    self.log("TCP隧道已停止")
        
            # 启动隧道线程
            self.tunnel_thread = threading.Thread(target=start_tunnel)
            self.tunnel_thread.daemon = True
            self.tunnel_thread.start()
            
            # 等待隧道启动
            time.sleep(1)
            return self.tunnel_active
            
        except Exception as e:
            self.log(f"✗ 启动TCP隧道失败: {e}")
            return False

    def stop_tcp_tunnel(self):
        """停止TCP隧道"""
        if hasattr(self, 'tunnel_active') and self.tunnel_active:
            self.tunnel_active = False
            if hasattr(self, 'tunnel_socket'):
                try:
                    self.tunnel_socket.close()
                except:
                    pass
            self.log("✓ TCP隧道已停止")

    def get_room_info_from_cloud(self, full_room_code):
        """从云端获取指定房间号的FRP服务器信息"""
        try:
            self.log(f"正在从云端获取房间 {full_room_code} 的信息...")
            
            # 解析房间号
            room_parts = full_room_code.split('_')
            if len(room_parts) != 2:
                self.log("✗ 房间号格式错误")
                return None
            
            remote_port = int(room_parts[0])
            node_id = int(room_parts[1])
            
            # 从云端获取FRP节点列表
            self.log(f"正在获取FRP节点 #{node_id} 的服务器信息...")
            nodes = self.get_frp_nodes()
            
            # 查找指定节点ID的服务器信息
            target_node = None
            for node in nodes:
                if node['node_id'] == node_id:
                    target_node = node
                    break
            
            if not target_node:
                self.log(f"✗ 未找到FRP节点 #{node_id} 的信息")
                return None
            
            self.log(f"✓ 找到FRP节点 #{node_id}: {target_node['name']}")
            self.log(f"   服务器地址: {target_node['server_addr']}:{target_node['server_port']}")
            
            # 使用房间号的前6位作为真正的远程端口
            actual_remote_port = int(str(remote_port)[:6]) if len(str(remote_port)) >= 6 else remote_port
            self.log(f"✓ 使用真正的远程端口: {actual_remote_port}")
            
            # 构建房间信息
            room_info = {
                'full_room_code': full_room_code,
                'server_addr': target_node['server_addr'],
                'server_port': target_node['server_port'],
                'remote_port': actual_remote_port,
                'node_id': node_id,
                'node_name': target_node['name'],
                'room_name': f"FRP节点#{node_id}的房间",
                'game_version': '未知',
                'host_player': '未知玩家',
                'description': f"通过FRP节点 #{node_id} 连接"
            }
            
            self.log(f"✓ 房间信息获取成功")
            return room_info
            
        except Exception as e:
            self.log(f"✗ 获取房间信息失败: {e}")
            return None

    def auto_join_room_from_lobby(self, full_room_code, room_info):
        """从联机大厅直接加入房间 - 使用TCP隧道"""
        def join_thread():
            try:
                # 重新从云端获取最新的节点信息
                fresh_room_info = self.get_room_info_from_cloud(full_room_code)
                if not fresh_room_info:
                    self.log("✗ 无法获取最新的房间信息")
                    return
                
                server_addr = fresh_room_info['server_addr']
                remote_port = fresh_room_info['remote_port']
                node_name = fresh_room_info['node_name']
                
                self.log(f"✓ 获取到最新房间信息")
                self.log(f"   完整房间号: {full_room_code}")
                self.log(f"   FRP节点: #{fresh_room_info['node_id']} - {node_name}")
                self.log(f"   服务器地址: {server_addr}:{remote_port}")
                
                # 停止现有的隧道
                self.stop_tcp_tunnel()
                
                # 启动TCP隧道
                if self.run_tcp_tunnel(server_addr, remote_port, 25565):
                    self.log("✓ TCP隧道启动成功")
                    self.log("使用说明：")
                    self.log("  1. TCP隧道已就绪")
                    self.log("  2. 在Minecraft中添加服务器")
                    self.log("  3. 服务器地址输入: 127.0.0.1:25565")
                    self.log("  4. 等待房主开启游戏")
                    
                    if self.copy_to_clipboard("127.0.0.1:25565"):
                        self.log("服务器地址已自动复制到剪贴板")
                    
                    self.log(f"\n隧道信息：")
                    self.log(f"   完整房间号: {full_room_code}")
                    self.log(f"   FRP节点: {node_name}")
                    self.log(f"   远程服务器: {server_addr}:{remote_port}")
                    self.log(f"   本地地址: 127.0.0.1:25565")
                    self.log(f"   连接方式: TCP隧道直连")
                    
                    self.log("\n注意：请不要关闭程序，否则隧道会断开")
                else:
                    self.log("✗ TCP隧道启动失败")
                    
            except Exception as e:
                self.log(f"✗ 加入房间过程中出现错误: {e}")
        
        threading.Thread(target=join_thread, daemon=True).start()

    def show_lobby(self):
        if not self.cloud_permission_granted:
            messagebox.showwarning("功能锁定", "云端许可验证失败，无法使用联机大厅功能")
            return
            
        lobby_window = tk.Toplevel(self.root)
        lobby_window.title("联机大厅 - 公开房间列表")
        lobby_window.geometry("1200x600")
        lobby_window.transient(self.root)
        lobby_window.configure(bg=BW_COLORS["background"])
        
        try:
            icon_path = "lyy.ico"
            if os.path.exists(icon_path):
                lobby_window.iconbitmap(icon_path)
        except:
            pass
        
        main_container = create_bw_frame(lobby_window)
        main_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        header_frame = tk.Frame(main_container, bg=BW_COLORS["card_bg"])
        header_frame.pack(fill=tk.X, padx=15, pady=10)
        
        title_text = "联机大厅 - 实时房间列表（30秒自动刷新）"
        
        tk.Label(header_frame, text=title_text, font=BW_FONTS["subtitle"],
                bg=BW_COLORS["card_bg"], fg=BW_COLORS["primary"]).pack(side=tk.LEFT)
        
        btn_frame = tk.Frame(header_frame, bg=BW_COLORS["card_bg"])
        btn_frame.pack(side=tk.RIGHT)
        
        self.refresh_btn = create_bw_button(btn_frame, "⟳ 手动刷新", lambda: self.refresh_rooms(lobby_window), "primary")
        self.refresh_btn.pack(side=tk.LEFT, padx=5)
        
        tip_frame = tk.Frame(main_container, bg=BW_COLORS["card_bg"])
        tip_frame.pack(fill=tk.X, padx=15, pady=5)
        
        tip_text = "提示: 点击房间右侧的'加入'按钮，自动启动TCP隧道并连接到该房间"
        tip_color = BW_COLORS["primary"]
        
        tk.Label(tip_frame, text=tip_text, font=BW_FONTS["small"], 
                fg=tip_color, wraplength=600, justify=tk.CENTER, bg=BW_COLORS["card_bg"]).pack()
        
        list_frame = create_bw_frame(main_container)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        
        columns = ("房间名", "版本", "完整房间号", "服务器地址", "描述", "房主", "状态", "操作")
        self.room_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)
        
        self.room_tree.column("房间名", width=120)
        self.room_tree.column("版本", width=80)
        self.room_tree.column("完整房间号", width=120)
        self.room_tree.column("服务器地址", width=150)
        self.room_tree.column("描述", width=150)
        self.room_tree.column("房主", width=100)
        self.room_tree.column("状态", width=80)
        self.room_tree.column("操作", width=80)
        
        for col in columns:
            self.room_tree.heading(col, text=col)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.room_tree.yview)
        self.room_tree.configure(yscrollcommand=scrollbar.set)
        
        self.room_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        status_frame = tk.Frame(main_container, bg=BW_COLORS["card_bg"])
        status_frame.pack(fill=tk.X, padx=15, pady=5)
        
        self.lobby_status = tk.Label(status_frame, text="正在加载房间列表...", font=BW_FONTS["small"],
                                   bg=BW_COLORS["card_bg"], fg=BW_COLORS["text_secondary"])
        self.lobby_status.pack(side=tk.LEFT)
        
        self.last_update_label = tk.Label(status_frame, text="", font=BW_FONTS["small"],
                                        bg=BW_COLORS["card_bg"], fg=BW_COLORS["text_secondary"])
        self.last_update_label.pack(side=tk.RIGHT)
        
        self.room_tree.bind("<ButtonRelease-1>", lambda e: self.on_room_click(e, lobby_window))
        self.refresh_rooms(lobby_window)
        self.start_auto_refresh(lobby_window)
        lobby_window.protocol("WM_DELETE_WINDOW", lambda: self.on_lobby_close(lobby_window))
        return lobby_window

    def start_auto_refresh(self, lobby_window):
        def auto_refresh():
            while hasattr(lobby_window, 'winfo_exists') and lobby_window.winfo_exists():
                time.sleep(30)
                if hasattr(lobby_window, 'winfo_exists') and lobby_window.winfo_exists():
                    self.refresh_rooms(lobby_window)
        
        threading.Thread(target=auto_refresh, daemon=True).start()

    def on_lobby_close(self, lobby_window):
        lobby_window.destroy()

    def refresh_rooms(self, lobby_window):
        if self.is_refreshing:
            return
            
        self.is_refreshing = True
        if self.refresh_btn:
            self.refresh_btn.config(state='disabled', text='⟳ 刷新中...')
        
        def refresh_thread():
            try:
                self.log("⟳ 正在获取房间列表...")
                response = self.http_request("GET")
                if response:
                    if response.get('success'):
                        self.current_rooms = response['data']['rooms']
                        self.update_room_list()
                        current_time = datetime.now().strftime("%H:%M:%S")
                        stats = response['data'].get('stats', {})
                        cleaned_count = stats.get('cleaned_rooms', 0)
                        
                        status_text = f"找到 {len(self.current_rooms)} 个活跃房间"
                        if cleaned_count > 0:
                            status_text += f" (已清理 {cleaned_count} 个过期房间)"
                        
                        self.lobby_status.config(text=status_text)
                        self.last_update_label.config(text=f"最后更新: {current_time}")
                    else:
                        self.lobby_status.config(text="获取房间列表失败")
                else:
                    self.lobby_status.config(text="获取房间列表失败：无响应")
            except Exception as e:
                self.lobby_status.config(text=f"刷新失败: {e}")
            finally:
                self.is_refreshing = False
                if hasattr(lobby_window, 'winfo_exists') and lobby_window.winfo_exists():
                    if self.refresh_btn:
                        self.refresh_btn.config(state='normal', text='⟳ 手动刷新')
        
        threading.Thread(target=refresh_thread, daemon=True).start()

    def update_room_list(self):
        for item in self.room_tree.get_children():
            self.room_tree.delete(item)
        
        for room in self.current_rooms:
            player_text = f"{room['player_count']}/{room['max_players']}"
            current_time = time.time()
            time_diff = current_time - room['last_update']
            if time_diff <= 60:
                status = "● 活跃"
            else:
                status = "○ 离线"
            
            full_room_code = f"{room['remote_port']}_{room['node_id']}"
            server_addr = f"{room.get('server_addr', '未知')}:{room.get('remote_port', '未知')}"
            
            join_button_text = "加入"
            join_button_state = "normal"
            
            item_id = self.room_tree.insert("", "end", values=(
                room['room_name'],
                room['game_version'],
                full_room_code,
                server_addr,
                room['description'][:20] + "..." if len(room['description']) > 20 else room['description'],
                room.get('host_player', '未知玩家'),
                status,
                join_button_text
            ), tags=(full_room_code, join_button_state))

    def on_room_click(self, event, lobby_window):
        item = self.room_tree.identify_row(event.y)
        column = self.room_tree.identify_column(event.x)
        
        if not item:
            return
        
        if column == "#8":  # 操作列
            tags = self.room_tree.item(item, "tags")
            if len(tags) > 1 and tags[1] == "disabled":
                return
            
            self.join_selected_room(lobby_window)

    def join_selected_room(self, lobby_window=None):
        selection = self.room_tree.selection()
        if not selection:
            if lobby_window:
                messagebox.showwarning("提示", "请先选择一个房间", parent=lobby_window)
            else:
                messagebox.showwarning("提示", "请先选择一个房间")
            return
        
        item = selection[0]
        full_room_code = self.room_tree.item(item, "tags")[0]
        
        # 直接从当前房间列表中获取房间信息，不需要查询云端
        room_info = None
        for room in self.current_rooms:
            current_full_room_code = f"{room['remote_port']}_{room['node_id']}"
            if current_full_room_code == full_room_code:
                room_info = room
                break
        
        if not room_info:
            if lobby_window:
                messagebox.showerror("错误", "房间信息获取失败", parent=lobby_window)
            else:
                messagebox.showerror("错误", "房间信息获取失败")
            return
        
        server_addr = room_info.get('server_addr')
        remote_port = room_info.get('remote_port')
        room_name = room_info.get('room_name', '未知房间')
        
        if lobby_window:
            confirm = messagebox.askyesno("确认加入", 
                                         f"是否加入房间：{room_name}\n完整房间号：{full_room_code}\n\n"
                                         f"服务器地址：{server_addr}:{remote_port}\n\n"
                                         f"注意：这将启动TCP隧道，将远程服务器映射到127.0.0.1:25565", 
                                         parent=lobby_window)
        else:
            confirm = messagebox.askyesno("确认加入", 
                                         f"是否加入房间：{room_name}\n完整房间号：{full_room_code}\n\n"
                                         f"服务器地址：{server_addr}:{remote_port}\n\n"
                                         f"注意：这将启动TCP隧道，将远程服务器映射到127.0.0.1:25565")
        
        if confirm:
            self.log(f"正在加入房间: {room_name} ({full_room_code})")
            self.auto_join_room_from_lobby(full_room_code, room_info)

    def run_frp_create(self):
        if not self.cloud_permission_granted:
            messagebox.showwarning("功能锁定", "云端许可验证失败，无法使用此功能")
            return
            
        self.clear_log()
        self.lock_buttons()
        
        def create_room():
            try:
                self.log("正在创建FRP联机房间...")
                self.log("正在检测Minecraft端口...")
                
                # 检测Minecraft端口（使用和IPv6联机一样的逻辑）
                mc_port = self.check_minecraft_ports()
                if not mc_port:
                    self.log("✗ 未检测到Minecraft服务器端口")
                    messagebox.showerror("错误", "未检测到Minecraft服务器运行\n\n请确保已在Minecraft中开启局域网游戏")
                    self.unlock_buttons()
                    return
                
                self.log(f"✓ 检测到Minecraft服务器在端口 {mc_port} 运行")
                
                self.log("正在选择最佳FRP节点...")
                best_node = self.find_best_frp_node()
                if not best_node:
                    self.log("✗ 无法找到可用的FRP节点")
                    messagebox.showerror("错误", "无法找到可用的FRP节点，请检查网络连接")
                    self.unlock_buttons()
                    return
                
                self.log(f"✓ 已选择节点: #{best_node['node_id']} - {best_node['name']}")
                
                # 生成房间信息 - 房间号格式：远程端口_FRP服务器号
                remote_port = self.generate_random_remote_port()
                full_room_code = f"{remote_port}_{best_node['node_id']}"
                proxy_name = f"mc_{remote_port}"
                
                self.log(f"✓ 生成完整房间号: {full_room_code}")
                self.log(f"✓ 本地Minecraft端口: {mc_port}")
                self.log(f"✓ 远程映射端口: {remote_port}")
                
                # 创建FRP配置文件
                if not self.create_frpc_config(best_node, proxy_name, mc_port, remote_port):
                    self.unlock_buttons()
                    return
                
                # 收集房间信息
                room_info = self.collect_room_info(remote_port, best_node['node_id'], full_room_code, 
                                                 best_node['server_addr'])
                
                self.is_frp_running = True
                
                if self.run_frp_command():
                    self.log("\n房间创建成功！")
                    self.log(f"完整房间号: {full_room_code}")
                    self.log(f"服务器地址: {best_node['server_addr']}:{remote_port}")
                    self.log(f"本地Minecraft端口: {mc_port}")
                    
                    if room_info:
                        room_info['full_room_code'] = full_room_code
                        
                        if room_info['is_public']:
                            self.log("✓ 房间已发布到联机大厅")
                            self.log("其他玩家可以在联机大厅看到并加入")
                            self.heartbeat_manager.submit_room_info(room_info)
                        else:
                            self.log("私有房间创建成功")
                            self.log("只有知道房间号的玩家才能加入")
                            self.log("请将房间号分享给朋友: " + full_room_code)
                    else:
                        self.log("房间未发布到联机大厅")
                    
                    if self.copy_to_clipboard(full_room_code):
                        self.log("完整房间号已自动复制到剪贴板")
                    
                    self.log("\n注意：请不要关闭FRP窗口，否则联机会断开")
                    
                    # 保存当前房间信息
                    self.current_room_code = full_room_code
                    self.current_node_id = best_node['node_id']
                    self.current_remote_port = remote_port
                else:
                    self.is_frp_running = False
                    self.log("✗ 房间创建失败")
                
                self.unlock_buttons()
                
            except Exception as e:
                self.is_frp_running = False
                self.log(f"✗ 创建房间过程中出现错误: {e}")
                self.unlock_buttons()

        threading.Thread(target=create_room, daemon=True).start()

    def run_frp_join(self):
        if not self.cloud_permission_granted:
            messagebox.showwarning("功能锁定", "云端许可验证失败，无法使用此功能")
            return
            
        self.clear_log()
        self.lock_buttons()
        
        input_window = tk.Toplevel(self.root)
        input_window.title("输入完整房间号")
        input_window.geometry("400x150")
        input_window.transient(self.root)
        input_window.grab_set()
        input_window.configure(bg=BW_COLORS["background"])
        
        try:
            icon_path = "lyy.ico"
            if os.path.exists(icon_path):
                input_window.iconbitmap(icon_path)
        except:
            pass
        
        main_container = create_bw_frame(input_window)
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(main_container, text="请输入完整房间号:", font=BW_FONTS["small"],
                bg=BW_COLORS["card_bg"]).pack(pady=10)
        
        room_entry = tk.Entry(main_container, width=30, font=BW_FONTS["small"])
        room_entry.pack(pady=5)
        
        def confirm_join():
            full_room_code = room_entry.get().strip()
            input_window.destroy()
            
            if not full_room_code:
                messagebox.showerror("错误", "房间号不能为空")
                self.unlock_buttons()
                return
            
            if '_' not in full_room_code:
                messagebox.showerror("错误", "房间号格式错误，请使用完整房间号（远程端口_FRP服务器号）")
                self.unlock_buttons()
                return
            
            room_parts = full_room_code.split('_')
            if len(room_parts) != 2:
                messagebox.showerror("错误", "房间号格式错误，请使用完整房间号（远程端口_FRP服务器号）")
                self.unlock_buttons()
                return
            
            remote_port_str = room_parts[0]
            node_id_str = room_parts[1]
            
            if not remote_port_str.isdigit() or not (10000 <= int(remote_port_str) <= 60000):
                messagebox.showerror("错误", "远程端口格式错误，必须是10000-60000的数字")
                self.unlock_buttons()
                return
            
            if not node_id_str.isdigit() or not (1 <= int(node_id_str) <= 1000):
                messagebox.showerror("错误", "FRP服务器号格式错误，必须是1-1000的数字")
                self.unlock_buttons()
                return
            
            self.log(f"正在加入房间: {full_room_code}")
            
            def join_thread():
                try:
                    # 从云端获取房间信息
                    room_info = self.get_room_info_from_cloud(full_room_code)
                    if not room_info:
                        self.log("✗ 无法获取房间信息，请检查房间号是否正确")
                        self.unlock_buttons()
                        return
                    
                    server_addr = room_info.get('server_addr')
                    remote_port = room_info.get('remote_port')
                    node_name = room_info.get('node_name')
                    
                    if not server_addr or not remote_port:
                        self.log("✗ 房间信息不完整")
                        self.unlock_buttons()
                        return
                    
                    self.log(f"✓ 获取到房间信息")
                    self.log(f"   完整房间号: {full_room_code}")
                    self.log(f"   FRP节点: {node_name}")
                    self.log(f"   服务器地址: {server_addr}:{remote_port}")
                    
                    # 停止现有的隧道
                    self.stop_tcp_tunnel()
                    
                    # 启动TCP隧道
                    if self.run_tcp_tunnel(server_addr, remote_port, 25565):
                        self.log("正在连接到房间！")
                        self.log("使用说明：")
                        self.log("  1. TCP隧道已就绪")
                        self.log("  2. 在Minecraft中添加服务器")
                        self.log("  3. 服务器地址输入: 127.0.0.1:25565")
                        self.log("  4. 等待朋友在Minecraft中开启游戏")
                        self.log(f"\n联机信息：")
                        self.log(f"   完整房间号: {full_room_code}")
                        self.log(f"   FRP节点: {node_name}")
                        self.log(f"   远程服务器: {server_addr}:{remote_port}")
                        self.log(f"   本地地址: 127.0.0.1:25565")
                        self.log(f"   连接方式: TCP隧道直连")
                        
                        if self.copy_to_clipboard("127.0.0.1:25565"):
                            self.log("服务器地址已自动复制到剪贴板")
                        
                        self.log("\n注意：请不要关闭程序，否则隧道会断开")
                    else:
                        self.log("✗ 连接房间失败")
                    
                    self.unlock_buttons()
                    
                except Exception as e:
                    self.log(f"✗ 加入房间过程中出现错误: {e}")
                    self.unlock_buttons()
            
            threading.Thread(target=join_thread, daemon=True).start()
        
        def cancel_join():
            input_window.destroy()
            self.unlock_buttons()
        
        btn_frame = tk.Frame(main_container, bg=BW_COLORS["card_bg"])
        btn_frame.pack(pady=10)
        
        confirm_btn = create_bw_button(btn_frame, "确认", confirm_join, "primary", width=10)
        confirm_btn.pack(side=tk.LEFT, padx=5)
        
        cancel_btn = create_bw_button(btn_frame, "取消", cancel_join, "secondary", width=10)
        cancel_btn.pack(side=tk.LEFT, padx=5)
        
        input_window.bind('<Return>', lambda e: confirm_join())
        room_entry.focus()

    def find_best_frp_node(self):
        """根据延迟选择最佳FRP节点"""
        self.log("正在获取FRP节点列表...")
        nodes = self.get_frp_nodes()
        
        if not nodes:
            self.log("✗ 无法获取FRP节点列表")
            return None
        
        # 测试所有节点的延迟
        nodes_with_delay = self.test_nodes_delay(nodes)
        
        if not nodes_with_delay:
            self.log("⚠ 所有节点都无法连接，使用第一个节点")
            return nodes[0]
        
        # 选择延迟最低的节点
        best_node = nodes_with_delay[0]
        best_delay = best_node['delay']
        
        self.log(f"✓ 选择最佳节点: #{best_node['node_id']} - {best_node['name']}，延迟: {best_delay}ms")
        
        # 显示前3个最佳节点
        self.log("延迟最低的前3个节点:")
        for i, node in enumerate(nodes_with_delay[:3]):
            self.log(f"  {i+1}. #{node['node_id']} - {node['name']} - 延迟: {node['delay']}ms")
        
        return best_node

    def ping_node(self, server_addr, server_port):
        """测试节点延迟"""
        try:
            start_time = time.time()
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            result = sock.connect_ex((server_addr, server_port))
            end_time = time.time()
            sock.close()
            
            if result == 0:
                delay = int((end_time - start_time) * 1000)
                return delay
            else:
                return None
        except:
            return None

    def test_nodes_delay(self, nodes):
        """测试多个节点的延迟"""
        self.log(f"正在测试 {len(nodes)} 个节点的延迟...")
        
        nodes_with_delay = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            future_to_node = {
                executor.submit(self.ping_node, node['server_addr'], node['server_port']): node 
                for node in nodes
            }
            
            for future in concurrent.futures.as_completed(future_to_node):
                node = future_to_node[future]
                try:
                    delay = future.result()
                    if delay is not None:
                        node['delay'] = delay
                        nodes_with_delay.append(node)
                        self.log(f"节点 #{node['node_id']} - {node['name']} 延迟: {delay}ms")
                    else:
                        self.log(f"节点 #{node['node_id']} - {node['name']} 无法连接")
                except Exception as e:
                    self.log(f"节点 #{node['node_id']} - {node['name']} 测试失败: {e}")
        
        # 按延迟排序
        nodes_with_delay.sort(key=lambda x: x.get('delay', float('inf')))
        return nodes_with_delay

    def run_ipv6_mode(self):
        if not self.cloud_permission_granted:
            messagebox.showwarning("功能锁定", "云端许可验证失败，无法使用此功能")
            return
            
        self.clear_log()
        self.lock_buttons()
        self.log("正在检测IPv6网络配置...")
        self.log("正在获取IPv6地址，请稍等...")
        
        def detect_ipv6():
            try:
                self.ipv6 = self.get_ipv6_powershell()
                
                if not self.ipv6:
                    self.ipv6 = self.get_ipv6_ipconfig()
                
                if not self.ipv6:
                    self.log("✗ 未检测到公网IPv6地址")
                    messagebox.showerror("错误", "未检测到公网IPv6地址，请联系QQ2232908600获取帮助")
                    self.unlock_buttons()
                    return
                
                self.log(f"✓ 获取到IPv6地址: {self.ipv6}")
                
                self.log("正在检测Minecraft联机端口...")
                self.mc_port = self.check_minecraft_ports()
                
                if not self.mc_port:
                    self.mc_port = self.manual_port_selection()
                
                if not self.mc_port:
                    self.log("✗ 未检测到有效的Minecraft联机端口")
                    self.log("")
                    self.log("可能的原因：")
                    self.log("1. 未开启Minecraft局域网游戏")
                    self.log("2. 防火墙阻止了端口访问")
                    self.log("3. Minecraft服务未正常启动")
                    self.log("")
                    self.log("请先进入Minecraft单人游戏，开启局域网游戏：")
                    self.log("1. 进入单人游戏世界")
                    self.log("2. 按ESC键打开游戏菜单")
                    self.log("3. 点击'对局域网开放'")
                    self.log("4. 设置游戏模式（可选）")
                    self.log("5. 点击'创建局域网世界'")
                    self.log("6. 记下显示的端口号")
                    messagebox.showerror("错误", "未检测到Minecraft联机端口，请确保已在Minecraft中开启局域网游戏")
                    self.unlock_buttons()
                    return
                
                self.log(f"✓ 验证通过！将使用端口 {self.mc_port} 进行联机")
                
                mc_address = f"[{self.ipv6}]:{self.mc_port}"
                
                self.log("=" * 50)
                self.log("Minecraft联机地址已生成！")
                self.log(mc_address)
                self.log("=" * 50)
                
                if self.copy_to_clipboard(mc_address):
                    self.log("地址已自动复制到剪贴板！")
                self.log("")
                
                self.log("使用说明：")
                self.log("1. 确保您已在Minecraft中开启局域网游戏")
                self.log("2. 您的朋友需要在Minecraft多人游戏中输入此地址")
                self.log("3. 双方都需要支持IPv6网络")
                self.log("")
                
                self.log(f"游戏联机地址： [{self.ipv6}]:{self.mc_port}")
                self.log("")
                self.log("常见问题：")
                self.log("- 如果无法连接，请检查防火墙设置")
                self.log("- 确保端口号与Minecraft中显示的一致")
                self.log("- '登入失败:无效会话'：安装联机模组关闭正版验证")
                self.log("")
                
                self.log("如果使用本脚本联机时遇到问题，请联系：")
                self.log("QQ：2232908600")
                self.log("微信：liuyvetong")
                
                self.unlock_buttons()
                
            except Exception as e:
                self.log(f"✗ IPv6检测过程中出现错误: {e}")
                self.unlock_buttons()
        
        threading.Thread(target=detect_ipv6, daemon=True).start()

    def create_port_mapping(self, source_port, target_port=25565):
        try:
            command = f'netsh interface portproxy add v4tov4 listenport={target_port} listenaddress=0.0.0.0 connectport={source_port} connectaddress=127.0.0.1'
            
            self.log(f"创建端口映射: {source_port} -> {target_port}")
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.log("✓ 端口映射创建成功")
                
                firewall_command = f'netsh advfirewall firewall add rule name="Minecraft Port {target_port}" dir=in action=allow protocol=TCP localport={target_port}'
                subprocess.run(firewall_command, shell=True, capture_output=True)
                self.log("✓ 防火墙规则添加成功")
                
                return True
            else:
                self.log(f"✗ 端口映射创建失败: {result.stderr}")
                return False
        except Exception as e:
            self.log(f"✗ 创建端口映射时出错: {e}")
            return False

    def remove_port_mapping(self, target_port=25565):
        try:
            command = f'netsh interface portproxy delete v4tov4 listenport={target_port} listenaddress=0.0.0.0'
            subprocess.run(command, shell=True, capture_output=True)
            
            firewall_command = f'netsh advfirewall firewall delete rule name="Minecraft Port {target_port}"'
            subprocess.run(firewall_command, shell=True, capture_output=True)
            
            self.log(f"✓ 已移除端口 {target_port} 的映射规则")
            return True
        except Exception as e:
            self.log(f"✗ 移除端口映射时出错: {e}")
            return False

    def run_port_mapping(self):
        if not self.cloud_permission_granted:
            messagebox.showwarning("功能锁定", "云端许可验证失败，无法使用此功能")
            return
        
        self.clear_log()
        self.lock_buttons()
        
        input_window = tk.Toplevel(self.root)
        input_window.title("端口映射设置")
        input_window.geometry("400x200")
        input_window.transient(self.root)
        input_window.grab_set()
        input_window.configure(bg=BW_COLORS["background"])
        
        try:
            icon_path = "lyy.ico"
            if os.path.exists(icon_path):
                input_window.iconbitmap(icon_path)
        except:
            pass
        
        main_container = create_bw_frame(input_window)
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(main_container, text="请输入要映射的源端口:", font=BW_FONTS["small"],
                bg=BW_COLORS["card_bg"]).pack(pady=10)
        
        port_entry = tk.Entry(main_container, width=20, font=BW_FONTS["small"])
        port_entry.pack(pady=5)
        
        tk.Label(main_container, text="目标端口将固定为25565", font=BW_FONTS["small"],
                bg=BW_COLORS["card_bg"]).pack(pady=5)
        
        def confirm_mapping():
            port_str = port_entry.get().strip()
            input_window.destroy()
            
            if not port_str:
                messagebox.showerror("错误", "端口号不能为空")
                self.unlock_buttons()
                return
            
            try:
                source_port = int(port_str)
                if not (1 <= source_port <= 65535):
                    messagebox.showerror("错误", "端口号必须在1-65535范围内")
                    self.unlock_buttons()
                    return
            except ValueError:
                messagebox.showerror("错误", "请输入有效的端口号")
                self.unlock_buttons()
                return
            
            def mapping_thread():
                try:
                    self.log(f"正在设置端口映射: {source_port} -> 25565")
                    
                    if not self.is_port_occupied(source_port):
                        self.log(f"✗ 源端口 {source_port} 未被占用，请确保Minecraft服务正在运行")
                        messagebox.showerror("错误", f"源端口 {source_port} 未被占用，请确保Minecraft服务正在运行")
                        self.unlock_buttons()
                        return
                    
                    self.log(f"✓ 检测到源端口 {source_port} 正在运行")
                    
                    if self.is_port_occupied(25565):
                        self.log("⚠ 目标端口25565已被占用，正在清理...")
                        self.remove_port_mapping(25565)
                    
                    if self.create_port_mapping(source_port, 25565):
                        self.mapped_port = source_port
                        self.is_port_mapping_active = True
                        
                        self.log("\n端口映射设置成功！")
                        self.log(f"映射规则: {source_port} -> 25565")
                        self.log("现在可以使用25565端口连接Minecraft服务器")
                        self.log("注意：程序退出时将自动移除映射规则")
                        
                        self.port_map_btn.config(text="端口映射已激活 (点击关闭)", 
                                               command=self.stop_port_mapping)
                    else:
                        self.log("✗ 端口映射设置失败")
                    
                    self.unlock_buttons()
                    
                except Exception as e:
                    self.log(f"✗ 端口映射过程中出现错误: {e}")
                    self.unlock_buttons()
            
            threading.Thread(target=mapping_thread, daemon=True).start()
        
        def cancel_mapping():
            input_window.destroy()
            self.unlock_buttons()
        
        btn_frame = tk.Frame(main_container, bg=BW_COLORS["card_bg"])
        btn_frame.pack(pady=20)
        
        confirm_btn = create_bw_button(btn_frame, "确认", confirm_mapping, "primary", width=10)
        confirm_btn.pack(side=tk.LEFT, padx=5)
        
        cancel_btn = create_bw_button(btn_frame, "取消", cancel_mapping, "secondary", width=10)
        cancel_btn.pack(side=tk.LEFT, padx=5)
        
        input_window.bind('<Return>', lambda e: confirm_mapping())
        port_entry.focus()

    def stop_port_mapping(self):
        if self.is_port_mapping_active:
            self.remove_port_mapping(25565)
            self.is_port_mapping_active = False
            self.mapped_port = None
            
            self.log("✓ 端口映射已停止")
            self.port_map_btn.config(text="将其他端口映射至25565", 
                                   command=self.run_port_mapping)
        else:
            self.log("⚠ 没有激活的端口映射")

    def on_closing(self):
        self.stop_room_heartbeat()
        
        if self.is_frp_running or self.is_frp_already_running():
            self.log("正在停止FRP进程...")
            self.cleanup_frp_process()
        
        if self.is_port_mapping_active:
            self.remove_port_mapping(25565)
            self.log("✓ 已自动清理端口映射规则")
        
        # 停止TCP隧道
        self.stop_tcp_tunnel()
        
        self.root.quit()

def start_cloud_monitor(app_instance):
    def monitor_loop():
        while True:
            try:
                time.sleep(30)
                if not check_cloud_permission():
                    app_instance.root.after(0, lambda: show_cloud_warning_and_lock(app_instance))
            except Exception as e:
                print(f"云端监控检查失败: {e}")
                app_instance.root.after(0, lambda: lock_all_buttons(app_instance))
    
    monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
    monitor_thread.start()
    print("云端许可监控已启动")

def show_cloud_warning_and_lock(app_instance):
    if hasattr(app_instance, '_cloud_warning_shown') and app_instance._cloud_warning_shown:
        return
        
    app_instance._cloud_warning_shown = True
    lock_all_buttons(app_instance)
    
    warning_window = tk.Toplevel(app_instance.root)
    warning_window.title("⚠ 软件许可警告")
    warning_window.geometry("500x560")
    warning_window.resizable(False, False)
    warning_window.configure(bg=BW_COLORS["background"])
    warning_window.transient(app_instance.root)
    warning_window.attributes('-topmost', True)
    
    try:
        icon_path = "lyy.ico"
        if os.path.exists(icon_path):
            warning_window.iconbitmap(icon_path)
    except:
        pass
    
    def on_warning_close():
        app_instance._cloud_warning_shown = False
        warning_window.destroy()
    
    warning_window.protocol("WM_DELETE_WINDOW", on_warning_close)
    
    main_container = create_bw_frame(warning_window)
    main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
    
    header_frame = tk.Frame(main_container, bg=BW_COLORS["card_bg"])
    header_frame.pack(fill=tk.X, padx=20, pady=15)
    
    warning_icon = tk.Label(
        header_frame,
        text="⚠",
        font=("Arial", 24),
        bg=BW_COLORS["card_bg"],
        fg=BW_COLORS["warning"]
    )
    warning_icon.pack(side=tk.LEFT, padx=(0, 10))
    
    title_label = tk.Label(
        header_frame,
        text="软件许可警告",
        font=BW_FONTS["title"],
        bg=BW_COLORS["card_bg"],
        fg=BW_COLORS["warning"]
    )
    title_label.pack(side=tk.LEFT)
    
    content_frame = create_bw_frame(main_container)
    content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
    
    warning_text = """
检测到当前软件使用许可可能存在问题。

可能的原因：
• 软件版本过旧，请更新到最新版本
• 服务器维护或升级期间
• 网络连接问题
• 软件使用权限受限

当前状态：
• 软件功能已被锁定
• 所有按钮已禁用
• 需要重新验证许可后才能继续使用

请选择以下操作：
"""
    
    text_widget = scrolledtext.ScrolledText(
        content_frame,
        width=50,
        height=15,
        font=BW_FONTS["normal"],
        wrap=tk.WORD,
        bg=BW_COLORS["light"],
        fg=BW_COLORS["text_primary"],
        relief="flat",
        bd=0,
        padx=10,
        pady=10
    )
    text_widget.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    text_widget.insert(tk.END, warning_text)
    text_widget.config(state=tk.DISABLED)
    
    button_frame = tk.Frame(main_container, bg=BW_COLORS["card_bg"])
    button_frame.pack(fill=tk.X, padx=20, pady=15)
    
    def refresh_check():
        if check_cloud_permission():
            messagebox.showinfo("检查通过", "✓ 软件使用许可已恢复！\n\n软件功能已重新启用。", parent=warning_window)
            unlock_all_buttons(app_instance)
            on_warning_close()
        else:
            messagebox.showwarning("检查失败", "⚠ 软件使用许可仍未恢复。\n\n所有功能保持锁定状态。", parent=warning_window)
    
    def exit_software():
        app_instance.on_closing()
        app_instance.root.quit()
    
    refresh_btn = create_bw_button(button_frame, "⟳ 重新验证许可", refresh_check, "primary", width=18)
    refresh_btn.pack(side=tk.LEFT, padx=5)
    
    exit_btn = create_bw_button(button_frame, "✗ 退出软件", exit_software, "danger", width=15)
    exit_btn.pack(side=tk.RIGHT, padx=5)
    
    warning_window.update_idletasks()
    x = (warning_window.winfo_screenwidth() - warning_window.winfo_width()) // 2
    y = (warning_window.winfo_screenheight() - warning_window.winfo_height()) // 2
    warning_window.geometry(f"+{x}+{y}")

def lock_all_buttons(app_instance):
    buttons = [
        'ipv6_btn', 'frp_create_btn', 'frp_join_btn', 
        'port_map_btn', 'lobby_btn', 'stop_btn',
        'clear_btn', 'help_btn'
    ]
    
    for btn_name in buttons:
        if hasattr(app_instance, btn_name):
            btn = getattr(app_instance, btn_name)
            btn.config(state='disabled', bg=BW_COLORS["text_secondary"])
    
    if hasattr(app_instance, 'status_text'):
        app_instance.status_text.insert(tk.END, "■ 软件功能已锁定 - 云端许可验证失败\n")
        app_instance.status_text.see(tk.END)
    
    app_instance.root.update()

def unlock_all_buttons(app_instance):
    buttons_config = {
        'ipv6_btn': 'primary',
        'frp_create_btn': 'secondary',
        'frp_join_btn': 'secondary',
        'port_map_btn': 'primary', 
        'lobby_btn': 'primary',
        'stop_btn': 'danger',
        'clear_btn': 'secondary',
        'help_btn': 'primary'
    }
    
    for btn_name, style in buttons_config.items():
        if hasattr(app_instance, btn_name):
            btn = getattr(app_instance, btn_name)
            btn.config(state='normal', bg=BW_COLORS[style])
    
    if hasattr(app_instance, 'status_text'):
        app_instance.status_text.insert(tk.END, "✓ 软件功能已解锁 - 云端许可验证通过\n")
        app_instance.status_text.see(tk.END)
    
    app_instance.root.update()

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def request_uac():
    if is_admin():
        return True
        
    try:
        if getattr(sys, 'frozen', False):
            current_file = sys.executable
        else:
            current_file = sys.argv[0]
        
        result = ctypes.windll.shell32.ShellExecuteW(
            None, 
            "runas", 
            current_file, 
            " ".join(sys.argv[1:]), 
            None, 
            1
        )
        
        if result > 32:
            return True
        else:
            print("请求管理员权限失败")
            return False
    except Exception as e:
        print(f"请求管理员权限失败: {e}")
        return False

def main():
    if platform.system() != "Windows":
        messagebox.showerror("错误", "此程序目前仅支持Windows系统")
        return
    
    # 第一步：显示免责声明
    if not show_disclaimer():
        return
    
    # 第二步：同时启动云端许可检查和公告检查
    print("开始并行检查：云端许可和公告...")


    # 启动云端许可检查窗口
    print("启动云端许可检查窗口...")
    check_window, check_result = show_cloud_permission_check()
    
    # 同时检查公告（不阻塞许可检查）
    def check_announcements_thread():
        print("启动公告检查线程...")
        announcements_info = check_announcements()
        return announcements_info
    
    # 启动公告检查线程
    announcement_info_result = [None]
    announcement_thread = threading.Thread(
        target=lambda: announcement_info_result.__setitem__(0, check_announcements_thread()),
        daemon=True
    )
    announcement_thread.start()
    
    # 等待云端许可检查窗口完成
    check_window.mainloop()
    permission_result = check_result[0]
    check_window.destroy()
    
    # 等待公告检查线程完成（最多等待5秒）
    announcement_thread.join(timeout=5)
    
    # 处理云端许可检查结果
    if permission_result is None or not permission_result:
        print("云端许可检查失败或被取消")
        messagebox.showinfo("退出", "程序即将退出。")
        return
    
    print("✓ 云端许可检查通过")
    
    # 检查公告结果
    announcements_info = announcement_info_result[0]
    
    # 第四步：创建主程序窗口
    print("创建主程序窗口...")
    root = tk.Tk()
    app = LMFP_MinecraftTool(root)
    app.enable_all_buttons()
    
    # 第五步：启动云端许可监控
    print("启动云端许可监控...")
    start_cloud_monitor(app)
    
    # 第六步：如果有公告，显示公告窗口
    if announcements_info and announcements_info.get('has_new_announcements'):
        print(f"显示公告窗口，发现 {len(announcements_info['announcements'])} 条新公告")
        # 在主窗口显示后显示公告窗口
        root.after(500, lambda: show_announcements_window(announcements_info))
    else:
        print("没有新公告")
    
    root.mainloop()

if __name__ == "__main__":
    main()
