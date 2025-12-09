import os
import json
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import time
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime
import queue
import hashlib

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
    
    def on_enter(e):
        if btn['state'] == 'normal':
            btn['bg'] = BW_COLORS["accent"]
        
    def on_leave(e):
        if btn['state'] == 'normal':
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

class PublicChatRoom:
    def __init__(self, root):
        self.root = root
        self.root.title("公共聊天室 v1.0 - 实时在线聊天")
        self.root.geometry("1000x700")
        self.root.resizable(True, True)
        self.root.configure(bg=BW_COLORS["background"])
        
        # API配置
        self.api_base = "https://lytapi.asia/public_chat/api"  # 您的服务器地址
        self.user_token = None
        self.current_user = None
        
        # 聊天相关
        self.chat_active = False
        self.last_message_id = 0
        self.displayed_message_hashes = set()  # 用于跟踪已显示的消息
        self.pending_messages = []  # 待发送的消息队列
        self.history_loaded = False  # 历史记录是否已加载
        
        # 在线用户列表
        self.online_users = []
        
        # 注册时的临时信息
        self.pending_email = None
        self.pending_password = None
        
        # 线程管理
        self.thread_queue = queue.Queue()
        
        # 重试机制
        self.retry_count = {}
        self.max_retries = 3
        
        # 初始化界面
        self.create_ui()
        
        # 处理线程队列
        self.process_thread_queue()
        
        # 自动检查登录状态
        self.check_auto_login()
        
    def get_message_hash(self, message):
        """生成消息的唯一哈希"""
        if isinstance(message, dict):
            content = f"{message.get('id', 0)}_{message.get('sender', '')}_{message.get('content', '')}_{message.get('timestamp', 0)}"
        else:
            content = str(message)
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def process_thread_queue(self):
        """处理线程队列中的结果"""
        try:
            while True:
                # 非阻塞地从队列中获取结果
                item = self.thread_queue.get_nowait()
                if callable(item):
                    # 如果是函数，直接执行
                    self.root.after(0, item)
                elif isinstance(item, tuple) and len(item) == 2:
                    # 如果是(回调函数, 参数)元组
                    callback, args = item
                    if callable(callback):
                        if args:
                            self.root.after(0, callback, *args)
                        else:
                            self.root.after(0, callback)
        except queue.Empty:
            pass
        finally:
            # 每100ms检查一次队列
            self.root.after(100, self.process_thread_queue)
    
    def run_in_thread(self, func, callback=None, *callback_args):
        """在后台线程中运行函数"""
        def thread_worker():
            try:
                result = func()
                if callback:
                    # 将回调放入队列
                    if callback_args:
                        self.thread_queue.put((callback, (result,) + callback_args))
                    else:
                        self.thread_queue.put((callback, (result,)))
            except Exception as e:
                if callback:
                    self.thread_queue.put((callback, (None, str(e))))
        
        thread = threading.Thread(target=thread_worker, daemon=True)
        thread.start()
    
    def create_ui(self):
        """创建主界面"""
        # 顶部标题栏
        header_frame = create_bw_frame(self.root)
        header_frame.pack(fill=tk.X, padx=15, pady=15)
        
        title_container = tk.Frame(header_frame, bg=BW_COLORS["card_bg"])
        title_container.pack(fill=tk.X, padx=20, pady=15)
        
        title_label = tk.Label(
            title_container,
            text="公共聊天室 - 实时在线聊天平台",
            font=BW_FONTS["title"],
            bg=BW_COLORS["card_bg"],
            fg=BW_COLORS["primary"]
        )
        title_label.pack(side=tk.LEFT)
        
        self.user_status_label = tk.Label(
            title_container,
            text="未登录",
            font=BW_FONTS["small"],
            bg=BW_COLORS["card_bg"],
            fg=BW_COLORS["warning"]
        )
        self.user_status_label.pack(side=tk.RIGHT, padx=10)
        
        # 主容器（左右分割）
        main_container = tk.Frame(self.root, bg=BW_COLORS["background"])
        main_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        # 左侧功能区
        left_frame = create_bw_frame(main_container)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left_frame.config(width=300)
        
        # 用户管理区域
        user_section = tk.Frame(left_frame, bg=BW_COLORS["card_bg"])
        user_section.pack(fill=tk.X, padx=15, pady=15)
        
        tk.Label(
            user_section,
            text="用户管理",
            font=BW_FONTS["subtitle"],
            bg=BW_COLORS["card_bg"],
            fg=BW_COLORS["primary"]
        ).pack(anchor="w", pady=(0, 10))
        
        self.login_btn = create_bw_button(
            user_section,
            "登录账号",
            self.show_login,
            "primary"
        )
        self.login_btn.pack(fill=tk.X, pady=5)
        
        self.register_btn = create_bw_button(
            user_section,
            "注册账号",
            self.show_register,
            "secondary"
        )
        self.register_btn.pack(fill=tk.X, pady=5)
        
        self.logout_btn = create_bw_button(
            user_section,
            "退出登录",
            self.logout,
            "danger"
        )
        self.logout_btn.pack(fill=tk.X, pady=5)
        self.logout_btn.config(state='disabled')
        
        # 在线用户区域
        online_section = tk.Frame(left_frame, bg=BW_COLORS["card_bg"])
        online_section.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        tk.Label(
            online_section,
            text="在线用户",
            font=BW_FONTS["subtitle"],
            bg=BW_COLORS["card_bg"],
            fg=BW_COLORS["primary"]
        ).pack(anchor="w", pady=(0, 10))
        
        # 在线用户列表
        self.online_listbox = tk.Listbox(
            online_section,
            bg=BW_COLORS["light"],
            fg=BW_COLORS["text_primary"],
            font=BW_FONTS["normal"],
            relief="flat",
            bd=1,
            highlightbackground=BW_COLORS["border"]
        )
        self.online_listbox.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 刷新在线用户按钮
        self.refresh_online_btn = create_bw_button(
            online_section,
            "刷新在线列表",
            self.refresh_online_users,
            "primary"
        )
        self.refresh_online_btn.pack(fill=tk.X)
        
        # 右侧聊天区
        right_frame = create_bw_frame(main_container)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # 聊天标题
        chat_header = tk.Frame(right_frame, bg=BW_COLORS["card_bg"])
        chat_header.pack(fill=tk.X, padx=15, pady=15)
        
        self.chat_title = tk.Label(
            chat_header,
            text="公共聊天室 - 所有人都在这里聊天",
            font=BW_FONTS["subtitle"],
            bg=BW_COLORS["card_bg"],
            fg=BW_COLORS["primary"]
        )
        self.chat_title.pack(side=tk.LEFT)
        
        self.online_count_label = tk.Label(
            chat_header,
            text="在线: 0",
            font=BW_FONTS["small"],
            bg=BW_COLORS["card_bg"],
            fg=BW_COLORS["success"]
        )
        self.online_count_label.pack(side=tk.RIGHT, padx=10)
        
        # 聊天消息区域
        chat_frame = create_bw_frame(right_frame)
        chat_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        self.chat_text = scrolledtext.ScrolledText(
            chat_frame,
            wrap=tk.WORD,
            font=BW_FONTS["normal"],
            bg=BW_COLORS["light"],
            fg=BW_COLORS["text_primary"],
            relief="flat",
            bd=0,
            padx=10,
            pady=10
        )
        self.chat_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.chat_text.config(state=tk.DISABLED)
        
        # 历史记录加载状态标签
        self.history_status_label = tk.Label(
            chat_frame,
            text="正在加载历史聊天记录...",
            font=BW_FONTS["small"],
            bg=BW_COLORS["light"],
            fg=BW_COLORS["warning"]
        )
        self.history_status_label.pack(pady=5)
        
        # 消息输入区域
        input_frame = tk.Frame(right_frame, bg=BW_COLORS["card_bg"])
        input_frame.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        self.message_entry = tk.Entry(
            input_frame,
            font=BW_FONTS["normal"],
            bg=BW_COLORS["light"],
            fg=BW_COLORS["text_primary"],
            relief="flat",
            bd=1,
            highlightbackground=BW_COLORS["border"],
            highlightthickness=1
        )
        self.message_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.message_entry.bind("<Return>", lambda e: self.send_message())
        
        self.send_btn = create_bw_button(
            input_frame,
            "发送",
            self.send_message,
            "primary"
        )
        self.send_btn.pack(side=tk.RIGHT)
        
        # 状态栏
        status_frame = tk.Frame(self.root, bg=BW_COLORS["background"])
        status_frame.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        self.status_label = tk.Label(
            status_frame,
            text="就绪",
            font=BW_FONTS["small"],
            bg=BW_COLORS["background"],
            fg=BW_COLORS["text_secondary"]
        )
        self.status_label.pack(side=tk.LEFT)
        
        # 启动聊天消息自动刷新
        self.auto_refresh_messages()
        self.auto_refresh_online_users()
    
    def check_auto_login(self):
        """检查自动登录"""
        try:
            if os.path.exists("user_session.json"):
                with open("user_session.json", "r", encoding="utf-8") as f:
                    session = json.load(f)
                    # 在后台线程中验证token
                    def verify_task():
                        return self.verify_token(session.get("token"))
                    
                    self.run_in_thread(
                        verify_task,
                        self.on_auto_login_checked,
                        session
                    )
        except Exception as e:
            self.log(f"自动登录失败: {e}")
    
    def on_auto_login_checked(self, token_valid, session):
        """自动登录检查完成后的回调"""
        if token_valid:
            self.user_token = session["token"]
            self.current_user = session["username"]
            self.update_login_state()
            self.log("✓ 自动登录成功")
            self.refresh_online_users()
            self.start_chat_connection()
            # 登录成功后加载历史记录
            self.load_chat_history()
        else:
            self.log("自动登录失败: Token无效", is_error=True)
    
    def load_chat_history(self):
        """加载历史聊天记录"""
        if not self.current_user:
            return
        
        self.log("正在加载历史聊天记录...")
        self.lock_message_input()  # 锁定发送功能
        
        def load_history_task():
            return self.api_get_messages(0)  # 从第一条消息开始获取
        
        def on_history_complete(result):
            if isinstance(result, tuple) and len(result) >= 2:
                success = result[0]
                messages = result[1] if success else []
            else:
                success = False
                messages = []
            
            if success and messages:
                # 按时间排序消息
                messages.sort(key=lambda x: x.get('id', 0))
                
                # 显示历史消息
                for msg in messages:
                    msg_hash = self.get_message_hash(msg)
                    if msg_hash in self.displayed_message_hashes:
                        continue
                    
                    self.display_message(msg)
                    self.displayed_message_hashes.add(msg_hash)
                    
                    # 更新最后消息ID
                    if msg['id'] > self.last_message_id:
                        self.last_message_id = msg['id']
                
                self.history_loaded = True
                self.history_status_label.config(text=f"已加载 {len(messages)} 条历史记录", fg=BW_COLORS["success"])
                self.log(f"✓ 历史记录加载完成，共 {len(messages)} 条消息")
                self.unlock_message_input()  # 解锁发送功能
            else:
                self.history_status_label.config(text="历史记录加载失败", fg=BW_COLORS["danger"])
                self.log("✗ 历史记录加载失败", is_error=True)
                # 即使加载失败也解锁发送功能，但显示警告
                self.unlock_message_input()
                self.history_status_label.after(3000, lambda: self.history_status_label.pack_forget())
        
        self.run_in_thread(load_history_task, on_history_complete)
    
    def lock_message_input(self):
        """锁定消息输入和发送功能"""
        self.message_entry.config(state='disabled')
        self.send_btn.config(state='disabled')
        self.history_status_label.config(text="正在加载历史聊天记录...", fg=BW_COLORS["warning"])
        self.history_status_label.pack(pady=5)
        self.update_status("正在加载历史记录...")
    
    def unlock_message_input(self):
        """解锁消息输入和发送功能"""
        if self.current_user and self.history_loaded:
            self.message_entry.config(state='normal')
            self.send_btn.config(state='normal')
            self.update_status("就绪")
            # 3秒后隐藏状态标签
            self.root.after(3000, lambda: self.history_status_label.pack_forget())
    
    def save_session(self):
        """保存会话信息"""
        if self.user_token and self.current_user:
            session = {
                "token": self.user_token,
                "username": self.current_user,
                "timestamp": int(time.time())
            }
            try:
                with open("user_session.json", "w", encoding="utf-8") as f:
                    json.dump(session, f, ensure_ascii=False)
            except:
                pass
    
    def clear_session(self):
        """清除会话信息"""
        try:
            if os.path.exists("user_session.json"):
                os.remove("user_session.json")
        except:
            pass
    
    def log(self, message, is_error=False):
        """记录日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        if is_error:
            formatted_message = f"[{timestamp}] ✗ {message}"
        else:
            formatted_message = f"[{timestamp}] {message}"
        
        self.chat_text.config(state=tk.NORMAL)
        self.chat_text.insert(tk.END, formatted_message + "\n")
        self.chat_text.see(tk.END)
        self.chat_text.config(state=tk.DISABLED)
    
    def update_status(self, message):
        """更新状态栏"""
        self.status_label.config(text=message)
    
    def update_login_state(self):
        """更新登录状态"""
        if self.current_user:
            self.user_status_label.config(text=f"已登录: {self.current_user}", fg=BW_COLORS["success"])
            self.login_btn.config(state='disabled')
            self.register_btn.config(state='disabled')
            self.logout_btn.config(state='normal')
            self.refresh_online_btn.config(state='normal')
            
            # 只有在历史记录加载完成后才解锁消息输入
            if self.history_loaded:
                self.message_entry.config(state='normal')
                self.send_btn.config(state='normal')
            else:
                self.message_entry.config(state='disabled')
                self.send_btn.config(state='disabled')
                self.history_status_label.config(text="正在加载历史聊天记录...", fg=BW_COLORS["warning"])
                self.history_status_label.pack(pady=5)
        else:
            self.user_status_label.config(text="未登录", fg=BW_COLORS["warning"])
            self.login_btn.config(state='normal')
            self.register_btn.config(state='normal')
            self.logout_btn.config(state='disabled')
            self.message_entry.config(state='disabled')
            self.send_btn.config(state='disabled')
            self.refresh_online_btn.config(state='disabled')
            self.history_loaded = False
            self.history_status_label.pack_forget()
    
    def show_login(self):
        """显示登录窗口"""
        login_window = tk.Toplevel(self.root)
        login_window.title("登录账号")
        login_window.geometry("400x300")
        login_window.resizable(False, False)
        login_window.configure(bg=BW_COLORS["background"])
        login_window.transient(self.root)
        login_window.grab_set()
        
        main_container = create_bw_frame(login_window)
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(
            main_container,
            text="登录账号",
            font=BW_FONTS["subtitle"],
            bg=BW_COLORS["card_bg"],
            fg=BW_COLORS["primary"]
        ).pack(pady=10)
        
        form_frame = tk.Frame(main_container, bg=BW_COLORS["card_bg"])
        form_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(
            form_frame,
            text="QQ邮箱:",
            font=BW_FONTS["normal"],
            bg=BW_COLORS["card_bg"]
        ).grid(row=0, column=0, sticky=tk.W, pady=10, padx=5)
        
        email_var = tk.StringVar()
        email_entry = tk.Entry(form_frame, textvariable=email_var, width=30, font=BW_FONTS["normal"])
        email_entry.grid(row=0, column=1, sticky=tk.W, pady=10)
        
        tk.Label(
            form_frame,
            text="密码:",
            font=BW_FONTS["normal"],
            bg=BW_COLORS["card_bg"]
        ).grid(row=1, column=0, sticky=tk.W, pady=10, padx=5)
        
        password_var = tk.StringVar()
        password_entry = tk.Entry(form_frame, textvariable=password_var, width=30, font=BW_FONTS["normal"], show="*")
        password_entry.grid(row=1, column=1, sticky=tk.W, pady=10)
        
        result_label = tk.Label(
            form_frame,
            text="",
            font=BW_FONTS["small"],
            bg=BW_COLORS["card_bg"],
            fg=BW_COLORS["danger"]
        )
        result_label.grid(row=2, column=0, columnspan=2, pady=10)
        
        btn_frame = tk.Frame(main_container, bg=BW_COLORS["card_bg"])
        btn_frame.pack(pady=10)
        
        def disable_form():
            email_entry.config(state='disabled')
            password_entry.config(state='disabled')
            login_btn.config(state='disabled')
            cancel_btn.config(state='disabled')
            result_label.config(text="正在登录...")
        
        def enable_form():
            email_entry.config(state='normal')
            password_entry.config(state='normal')
            login_btn.config(state='normal')
            cancel_btn.config(state='normal')
        
        def on_login_complete(result):
            if isinstance(result, tuple) and len(result) >= 2:
                success = result[0]
                data = result[1] if success else result[1]
            else:
                success = False
                data = "未知错误"
            
            enable_form()
            login_window.update()
            
            if success and data and isinstance(data, dict):
                self.user_token = data.get("token")
                self.current_user = data.get("username")
                if self.user_token and self.current_user:
                    self.save_session()
                    self.update_login_state()
                    login_window.destroy()
                    self.log("✓ 登录成功")
                    self.refresh_online_users()
                    self.start_chat_connection()
                    # 登录成功后加载历史记录
                    self.load_chat_history()
                else:
                    result_label.config(text="登录失败: 服务器返回数据不完整")
            else:
                result_label.config(text=f"登录失败: {data}")
        
        def do_login():
            email = email_var.get().strip().lower()
            password = password_var.get().strip()
            
            if not email or not password:
                result_label.config(text="请输入QQ邮箱和密码")
                return
            
            # 检查邮箱格式
            if not email.endswith('@qq.com'):
                result_label.config(text="请使用QQ邮箱登录 (@qq.com)")
                return
            
            disable_form()
            
            # 在后台线程中执行登录
            def login_task():
                return self.api_login(email, password)
            
            self.run_in_thread(login_task, on_login_complete)
        
        login_btn = create_bw_button(btn_frame, "登录", do_login, "primary", width=15)
        login_btn.pack(side=tk.LEFT, padx=5)
        
        cancel_btn = create_bw_button(btn_frame, "取消", login_window.destroy, "secondary", width=15)
        cancel_btn.pack(side=tk.LEFT, padx=5)
        
        email_entry.focus()
        login_window.bind('<Return>', lambda e: do_login())
    
    def show_register(self):
        """显示注册窗口"""
        register_window = tk.Toplevel(self.root)
        register_window.title("注册账号")
        register_window.geometry("400x400")
        register_window.resizable(False, False)
        register_window.configure(bg=BW_COLORS["background"])
        register_window.transient(self.root)
        register_window.grab_set()
        
        main_container = create_bw_frame(register_window)
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(
            main_container,
            text="注册账号 (仅限QQ邮箱)",
            font=BW_FONTS["subtitle"],
            bg=BW_COLORS["card_bg"],
            fg=BW_COLORS["primary"]
        ).pack(pady=10)
        
        form_frame = tk.Frame(main_container, bg=BW_COLORS["card_bg"])
        form_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(
            form_frame,
            text="QQ邮箱:",
            font=BW_FONTS["normal"],
            bg=BW_COLORS["card_bg"]
        ).grid(row=0, column=0, sticky=tk.W, pady=8, padx=5)
        
        email_var = tk.StringVar()
        email_entry = tk.Entry(form_frame, textvariable=email_var, width=30, font=BW_FONTS["normal"])
        email_entry.grid(row=0, column=1, sticky=tk.W, pady=8)
        tk.Label(
            form_frame,
            text="(仅支持@qq.com邮箱)",
            font=BW_FONTS["small"],
            bg=BW_COLORS["card_bg"],
            fg=BW_COLORS["text_secondary"]
        ).grid(row=1, column=1, sticky=tk.W, padx=5)
        
        tk.Label(
            form_frame,
            text="用户名:",
            font=BW_FONTS["normal"],
            bg=BW_COLORS["card_bg"]
        ).grid(row=2, column=0, sticky=tk.W, pady=8, padx=5)
        
        username_var = tk.StringVar()
        username_entry = tk.Entry(form_frame, textvariable=username_var, width=30, font=BW_FONTS["normal"])
        username_entry.grid(row=2, column=1, sticky=tk.W, pady=8)
        
        tk.Label(
            form_frame,
            text="密码:",
            font=BW_FONTS["normal"],
            bg=BW_COLORS["card_bg"]
        ).grid(row=3, column=0, sticky=tk.W, pady=8, padx=5)
        
        password_var = tk.StringVar()
        password_entry = tk.Entry(form_frame, textvariable=password_var, width=30, font=BW_FONTS["normal"], show="*")
        password_entry.grid(row=3, column=1, sticky=tk.W, pady=8)
        
        tk.Label(
            form_frame,
            text="确认密码:",
            font=BW_FONTS["normal"],
            bg=BW_COLORS["card_bg"]
        ).grid(row=4, column=0, sticky=tk.W, pady=8, padx=5)
        
        confirm_var = tk.StringVar()
        confirm_entry = tk.Entry(form_frame, textvariable=confirm_var, width=30, font=BW_FONTS["normal"], show="*")
        confirm_entry.grid(row=4, column=1, sticky=tk.W, pady=8)
        
        result_label = tk.Label(
            form_frame,
            text="",
            font=BW_FONTS["small"],
            bg=BW_COLORS["card_bg"],
            fg=BW_COLORS["danger"]
        )
        result_label.grid(row=5, column=0, columnspan=2, pady=10)
        
        btn_frame = tk.Frame(main_container, bg=BW_COLORS["card_bg"])
        btn_frame.pack(pady=10)
        
        def disable_form():
            email_entry.config(state='disabled')
            username_entry.config(state='disabled')
            password_entry.config(state='disabled')
            confirm_entry.config(state='disabled')
            register_btn.config(state='disabled')
            cancel_btn.config(state='disabled')
            result_label.config(text="正在注册...")
        
        def enable_form():
            email_entry.config(state='normal')
            username_entry.config(state='normal')
            password_entry.config(state='normal')
            confirm_entry.config(state='normal')
            register_btn.config(state='normal')
            cancel_btn.config(state='normal')
        
        def on_register_complete(result):
            if isinstance(result, tuple) and len(result) >= 2:
                success = result[0]
                data = result[1] if not success else "注册成功"
            else:
                success = False
                data = "未知错误"
            
            enable_form()
            register_window.update()
            
            if success:
                result_label.config(text="注册成功！请查看QQ邮箱验证", fg=BW_COLORS["success"])
                register_window.after(1000, register_window.destroy)
                self.log("✓ 注册成功，请查收验证邮件")
                # 显示验证窗口
                self.show_email_verification(email_var.get(), username_var.get())
            else:
                result_label.config(text=f"注册失败: {data}")
        
        def do_register():
            email = email_var.get().strip().lower()
            username = username_var.get().strip()
            password = password_var.get().strip()
            confirm = confirm_var.get().strip()
            
            if not all([email, username, password, confirm]):
                result_label.config(text="请填写所有字段")
                return
            
            # 检查QQ邮箱格式
            if not email.endswith('@qq.com'):
                result_label.config(text="请使用QQ邮箱注册 (@qq.com)")
                return
            
            if password != confirm:
                result_label.config(text="两次输入的密码不一致")
                return
            
            if len(password) < 6:
                result_label.config(text="密码长度至少6位")
                return
            
            if len(username) < 2 or len(username) > 20:
                result_label.config(text="用户名长度2-20个字符")
                return
            
            disable_form()
            
            # 保存临时信息
            self.pending_email = email
            self.pending_password = password
            
            # 在后台线程中执行注册
            def register_task():
                return self.api_register(email, username, password)
            
            self.run_in_thread(register_task, on_register_complete)
        
        register_btn = create_bw_button(btn_frame, "注册", do_register, "primary", width=15)
        register_btn.pack(side=tk.LEFT, padx=5)
        
        cancel_btn = create_bw_button(btn_frame, "取消", register_window.destroy, "secondary", width=15)
        cancel_btn.pack(side=tk.LEFT, padx=5)
        
        email_entry.focus()
        register_window.bind('<Return>', lambda e: do_register())
    
    def show_email_verification(self, email, username):
        """显示邮箱验证窗口"""
        verify_window = tk.Toplevel(self.root)
        verify_window.title("邮箱验证")
        verify_window.geometry("450x350")
        verify_window.resizable(False, False)
        verify_window.configure(bg=BW_COLORS["background"])
        verify_window.transient(self.root)
        verify_window.grab_set()
        
        main_container = create_bw_frame(verify_window)
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # 标题
        tk.Label(
            main_container,
            text="邮箱验证",
            font=BW_FONTS["subtitle"],
            bg=BW_COLORS["card_bg"],
            fg=BW_COLORS["primary"]
        ).pack(pady=10)
        
        # 提示信息
        info_frame = tk.Frame(main_container, bg=BW_COLORS["card_bg"])
        info_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(
            info_frame,
            text=f"验证码已发送到您的QQ邮箱：",
            font=BW_FONTS["normal"],
            bg=BW_COLORS["card_bg"]
        ).pack()
        
        tk.Label(
            info_frame,
            text=email,
            font=BW_FONTS["small"],
            bg=BW_COLORS["card_bg"],
            fg=BW_COLORS["primary"]
        ).pack(pady=(2, 0))
        
        tk.Label(
            info_frame,
            text="请在1小时内完成验证",
            font=BW_FONTS["small"],
            bg=BW_COLORS["card_bg"],
            fg=BW_COLORS["warning"]
        ).pack(pady=(5, 0))
        
        # 输入验证码
        form_frame = tk.Frame(main_container, bg=BW_COLORS["card_bg"])
        form_frame.pack(fill=tk.X, pady=15)
        
        tk.Label(
            form_frame,
            text="6位验证码：",
            font=BW_FONTS["normal"],
            bg=BW_COLORS["card_bg"]
        ).pack(pady=(0, 5))
        
        code_var = tk.StringVar()
        code_entry = tk.Entry(
            form_frame,
            textvariable=code_var,
            width=12,
            font=("Consolas", 18, "bold"),
            justify="center",
            bg=BW_COLORS["light"],
            relief="flat",
            bd=1,
            highlightbackground=BW_COLORS["border"]
        )
        code_entry.pack()
        
        # 验证结果标签
        result_label = tk.Label(
            main_container,
            text="",
            font=BW_FONTS["small"],
            bg=BW_COLORS["card_bg"],
            fg=BW_COLORS["danger"],
            wraplength=350
        )
        result_label.pack(pady=10)
        
        def disable_form():
            code_entry.config(state='disabled')
            verify_btn.config(state='disabled')
            resend_btn.config(state='disabled')
            cancel_btn.config(state='disabled')
        
        def enable_form():
            code_entry.config(state='normal')
            verify_btn.config(state='normal')
            resend_btn.config(state='normal')
            cancel_btn.config(state='normal')
        
        def on_verify_complete(result):
            if isinstance(result, tuple) and len(result) >= 2:
                success = result[0]
                message = result[1]
            else:
                success = False
                message = "未知错误"
            
            enable_form()
            verify_window.update()
            
            if success:
                result_label.config(text="✓ 验证成功！正在自动登录...", fg=BW_COLORS["success"])
                verify_window.update()
                
                # 验证成功，自动登录
                verify_window.after(1000, lambda: self.perform_auto_login(verify_window, email))
            else:
                result_label.config(text=f"验证失败: {message}")
        
        def on_resend_complete(result):
            if isinstance(result, tuple) and len(result) >= 2:
                success = result[0]
                message = result[1]
            else:
                success = False
                message = "未知错误"
            
            enable_form()
            verify_window.update()
            
            if success:
                messagebox.showinfo("成功", "验证码已重新发送到您的邮箱", parent=verify_window)
            else:
                messagebox.showerror("失败", f"发送失败: {message}", parent=verify_window)
        
        def do_verify():
            code = code_var.get().strip()
            if len(code) != 6 or not code.isdigit():
                result_label.config(text="请输入6位数字验证码")
                return
            
            result_label.config(text="正在验证...")
            disable_form()
            
            # 在后台线程中执行验证
            def verify_task():
                return self.api_verify_email(email, code)
            
            self.run_in_thread(verify_task, on_verify_complete)
        
        def resend_code():
            disable_form()
            # 在后台线程中重新发送验证码
            def resend_task():
                return self.api_resend_code(email)
            
            self.run_in_thread(resend_task, on_resend_complete)
        
        # 按钮框架
        btn_frame = tk.Frame(main_container, bg=BW_COLORS["card_bg"])
        btn_frame.pack(pady=10)
        
        verify_btn = create_bw_button(btn_frame, "验证", do_verify, "primary", width=10)
        verify_btn.pack(side=tk.LEFT, padx=5)
        
        resend_btn = create_bw_button(btn_frame, "重新发送", resend_code, "secondary", width=10)
        resend_btn.pack(side=tk.LEFT, padx=5)
        
        cancel_btn = create_bw_button(btn_frame, "取消", verify_window.destroy, "danger", width=10)
        cancel_btn.pack(side=tk.LEFT, padx=5)
        
        # 绑定回车键
        verify_window.bind('<Return>', lambda e: do_verify())
        
        # 自动聚焦到验证码输入框
        code_entry.focus()
    
    def perform_auto_login(self, verify_window, email):
        """执行自动登录"""
        def on_login_complete(result):
            verify_window.destroy()
            
            if isinstance(result, tuple) and len(result) >= 2:
                success = result[0]
                login_data = result[1] if success else None
            else:
                success = False
                login_data = None
            
            if success and login_data:
                self.user_token = login_data.get("token")
                self.current_user = login_data.get("username")
                if self.user_token and self.current_user:
                    self.save_session()
                    self.update_login_state()
                    self.log("✓ 自动登录成功")
                    self.refresh_online_users()
                    self.start_chat_connection()
                    # 登录成功后加载历史记录
                    self.load_chat_history()
                else:
                    self.log("✗ 自动登录失败：服务器返回数据不完整", is_error=True)
                    messagebox.showinfo("验证成功", "邮箱验证成功！请手动登录。")
            else:
                self.log("✗ 自动登录失败，请手动登录", is_error=True)
                messagebox.showinfo("验证成功", "邮箱验证成功！请手动登录。")
        
        # 在后台线程中执行登录
        def login_task():
            return self.api_login(email, self.pending_password)
        
        self.run_in_thread(login_task, on_login_complete)
    
    def logout(self):
        """退出登录"""
        if messagebox.askyesno("确认退出", "确定要退出登录吗？"):
            self.stop_chat_connection()
            self.user_token = None
            self.current_user = None
            self.history_loaded = False
            self.clear_session()
            self.update_login_state()
            self.clear_online_list()
            self.log("✓ 已退出登录")
            self.displayed_message_hashes.clear()  # 清空消息哈希
            self.last_message_id = 0  # 重置最后消息ID
    
    def refresh_online_users(self):
        """刷新在线用户列表"""
        if not self.current_user:
            return
        
        # 禁用按钮，防止重复点击
        self.refresh_online_btn.config(state='disabled')
        self.update_status("正在刷新在线用户...")
        
        def on_complete(result):
            if isinstance(result, tuple) and len(result) >= 2:
                success = result[0]
                users = result[1] if success else []
            else:
                success = False
                users = []
            
            # 恢复按钮状态
            if self.current_user:
                self.refresh_online_btn.config(state='normal')
            
            if success and users is not None:
                self.online_users = users
                self.update_online_list()
                self.online_count_label.config(text=f"在线: {len(users)}")
                self.update_status("就绪")
            else:
                self.update_status("刷新失败")
        
        # 在后台线程中获取在线用户
        def get_online_task():
            return self.api_get_online_users()
        
        self.run_in_thread(get_online_task, on_complete)
    
    def clear_online_list(self):
        """清空在线用户列表"""
        self.online_listbox.delete(0, tk.END)
        self.online_users = []
        self.online_count_label.config(text="在线: 0")
    
    def update_online_list(self):
        """更新在线用户列表显示"""
        self.online_listbox.delete(0, tk.END)
        
        for user in self.online_users:
            if user['username'] == self.current_user:
                display_name = f"{user['username']} (我)"
            else:
                display_name = user['username']
            
            self.online_listbox.insert(tk.END, display_name)
    
    def auto_refresh_online_users(self):
        """自动刷新在线用户列表"""
        if self.current_user:
            # 在后台线程中自动刷新
            def refresh_task():
                return self.api_get_online_users()
            
            def on_refresh_complete(result):
                if isinstance(result, tuple) and len(result) >= 2:
                    success = result[0]
                    users = result[1] if success else []
                else:
                    success = False
                    users = []
                
                if success and users is not None:
                    self.online_users = users
                    self.update_online_list()
                    self.online_count_label.config(text=f"在线: {len(users)}")
            
            self.run_in_thread(refresh_task, on_refresh_complete)
        
        # 每10秒刷新一次
        self.root.after(10000, self.auto_refresh_online_users)
    
    def send_message(self):
        """发送消息"""
        if not self.current_user:
            messagebox.showwarning("提示", "请先登录")
            return
        
        if not self.history_loaded:
            messagebox.showwarning("提示", "历史记录加载中，请稍后再发送消息")
            return
        
        message = self.message_entry.get().strip()
        if not message:
            return
        
        # 生成本地时间戳
        local_timestamp = int(time.time())
        
        # 先显示消息（即时反馈）
        self.display_local_message(message, local_timestamp)
        self.message_entry.delete(0, tk.END)
        
        # 将消息添加到待发送队列
        pending_msg = {
            "content": message,
            "timestamp": local_timestamp,
            "hash": self.get_message_hash(f"local_{local_timestamp}_{message}")
        }
        self.pending_messages.append(pending_msg)
        
        # 在后台线程中发送消息
        def send_task():
            return self.api_send_message(message)
        
        def on_send_complete(result):
            if isinstance(result, tuple) and len(result) >= 2:
                success = result[0]
                result_msg = result[1]
            else:
                success = False
                result_msg = "未知错误"
            
            if success:
                # 发送成功，从待发送队列中移除
                self.pending_messages = [msg for msg in self.pending_messages 
                                       if msg["hash"] != pending_msg["hash"]]
                self.log(f"✓ 消息发送成功")
            else:
                # 发送失败，记录日志
                error_msg = f"消息发送失败: {result_msg}"
                self.log(error_msg, is_error=True)
                
                # 如果有重试次数，可以在这里添加重试逻辑
                if pending_msg["hash"] not in self.retry_count:
                    self.retry_count[pending_msg["hash"]] = 0
                
                if self.retry_count[pending_msg["hash"]] < self.max_retries:
                    self.retry_count[pending_msg["hash"]] += 1
                    self.log(f"第{self.retry_count[pending_msg['hash']]}次重试发送...")
                    # 可以在这里添加重试发送的逻辑
                else:
                    self.log("消息发送失败，已放弃重试", is_error=True)
        
        self.run_in_thread(send_task, on_send_complete)
    
    def display_local_message(self, message, timestamp=None):
        """本地显示发送的消息（即时反馈）"""
        if timestamp is None:
            timestamp = time.time()
        
        time_str = datetime.fromtimestamp(timestamp).strftime("%H:%M:%S")
        formatted_message = f"[{time_str}] <我>: {message}"
        msg_hash = self.get_message_hash(f"local_{timestamp}_{message}")
        
        # 检查是否已显示过
        if msg_hash in self.displayed_message_hashes:
            return
        
        self.displayed_message_hashes.add(msg_hash)
        
        self.chat_text.config(state=tk.NORMAL)
        self.chat_text.insert(tk.END, formatted_message + "\n", "self")
        self.chat_text.see(tk.END)
        self.chat_text.config(state=tk.DISABLED)
        
        # 配置标签样式
        self.chat_text.tag_config("self", foreground=BW_COLORS["primary"])
        self.chat_text.tag_config("other", foreground=BW_COLORS["text_primary"])
    
    def start_chat_connection(self):
        """启动聊天连接"""
        self.chat_active = True
        self.log("已连接到公共聊天室")
    
    def stop_chat_connection(self):
        """停止聊天连接"""
        self.chat_active = False
        self.log("已断开聊天室连接")
    
    def auto_refresh_messages(self):
        """自动刷新消息"""
        if self.current_user and self.chat_active:
            # 在后台线程中获取新消息
            def get_messages_task():
                return self.api_get_messages(self.last_message_id)
            
            def on_messages_complete(result):
                if isinstance(result, tuple) and len(result) >= 2:
                    success = result[0]
                    messages = result[1] if success else []
                else:
                    success = False
                    messages = []
                
                if success and messages:
                    for msg in messages:
                        # 检查是否为重复消息
                        msg_hash = self.get_message_hash(msg)
                        if msg_hash in self.displayed_message_hashes:
                            continue
                        
                        self.display_message(msg)
                        self.displayed_message_hashes.add(msg_hash)
                        
                        # 更新最后消息ID
                        if msg['id'] > self.last_message_id:
                            self.last_message_id = msg['id']
            
            self.run_in_thread(get_messages_task, on_messages_complete)
        
        # 每2秒刷新一次
        self.root.after(2000, self.auto_refresh_messages)
    
    def display_message(self, message):
        """显示消息"""
        timestamp = message.get("timestamp", time.time())
        time_str = datetime.fromtimestamp(timestamp).strftime("%H:%M:%S")
        sender = message.get("sender", "未知用户")
        content = message.get("content", "")
        
        # 高亮显示自己发送的消息
        if sender == self.current_user:
            formatted_message = f"[{time_str}] <我>: {content}"
            tag = "self"
        else:
            formatted_message = f"[{time_str}] {sender}: {content}"
            tag = "other"
        
        self.chat_text.config(state=tk.NORMAL)
        self.chat_text.insert(tk.END, formatted_message + "\n", tag)
        self.chat_text.see(tk.END)
        self.chat_text.config(state=tk.DISABLED)
    
    # ========== HTTP 请求方法 ==========
    
    def http_request(self, url, method="GET", data=None, headers=None, timeout=10):
        """发送HTTP请求"""
        try:
            # 准备请求数据
            if data is not None:
                if method == "GET":
                    # GET请求将参数拼接到URL
                    if isinstance(data, dict):
                        params = urllib.parse.urlencode(data)
                        url = f"{url}?{params}"
                    data = None
                else:
                    # POST请求
                    if isinstance(data, dict):
                        data = urllib.parse.urlencode(data).encode('utf-8')
                    else:
                        data = str(data).encode('utf-8')
            
            # 准备请求头
            request_headers = {'User-Agent': 'PublicChat/1.0'}
            if headers:
                request_headers.update(headers)
            
            # 创建请求
            req = urllib.request.Request(url, data=data, headers=request_headers, method=method)
            
            # 发送请求
            with urllib.request.urlopen(req, timeout=timeout) as response:
                content = response.read().decode('utf-8')
                return json.loads(content)
                
        except urllib.error.URLError as e:
            return {"success": False, "message": f"网络错误: {e.reason}"}
        except urllib.error.HTTPError as e:
            return {"success": False, "message": f"HTTP错误 {e.code}"}
        except json.JSONDecodeError as e:
            return {"success": False, "message": "服务器响应格式错误"}
        except Exception as e:
            return {"success": False, "message": f"请求失败: {str(e)}"}
    
    def verify_token(self, token):
        """验证token"""
        try:
            response = self.http_request(
                f"{self.api_base}/verify_token.php",
                method="POST",
                data={"token": token}
            )
            return response.get("success", False)
        except Exception as e:
            return False
    
    def api_login(self, email, password):
        """API登录"""
        response = self.http_request(
            f"{self.api_base}/login.php",
            method="POST",
            data={
                "email": email,
                "password": password
            }
        )
        
        success = response.get("success", False)
        if success:
            return True, response.get("data")
        else:
            return False, response.get("message", "未知错误")
    
    def api_register(self, email, username, password):
        """API注册"""
        response = self.http_request(
            f"{self.api_base}/register.php",
            method="POST",
            data={
                "email": email,
                "username": username,
                "password": password
            }
        )
        
        success = response.get("success", False)
        message = response.get("message", "未知错误")
        return success, message
    
    def api_verify_email(self, email, code):
        """验证邮箱"""
        response = self.http_request(
            f"{self.api_base}/verify_email.php",
            method="POST",
            data={
                "email": email,
                "code": code
            }
        )
        
        success = response.get("success", False)
        return success, response.get("message", "未知错误")
    
    def api_resend_code(self, email):
        """重新发送验证码"""
        response = self.http_request(
            f"{self.api_base}/resend_code.php",
            method="POST",
            data={"email": email}
        )
        
        success = response.get("success", False)
        return success, response.get("message", "未知错误")
    
    def api_get_online_users(self):
        """获取在线用户列表"""
        params = {"token": self.user_token} if self.user_token else {}
        
        response = self.http_request(
            f"{self.api_base}/get_online_users.php",
            method="GET",
            data=params
        )
        
        success = response.get("success", False)
        if success:
            return True, response.get("data", [])
        else:
            return False, []
    
    def api_send_message(self, message):
        """发送消息"""
        response = self.http_request(
            f"{self.api_base}/send_message.php",
            method="POST",
            data={
                "token": self.user_token,
                "message": message
            }
        )
        
        success = response.get("success", False)
        return success, response.get("message", "未知错误")
    
    def api_get_messages(self, last_id=0):
        """获取消息"""
        params = {
            "token": self.user_token,
            "last_id": last_id
        }
        
        response = self.http_request(
            f"{self.api_base}/get_messages.php",
            method="GET",
            data=params
        )
        
        success = response.get("success", False)
        if success:
            return True, response.get("data", [])
        else:
            return False, []

def main():
    root = tk.Tk()
    app = PublicChatRoom(root)
    root.mainloop()

if __name__ == "__main__":
    main()
