"""
主窗口模块
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, colorchooser, simpledialog
from PIL import Image, ImageTk, ImageDraw, ImageFont
import json
import random
import os
import sys
import subprocess
import platform
from datetime import datetime
import threading
from queue import Queue

from auth_manager import auth  # [AUTH] 导入授权管理器

from canvas_widget import CanvasWidget
from image_processor import ImageProcessor
from modules.composite_image import CompositeImage, get_emoji_font
from constants import (SIZE_PRESETS, BORDER_STYLES, STICKER_LIST, COLORS, 
                      BORDER_STYLES_WITH_PREVIEW, BORDER_CATEGORIES, 
                      BORDER_COLORS, BORDER_STYLE_NAMES,
                      BORDER_SHAPES, BORDER_LINE_STYLES, DEFAULT_BACKGROUNDS,
                      BORDER_PATTERNS, BACKGROUND_PATTERNS, DEFAULT_BORDER_CONFIG,
                      QUICK_COLORS)
from color_picker import ColorPicker
from color_wheel_picker import ColorWheelPicker
from modules.ui_styles import ModernStyles
from modules.export_manager import ExportManager
from modules.batch_processor import BatchProcessor


class ModernToggleCheckbutton(tk.Frame):
    """现代风格的勾选框 - Canvas绘制版"""
    def __init__(self, parent, text, variable, command=None, bg='#1E1E1E', fg='#FFFFFF', 
                 select_color='#007AFF', font=('SF Pro Text', 11)):
        super().__init__(parent, bg=bg, cursor='hand2')
        self.variable = variable
        self.command = command
        self.select_color = select_color
        self.bg = bg
        self.fg = fg
        self.text = text
        
        # 图标画布 (24x24)
        self.canvas = tk.Canvas(self, width=24, height=24, bg=bg, highlightthickness=0)
        self.canvas.pack(side=tk.LEFT)
        
        # 文本标签
        self.text_label = tk.Label(self, text=text, font=font, 
                                  bg=bg, fg=fg)
        self.text_label.pack(side=tk.LEFT, padx=(4, 4))
        
        # 绑定事件
        self.bind('<Button-1>', self._toggle)
        self.canvas.bind('<Button-1>', self._toggle)
        self.text_label.bind('<Button-1>', self._toggle)
        
        # 初始状态
        self._update_display()
        
        # 监听变量变化
        self.variable.trace_add('write', lambda *args: self._update_display())

    def _toggle(self, event=None):
        new_val = not self.variable.get()
        self.variable.set(new_val)
        if self.command:
            self.command()
            
    def _update_display(self):
        self.canvas.delete('all')
        
        # 绘制背景框 (18x18, 居中)
        box_args = {'outline': '#555555', 'width': 2}
        
        if self.variable.get():
            # 选中状态：填充颜色，白色对号
            self.canvas.create_rectangle(3, 3, 21, 21, fill=self.select_color, outline=self.select_color, width=0, tags='bg')
            # 对号
            self.canvas.create_line(7, 12, 11, 16, 17, 8, fill='white', width=2, capstyle=tk.ROUND, joinstyle=tk.ROUND, tags='check')
            self.text_label.config(fg='#FFFFFF')
        else:
            # 未选中状态：仅边框
            self.canvas.create_rectangle(3, 3, 21, 21, fill='', outline='#8E8E93', width=2, tags='bg')
            self.text_label.config(fg='#999999')
class Tooltip:
    """鼠标悬停提示工具类"""
    def __init__(self, widget, text, delay=500):
        self.widget = widget
        self.text = text
        self.delay = delay
        self.tooltip_window = None
        self.after_id = None
        
        widget.bind('<Enter>', self._on_enter)
        widget.bind('<Leave>', self._on_leave)
    
    def _on_enter(self, event):
        self.after_id = self.widget.after(self.delay, self._show_tooltip)
    
    def _on_leave(self, event):
        if self.after_id:
            self.widget.after_cancel(self.after_id)
            self.after_id = None
        self._hide_tooltip()
    
    def _show_tooltip(self):
        if self.tooltip_window:
            return
        
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        
        self.tooltip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        tw.attributes('-topmost', True)
        
        label = tk.Label(tw, text=self.text, bg='#333333', fg='#FFFFFF',
                        font=('SF Pro Text', 10), padx=8, pady=4,
                        relief='solid', borderwidth=0, justify='left') # [UI] 左对齐
        label.pack()
    
    def _hide_tooltip(self):
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None


def get_emoji_font_name():
    """获取跨平台的 tkinter emoji 字体名称
    
    Returns:
        str: 字体名称，用于 tkinter 的 font 参数
    """
    system = platform.system()
    if system == 'Darwin':  # macOS
        return 'Apple Color Emoji'
    elif system == 'Windows':  # Windows
        return 'Segoe UI Emoji'
    else:  # Linux
        return 'Noto Color Emoji'


class MainWindow(tk.Tk):
    """主窗口类"""
    
    def __init__(self):
        super().__init__()
        
        self.title('图片套版工具')
        self.export_manager = ExportManager()
        self.batch_processor = BatchProcessor(self.export_manager)
        # 将 logging 方法绑定到 batch_processor
        self.batch_processor.set_log_callback(self.batch_log)
        
        # 获取屏幕尺寸并设置窗口大小（屏幕的80%）
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        window_width = int(screen_width * 0.85)
        window_height = int(screen_height * 0.85)
        
        # 居中显示
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        self.geometry(f'{window_width}x{window_height}+{x}+{y}')
        self.minsize(1200, 700)  # 最小窗口尺寸
        self.configure(bg=COLORS['bg'])
        
        # 禁用双击标题栏缩小窗口 (macOS workaround)
        self.resizable(True, True)
        self._last_good_geometry = f'{window_width}x{window_height}+{x}+{y}'
        self._ignore_configure = False
        
        def _on_configure(event):
            # 检测窗口是否被"最小化"到只剩标题栏
            if self._ignore_configure:
                return
            # macOS 双击标题栏会将窗口高度缩到很小
            if event.widget == self and event.height < 100:
                self._ignore_configure = True
                self.geometry(self._last_good_geometry)
                self.after(100, lambda: setattr(self, '_ignore_configure', False))
            elif event.widget == self and event.height >= 700:
                # 记录正常尺寸
                self._last_good_geometry = self.geometry()
                
        self.bind('<Configure>', _on_configure)
        
        # 应用现代 UI 主题
        ModernStyles.apply_theme(self)
        
        # 初始化变量
        self.image_processor = ImageProcessor()
        self.current_size_preset = SIZE_PRESETS[3]  # 默认小红书3:4
        self.current_border = BORDER_STYLES[0]  # 默认无边框
        self.batch_images = []  # 批量图片列表
        self.sticker_images = {}  # 缓存贴纸图片（用于UI显示）
        self.border_preview_images = {}  # 缓存边框预览图
        self.sticker_photo_refs = []  # 保持图片引用，防止被垃圾回收
        self.border_photo_refs = []  # 保持边框图片引用
        self.sticker_image_cache = {}  # 缓存原始图片对象（用于画布显示，保持高分辨率）
        
        # 历史记录系统
        self.history_stack = []  # 历史记录栈
        self.history_index = -1  # 当前历史位置
        self.max_history = 30  # 最大历史记录数
        
        # 边框选择状态（旧版）
        self.selected_border_category = 'modern'
        self.selected_border_color = 'black'
        
        # 自定义边框配置
        # 边框配置 - 使用默认值
        self.border_config = {
            'shape': DEFAULT_BORDER_CONFIG['shape'],
            'line_style': DEFAULT_BORDER_CONFIG['line_style'],
            'width': DEFAULT_BORDER_CONFIG['width'],
            'radius': DEFAULT_BORDER_CONFIG['radius'],
            'color': DEFAULT_BORDER_CONFIG['color'],
            'pattern': DEFAULT_BORDER_CONFIG['pattern'],
            'pattern_color': DEFAULT_BORDER_CONFIG['pattern_color'],
            'pattern_size': DEFAULT_BORDER_CONFIG['pattern_size'],
        }
        
        # 背景配置
        self.background_color = '#FFFFFF'
        self.background_pattern = 'none'
        self.background_pattern_color = '#E0E0E0'
        self.background_pattern_size = 10
        self.background_image = None
        
        # 颜色方块引用
        self.bg_color_canvases = {}
        self.border_color_canvas = None
        
        # 加载资源
        self.load_sticker_images()
        self.load_border_preview_images()
        
        # 历史记录
        self.history = []
        self.history_index = -1
        
        # 预设主题列表
        self.preset_themes = []
        
        # 滚动控制
        self._active_scroll_widget = None
        
        # 批量处理配置
        self.batch_input_dir = ''  # 输入目录
        self.batch_output_dir = ''  # 输出目录
        self.processed_images = set()  # 已处理的图片集合
        # self.batch_regenerate_all = tk.BooleanVar(value=False) # 已废弃
        
        # 批量随机化选项
        # 批量随机化选项
        self.batch_random_color = tk.BooleanVar(value=True)
        self.batch_random_style = tk.BooleanVar(value=True)
        self.batch_random_pattern = tk.BooleanVar(value=True)
        self.batch_random_highlight = tk.BooleanVar(value=True) # NEW
        self.batch_random_font_style = tk.BooleanVar(value=True) # 随机字体样式
        self.batch_random_background_style = tk.BooleanVar(value=True) # 随机背景样式 (颜色+图案)
        self.batch_random_stickers = tk.BooleanVar(value=True) # 随机贴纸 (1-4个，优先下方)
        self.batch_match_canvas = tk.BooleanVar(value=True) # 参考画布位置
        
        # 文字层配置
        self.text_layers = []  # 文字层列表
        self.current_text_config = {
            'content': '',
            'font_size': 48,
            'color': '#FFFFFF',
            'font_family': 'yuanti',
            'align': 'center',
            'position': 'center',
            'margin': 20,
            'shadow': {'enabled': True, 'color': '#000000', 'offset': (2, 2), 'blur': 4},
            'stroke': {'enabled': False, 'color': '#000000', 'width': 2},
        }
        
        # 批量文字配置
        self.batch_text_dir = ''  # 文本目录
        self.batch_use_text_dir = tk.BooleanVar(value=False)  # 使用文本目录
        
        # 自动高亮定时器
        self._highlight_timer = None
        
        # 加载用户设置
        self.load_settings()
        # [AUTH] 单独加载 API Key
        self.deepseek_api_key = self._load_api_key()
        
         
        # [AUTH] 初始化后检查授权
        self.check_auth_at_startup()
        self.create_auth_menu()
        
        # [UI] 创建界面
        self.create_widgets()

    def create_auth_menu(self):
        """创建授权菜单"""
        menubar = tk.Menu(self)
        self.config(menu=menubar)
        
        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="软件激活 / 授权信息", command=self.show_activation_dialog)
        help_menu.add_command(label="用量统计", command=self.show_usage_dialog)
        help_menu.add_command(label="关于", command=lambda: messagebox.showinfo("关于", "图片批量套版工具 v1.0"))

    def check_auth_at_startup(self):
        """启动时检查授权"""
        status = auth.get_status()
        title_suffix = ""
        
        if status['status'] == 'limited':
            messagebox.showwarning("今日额度耗尽", f"{status['msg']}\n请明天再来或激活解除限制。")
            title_suffix = " [免费版 - 今日额度耗尽]"
        elif status['status'] == 'trial':
             # 试用期提示
             title_suffix = f" [全功能体验版 - {status['msg']}]"
        elif status['status'] == 'free':
             title_suffix = f" [免费版 - {status['msg']}]"
        elif status['status'] == 'expired':
             messagebox.showerror("授权过期", "您的授权已过期，软件已降级为免费版限制。请重新激活。")
             title_suffix = " [授权过期 - 免费版]"
        elif status['status'] == 'activated':
             title_suffix = " [已激活]"
             if '天' in status['msg']:
                 days_left = status.get('days_left', 0)
                 title_suffix = f" [有效期剩 {days_left} 天]"
             
        if title_suffix:
            self.title(f"{self.title().split(' [')[0]}{title_suffix}")

    def show_activation_dialog(self):
        """显示激活对话框 (在线激活版)"""
        import webbrowser
        
        info = auth.get_activation_info()
        status_msg = info['status']['msg']
        ui_config = auth.get_ui_config()
        
        dialog = tk.Toplevel(self)
        dialog.title(ui_config.get("ui_title", "软件授权激活"))
        dialog.geometry("700x720")
        dialog.resizable(False, False)
        dialog.configure(bg=COLORS['bg'])
        
        # [MOD] Ensure window is initialized before grab
        dialog.transient(self)
        
        # 主容器
        main_frame = tk.Frame(dialog, bg=COLORS['bg'], padx=30, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Force update to ensure geometry and widgets are processed
        dialog.update_idletasks()
        dialog.grab_set()
        
        # 1. 标题和状态
        header_frame = tk.Frame(main_frame, bg=COLORS['bg'])
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        tk.Label(header_frame, text=ui_config.get("ui_title", "软件授权激活"), font=("SF Pro Display", 20, "bold"), 
                bg=COLORS['bg'], fg=COLORS['text_primary']).pack(anchor='w')
                
        status_fg = "#4CD964" if info['status']['status'] == 'activated' else "#FF3B30"
        tk.Label(header_frame, text=f"当前状态: {status_msg}", 
                font=("SF Pro Text", 11), bg=COLORS['bg'], fg=status_fg).pack(anchor='w', pady=(5,0))
        
        # [NEW] 免费体验提示
        tk.Label(header_frame, text="新用户安装即可享受 3 天免费全功能体验", 
                font=("SF Pro Text", 9), bg=COLORS['bg'], fg=COLORS['text_tertiary']).pack(anchor='w', pady=(2,0))
        
        # [NEW] 促销与更新说明
        promo_frame = tk.Frame(header_frame, bg="#1C1C1E", padx=10, pady=6)
        promo_frame.pack(fill=tk.X, pady=(10, 0))
        
        inner_promo = tk.Frame(promo_frame, bg="#1C1C1E")
        inner_promo.pack(expand=True)
        
        tk.Label(inner_promo, text=ui_config.get("ui_promo_text", "🔥 限量特惠进行中"), font=("SF Pro Text", 10, "bold"), 
                 bg="#1C1C1E", fg="#FF9500").pack(side=tk.LEFT)
        tk.Label(inner_promo, text=f" | {ui_config.get('ui_slogan', '成功源于坚持，灵感来自创作')}", font=("SF Pro Text", 10), 
                 bg="#1C1C1E", fg="#A0A0A0").pack(side=tk.LEFT)

        # 2. 购买套餐卡片 (Grid布局)
        plans_frame = tk.Frame(main_frame, bg=COLORS['bg'])
        plans_frame.pack(fill=tk.X, pady=(0, 20))
        
        plans = ui_config.get("ui_pricing", [])
        
        for i, plan in enumerate(plans):
            # 强化型解析逻辑：全 get() 访问 + 默认值，彻底杜绝 KeyError
            try:
                p_raw = plan.get('price', '0')
                op_raw = plan.get('old_price', '0')
                p_val = float(p_raw)
                op_val = float(op_raw)
                discount = int((1 - p_val/op_val) * 100) if op_val > 0 else 0
            except:
                discount = 0
            
            # 卡片容器
            plan_name = plan.get("name", "套餐")
            card_border = "#0A84FF" if "三年" in plan_name else "#3A3A3C"
            card = tk.Frame(plans_frame, bg="#2C2C2E", bd=0, highlightthickness=1, highlightbackground=card_border)
            card.grid(row=0, column=i, padx=5, sticky="ew")
            plans_frame.grid_columnconfigure(i, weight=1)
            
            # [NEW] 折扣标签
            badge_text = f"-{discount}%"
            badge = tk.Label(card, text=badge_text, font=("SF Pro Text", 9, "bold"), bg="#FF3B30", fg="white", padx=5, pady=2)
            badge.place(relx=1.0, x=0, y=0, anchor="ne")
            
            tk.Label(card, text=plan_name, font=("SF Pro Text", 11, "bold"), bg="#2C2C2E", fg=COLORS['text_primary']).pack(pady=(20, 2))
            
            # 原价 (中划线效果)
            old_price_display = plan.get('old_price', '0')
            old_price_frame = tk.Frame(card, bg="#2C2C2E")
            old_price_frame.pack(pady=(2, 0))
            tk.Label(old_price_frame, text=f"¥{old_price_display}", font=("SF Pro Text", 13, "overstrike"), 
                     bg="#2C2C2E", fg="#999999").pack()
            
            # 现价
            price_display = plan.get('price', '0')
            price_frame = tk.Frame(card, bg="#2C2C2E")
            price_frame.pack(pady=(0, 8))
            tk.Label(price_frame, text="¥", font=("SF Pro Display", 15, "bold"), bg="#2C2C2E", fg="#0A84FF").pack(side=tk.LEFT, pady=(5,0))
            tk.Label(price_frame, text=str(price_display), font=("SF Pro Display", 30, "bold"), bg="#2C2C2E", fg="#0A84FF").pack(side=tk.LEFT)
            
            # 描述 (促销副标题)
            display_desc = plan.get("desc", "")
            tk.Label(card, text=display_desc, font=("SF Pro Text", 9), bg="#2C2C2E", fg="#B0B0B0").pack(pady=(2, 8))
            
            # 计费周期 (卡片底部标签)
            display_period = plan.get("period", "")
            tk.Label(card, text=display_period, font=("SF Pro Text", 8), bg="#2C2C2E", fg="#666666").pack(pady=(0, 10))
            
            # 购买按钮
            buy_btn = tk.Label(card, text="立即购买", bg="#007AFF", fg="white", font=("SF Pro Text", 10, "bold"),
                               padx=15, pady=8, cursor='hand2')
            buy_btn.pack(pady=(0, 15), padx=20, fill=tk.X)
            
            def make_hover(btn, normal_bg, hover_bg):
                btn.bind("<Enter>", lambda e: btn.config(bg=hover_bg))
                btn.bind("<Leave>", lambda e: btn.config(bg=normal_bg))
            
            make_hover(buy_btn, "#007AFF", "#0056b3")
            # 安全获取 URL
            target_url = plan.get("url", "https://your-shop-url.com")
            buy_btn.bind("<Button-1>", lambda e, u=target_url: webbrowser.open(u))

        # 4. 激活码输入区域 (极致压缩，找回按钮)
        input_section = tk.Frame(main_frame, bg="#252526", padx=30, pady=12, highlightthickness=1, highlightbackground="#3A3A3C")
        input_section.pack(fill=tk.X, pady=(5, 0))
        
        tk.Label(input_section, text="输入激活码 (License Key)", font=("SF Pro Text", 10, "bold"), 
                 bg="#252526", fg="#8E8E93").pack(anchor='w', pady=(0, 3))
        
        entry_key = tk.Entry(input_section, font=("Courier New", 18), justify='center', 
                            bg="#1C1C1E", fg="#FFD60A", relief="flat", insertbackground="#FFD60A")
        entry_key.pack(fill=tk.X, ipady=10, pady=(0, 12))
        
        def do_activate():
            code = entry_key.get().strip()
            if not code:
                messagebox.showwarning("提示", "请输入激活码")
                return
                
            btn_activate.config(text="正在进行在线验证...", state='disabled', bg="#3A3A3C")
            dialog.update()
            
            success, msg = auth.activate_online(code)
            
            if success:
                messagebox.showinfo("激活成功", "授权码验证通过，感谢您的支持！")
                dialog.destroy()
                self.check_auth_at_startup()
            else:
                messagebox.showerror("激活失败", msg)
                btn_activate.config(text="立即激活授权", state='normal', bg="#30D158")

        # 使用 Label 模拟大按钮以获得更好的视觉效果 - 更加大气协调
        btn_activate = tk.Label(input_section, text="立即激活授权", bg="#30D158", fg="white", 
                               font=("SF Pro Text", 15, "bold"), cursor="hand2", pady=12)
        btn_activate.pack(fill=tk.X, padx=10)
        
        def on_activate_click(e):
            if btn_activate.cget("state") != "disabled":
                do_activate()

        btn_activate.bind("<Button-1>", on_activate_click)
        btn_activate.bind("<Enter>", lambda e: btn_activate.config(bg="#32E067") if btn_activate.cget("state") != "disabled" else None)
        btn_activate.bind("<Leave>", lambda e: btn_activate.config(bg="#30D158") if btn_activate.cget("state") != "disabled" else None)
        
        # 5. 客服与设备信息 (页脚 - 整合版)
        footer_frame = tk.Frame(main_frame, bg=COLORS['bg'])
        footer_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))
        
        device_id = info['machine_code']
        
        def copy_device_id(e=None):
            self.clipboard_clear()
            self.clipboard_append(device_id)
            
            # 自定义深色高级弹窗 (Toast)
            toast = tk.Toplevel(dialog)
            toast.overrideredirect(True)
            toast.attributes("-topmost", True)
            toast.configure(bg="#1E1E1E", highlightthickness=1, highlightbackground="#0A84FF")
            
            # 居中对齐计算 (相对于激活窗口)
            w, h = 320, 100
            root_x = dialog.winfo_rootx()
            root_y = dialog.winfo_rooty()
            center_x = root_x + (dialog.winfo_width() // 2) - (w // 2)
            center_y = root_y + (dialog.winfo_height() // 2) - (h // 2)
            toast.geometry(f"{w}x{h}+{center_x}+{center_y}")
            
            # 内容
            tk.Label(toast, text="✓", font=("SF Pro Display", 26), 
                     bg="#1E1E1E", fg="#30D158").pack(pady=(15, 0))
            tk.Label(toast, text="设备 ID 已复制到剪贴板", font=("SF Pro Text", 11), 
                     bg="#1E1E1E", fg="white").pack(pady=(5, 15))
            
            # 1.5秒后自动消失
            toast.after(1500, toast.destroy)

        # 简洁的页脚：左侧显示建议，中间/右侧显示可点击复制的 ID
        tk.Label(footer_frame, text="遇到问题请联系客服 | 激活后绑定当前设备", 
                font=("SF Pro Text", 9), bg=COLORS['bg'], fg="#555555").pack(side=tk.LEFT)
        
        id_label = tk.Label(footer_frame, text=f"设备 ID: {device_id} (点击复制)", 
                          font=("SF Pro Text", 9), bg=COLORS['bg'], fg="#0A84FF", cursor="hand2")
        id_label.pack(side=tk.RIGHT)
        id_label.bind("<Button-1>", copy_device_id)
        id_label.bind("<Enter>", lambda e: id_label.config(fg="#5AC8FA"))
        id_label.bind("<Leave>", lambda e: id_label.config(fg="#0A84FF"))
        
        # 兼容 disabled 模拟
        def set_btn_state(state):
            btn_activate.config(state=state)
            if state == "disabled":
                btn_activate.config(bg="#3A3A3C", fg="#8E8E93")
            else:
                btn_activate.config(bg="#30D158", fg="white")
        
        btn_activate.set_state = set_btn_state

    def show_usage_dialog(self):
        """显示用量统计"""
        stats = auth.get_usage_stats()
        status = auth.get_status()
        
        msg = (f"📊 用量统计\n\n"
               f"累计导出总数: {stats['total_count']} 张\n"
               f"今日导出数量: {stats['daily_count']} 张\n"
               f"软件安装日期: {stats['install_date']}\n\n"
               f"当前账户状态: {status['msg']}")
               
        messagebox.showinfo("用量统计", msg)

    def create_widgets(self):
        """创建界面组件 - 毛玻璃风格"""
        # 主容器 - 使用 PanedWindow 实现可调整大小
        self.paned_window = tk.PanedWindow(self, orient=tk.HORIZONTAL, 
                                          bg=COLORS['bg'], sashwidth=4, sashpad=0,
                                          showhandle=False, borderwidth=0)
        # 状态变量 - 记录当前拖拽的sash索引
        self.dragging_sash_index = None
        
        self.paned_window.pack(fill=tk.BOTH, expand=True)
        
        # 绑定鼠标事件处理拖拽限制
        # ButtonPress: 检测点中了哪个 sash
        self.paned_window.bind('<ButtonPress-1>', self.start_sash_drag, add='+')
        # B1-Motion: 拦截拖拽，实施限制
        self.paned_window.bind('<B1-Motion>', self.on_sash_drag)
        # ButtonRelease: 结束拖拽
        self.paned_window.bind('<ButtonRelease-1>', self.end_sash_drag, add='+')
        
        # 延迟绑定窗口大小改变事件
        self.after(1000, self.bind_configure_limit)
        
        # 左侧面板容器
        self.left_container = tk.Frame(self.paned_window, bg=COLORS['bg'])
        # self.left_container.bind('<Configure>', self.on_panel_resize) # 移除容易导致闪烁的 Configure 绑定
        
        self.left_panel = self.create_left_panel(self.left_container)
        self.left_panel.pack(fill=tk.BOTH, expand=True, padx=(8, 0), pady=8)
        
        self.left_panel_visible = True
        
        # 将左侧容器添加到 PanedWindow (设置最小宽度 260)
        self.paned_window.add(self.left_container, minsize=260, width=280)

        # 中间画布区域
        self.center_panel = self.create_center_panel(self.paned_window)
        # 设置 stretch='always' 确保中间区域优先占用空间
        self.paned_window.add(self.center_panel, stretch='always', minsize=360)
        
        # 绑定文字交互回调
        if hasattr(self, 'canvas_widget'):
            self.canvas_widget.set_text_callback(self.on_text_transform)
        
        # 右侧面板
        self.right_panel = self.create_right_panel(self.paned_window)
        # 初始宽度设小一点，限制最小宽度
        self.paned_window.add(self.right_panel, minsize=260, width=280)
        
        # 延迟应用默认边框（等待画布初始化完成）
        self.after(200, self.apply_default_border)
        
        # 绑定快捷键
        self.bind('<Command-z>', lambda e: self.undo())
        self.bind('<Command-Shift-Z>', lambda e: self.redo())
        self.bind('<Command-s>', lambda e: self.export_image())
        self.bind('<Configure>', self.on_window_resize)
    
    def load_settings(self):
        """加载用户设置"""
        import json
        settings_path = os.path.join(os.path.dirname(__file__), 'settings.json')
        try:
            if os.path.exists(settings_path):
                with open(settings_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    self.batch_input_dir = settings.get('batch_input_dir', '')
                    self.batch_output_dir = settings.get('batch_output_dir', '')
                    self.batch_text_dir = settings.get('batch_text_dir', '') # NOW SAVED
                    self.ai_save_path = settings.get('ai_save_path', '') # AI 文案保存路径
                    # API Key 单独存储，不再从 settings 读取
                    self.show_batch_help = settings.get('show_batch_help', True) # [UX] Default True
                    self.processed_images = set(settings.get('processed_images', []))
                    self.preset_themes = settings.get('preset_themes', [])
                    print(f"✓ 已加载设置: 输入={self.batch_input_dir}, 输出={self.batch_output_dir}, 预设={len(self.preset_themes)}个")
        except Exception as e:
            print(f"加载设置失败: {e}")
    
    def save_settings(self):
        """保存用户设置"""
        import json
        settings_path = os.path.join(os.path.dirname(__file__), 'settings.json')
        try:
            settings = {
                'batch_input_dir': self.batch_input_dir,
                'batch_input_dir': self.batch_input_dir,
                'batch_output_dir': self.batch_output_dir,
                'batch_text_dir': self.batch_text_dir, # NOW SAVED
                'ai_save_path': getattr(self, 'ai_save_path', ''), # AI 文案保存路径
                # API Key 单独存储
                'show_batch_help': getattr(self, 'show_batch_help', True),
                'processed_images': list(self.processed_images),
                'preset_themes': self.preset_themes
            }
            with open(settings_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存设置失败: {e}")
    
    def batch_log(self, message):
        """输出日志到批量处理日志框"""
        if hasattr(self, 'batch_log_text'):
            self.batch_log_text.config(state=tk.NORMAL)
            self.batch_log_text.insert(tk.END, f"{message}\n")
            self.batch_log_text.see(tk.END)  # 自动滚动到底部
            self.batch_log_text.config(state=tk.DISABLED)
            self.update_idletasks()  # 强制更新UI
    
    def on_window_resize(self, event):
        """窗口大小改变时调整画布"""
        if event.widget == self:
            # 延迟调整，避免频繁触发
            if hasattr(self, 'resize_timer'):
                self.after_cancel(self.resize_timer)
            self.resize_timer = self.after(100, self.adjust_canvas_display)
    
    def adjust_canvas_display(self):
        """自适应调整画布显示，并限制侧边栏宽度"""
        try:
            # 1. 强制限制侧边栏宽度 (最大 1/4)
            if hasattr(self, 'paned_window'):
                total_width = self.paned_window.winfo_width()
                if total_width > 100:
                    max_side = int(total_width * 0.25)
                    
                    # 检查左侧 sash (index 0)
                    try:
                        sash0_x, sash0_y = self.paned_window.sash_coord(0)
                        if sash0_x > max_side:
                            self.paned_window.sash_place(0, max_side, sash0_y)
                            # print(f"Limit Left: {sash0_x} -> {max_side}")
                    except Exception:
                        pass
                    
                    # 检查右侧 sash (index 1)
                    try:
                        sash1_x, sash1_y = self.paned_window.sash_coord(1)
                        right_width = total_width - sash1_x
                        if right_width > max_side:
                            target_x = total_width - max_side
                            self.paned_window.sash_place(1, target_x, sash1_y)
                            # print(f"Limit Right: {right_width} -> {max_side}")
                    except Exception:
                        pass

            if hasattr(self, 'canvas_widget') and hasattr(self, 'center_panel'):
                # 获取中间面板实际大小
                self.center_panel.update_idletasks()
                panel_width = self.center_panel.winfo_width()
                panel_height = self.center_panel.winfo_height()
                
                # 预留一点边距
                if panel_width > 40 and panel_height > 40:
                    available_width = panel_width - 40
                    available_height = panel_height - 40
                    
                    # 获取当前预设比例
                    preset = self.current_size_preset
                    ratio = preset['width'] / preset['height']
                    
                    # 计算保持比例的尺寸
                    if ratio > available_width / available_height:
                        # 宽图，以宽度为准
                        new_width = available_width
                        new_height = int(new_width / ratio)
                    else:
                        # 高图或方图，以高度为准
                        new_height = available_height
                        new_width = int(new_height * ratio)
                    
                    # 只有当尺寸发生显著变化时才调整
                    current_width = self.canvas_widget.width
                    current_height = self.canvas_widget.height
                    
                    if abs(new_width - current_width) > 5 or abs(new_height - current_height) > 5:
                        self.canvas_widget.resize_canvas(new_width, new_height)
                        # 如果有当前图片，重新显示
                        if hasattr(self, 'image_processor') and self.image_processor.current_image:
                            self.canvas_widget.display_image(self.image_processor.current_image)
                        
                        # 重新应用背景图案
                        if hasattr(self, 'background_pattern') and self.background_pattern != 'none':
                             self.canvas_widget.set_background_pattern(
                                self.background_pattern, 
                                self.background_color, 
                                self.background_pattern_color,
                                self.background_pattern_size
                             )
                        
                        # 重新应用边框 (必须在背景图案之后，否则会被覆盖)
                        # 总是重新应用边框以确保它在最上层
                        self.canvas_widget.apply_custom_border(self.border_config)
        except Exception as e:
            print(f"Resize error: {e}")
            pass
        
    def next_tab(self, event=None):
        """切换到下一个标签页"""
        if hasattr(self, 'notebook'):
            current_index = self.notebook.index(self.notebook.select())
            total_tabs = self.notebook.index('end')
            next_index = (current_index + 1) % total_tabs
            self.notebook.select(next_index)
            return "break" # 防止默认行为

    def create_widgets(self):
        """创建界面组件 - 毛玻璃风格"""
        # 主容器 - 使用 PanedWindow 实现可调整大小
        self.paned_window = tk.PanedWindow(self, orient=tk.HORIZONTAL, 
                                          bg=COLORS['bg'], sashwidth=4, sashpad=0,
                                          showhandle=False, borderwidth=0)
        # 状态变量 - 记录当前拖拽的sash索引
        self.dragging_sash_index = None
        
        self.paned_window.pack(fill=tk.BOTH, expand=True)
        
        # 绑定鼠标事件处理拖拽限制
        # ButtonPress: 检测点中了哪个 sash
        self.paned_window.bind('<ButtonPress-1>', self.start_sash_drag, add='+')
        # B1-Motion: 拦截拖拽，实施限制
        self.paned_window.bind('<B1-Motion>', self.on_sash_drag)
        # ButtonRelease: 结束拖拽
        self.paned_window.bind('<ButtonRelease-1>', self.end_sash_drag, add='+')
        
        # 延迟绑定窗口大小改变事件
        self.after(1000, self.bind_configure_limit)
        
        # 左侧面板容器
        self.left_container = tk.Frame(self.paned_window, bg=COLORS['bg'])
        # self.left_container.bind('<Configure>', self.on_panel_resize) # 移除容易导致闪烁的 Configure 绑定
        
        self.left_panel = self.create_left_panel(self.left_container)
        self.left_panel.pack(fill=tk.BOTH, expand=True, padx=(8, 0), pady=8)
        
        self.left_panel_visible = True
        
        # 将左侧容器添加到 PanedWindow (设置最小宽度 260)
        self.paned_window.add(self.left_container, minsize=260, width=280)

        # 中间画布区域
        self.center_panel = self.create_center_panel(self.paned_window)
        # 设置 stretch='always' 确保中间区域优先占用空间
        self.paned_window.add(self.center_panel, stretch='always', minsize=360)
        
        # 绑定文字交互回调
        if hasattr(self, 'canvas_widget'):
            self.canvas_widget.set_text_callback(self.on_text_transform)
        
        # 右侧面板
        self.right_panel = self.create_right_panel(self.paned_window)
        # 初始宽度设小一点，限制最小宽度
        self.paned_window.add(self.right_panel, minsize=260, width=280)
        
        # 延迟应用默认边框（等待画布初始化完成）
        self.after(200, self.apply_default_border)
        
        # [FIX] 启动时同步预设字号 (确保批量导出默认字号正确)
        self.after(300, lambda: self.select_size_preset(self.current_size_preset))
        
    def bind_configure_limit(self):
        """延迟绑定窗口调整事件"""
        if hasattr(self, 'paned_window'):
             self.paned_window.bind('<Configure>', lambda e: self.on_sash_drag(e, configure=True), add='+')
    
    def start_sash_drag(self, event):
        """开始拖拽：判断点中了哪个sash"""
        if not hasattr(self, 'paned_window'): return
        
        try:
            # 简单的距离判断：Sash 宽度约4px，增加一点容错
            click_x = event.x
            
            # 检查 Sash 0 (左侧)
            try:
                sash0_x, _ = self.paned_window.sash_coord(0)
                if abs(click_x - sash0_x) < 10:
                    self.dragging_sash_index = 0
                    return
            except: pass
            
            # 检查 Sash 1 (右侧)
            try:
                sash1_x, _ = self.paned_window.sash_coord(1)
                if abs(click_x - sash1_x) < 10:
                    self.dragging_sash_index = 1
                    return
            except: pass
            
        except Exception as e:
            print(f"Drag start error: {e}")
            
    def end_sash_drag(self, event):
        """结束拖拽"""
        self.dragging_sash_index = None
        self.adjust_canvas_display()

    def on_sash_drag(self, event=None, configure=False):
        """处理拖拽过程中的限制"""
        if not hasattr(self, 'paned_window'): return
        if not self.winfo_viewable(): return
        
        try:
            total_width = self.paned_window.winfo_width()
            if total_width < 200: return
            
            MIN_SIDE = 260
            # 左侧最大 30%，右侧最大 35%
            max_left = int(total_width * 0.30) 
            max_right = int(total_width * 0.35)
            
            # 如果是窗口调整事件(configure=True)，检查所有 sash 并在越界时修正
            if configure or self.dragging_sash_index is None:
                # 检查所有并修正（此时不 return break，仅修正）
                try:
                    sash0_x, sash0_y = self.paned_window.sash_coord(0)
                    limit = max(MIN_SIDE, max_left)
                    if sash0_x > limit:
                        self.paned_window.sash_place(0, limit, sash0_y)
                except: pass
                
                try:
                    sash1_x, sash1_y = self.paned_window.sash_coord(1)
                    limit_right_panel = max(MIN_SIDE, max_right)
                    limit_x = total_width - limit_right_panel
                    if sash1_x < limit_x:
                         self.paned_window.sash_place(1, limit_x, sash1_y)
                except: pass
                return

            # 如果是主动拖拽 (dragging_sash_index valid)
            # 我们直接控制 sash 位置并拦截事件 (return 'break') 防止冲突
            
            if self.dragging_sash_index == 0:
                # 左侧
                # 目标位置受限于：最小宽度 ~ 最大宽度
                # 注意：sash_place 0 设置的是左侧面板宽度
                target_limit = max(MIN_SIDE, max_left)
                
                # 鼠标位置限制
                new_x = max(MIN_SIDE, min(event.x, target_limit))
                
                self.paned_window.sash_place(0, new_x, 0)
                return "break" # 拦截，防止系统覆盖
                
            elif self.dragging_sash_index == 1:
                # 右侧
                # sash_place 1 设置的是 (左+中) 的宽度
                # 右侧面板宽度 = Total - new_x
                # 限制：RightWidth <= max_right AND RightWidth >= MIN_SIDE
                # 所以: Total - new_x <= max_right  => new_x >= Total - max_right (Left bound)
                #       Total - new_x >= MIN_SIDE   => new_x <= Total - MIN_SIDE (Right bound)
                
                actual_max_right = max(MIN_SIDE, max_right)
                
                left_bound = total_width - actual_max_right
                right_bound = total_width - MIN_SIDE
                
                new_x = max(left_bound, min(event.x, right_bound))
                
                self.paned_window.sash_place(1, new_x, 0)
                return "break" # 拦截，防止系统覆盖

        except Exception as e:
            # print(f"Drag error: {e}")
            pass

    def apply_default_border(self):
        """应用默认边框"""
        self.canvas_widget.apply_custom_border(self.border_config)
        print("✓ 默认边框已应用")
    
    def bind_mousewheel(self, content_widget, scroll_widget=None):
        """绑定鼠标滚轮事件
        
        Args:
            content_widget: 内容widget,鼠标悬停在这里时触发滚动
            scroll_widget: 实际执行滚动的widget(有yview_scroll方法),如果为None则使用content_widget
        """
        target = scroll_widget if scroll_widget else content_widget
        
        def on_mousewheel(event):
            try:
                delta = event.delta
                if abs(delta) > 100:
                    delta = delta // 120
                target.yview_scroll(-delta, "units")
            except:
                pass
            return "break"
        
        # 递归绑定到content_widget及其所有子控件
        def bind_all(w):
            try:
                w.bind('<MouseWheel>', on_mousewheel)
                for child in w.winfo_children():
                    bind_all(child)
            except:
                pass
        
        bind_all(content_widget)
    
    def load_sticker_images(self):
        """加载贴纸PNG图片"""
        assets_dir = os.path.join(os.path.dirname(__file__), 'assets', 'stickers')
        
        for sticker in STICKER_LIST:
            if 'file' in sticker:
                img_path = os.path.join(assets_dir, sticker['file'])
                if os.path.exists(img_path):
                    try:
                        # 加载并调整大小
                        img = Image.open(img_path).convert('RGBA')
                        img = img.resize((32, 32), Image.Resampling.LANCZOS)
                        photo = ImageTk.PhotoImage(img)
                        self.sticker_images[sticker['id']] = photo
                        self.sticker_photo_refs.append(photo)  # 保持引用
                    except Exception as e:
                        print(f"加载贴纸失败 {sticker['file']}: {e}")
    
    def load_border_preview_images(self):
        """加载边框预览图"""
        frames_dir = os.path.join(os.path.dirname(__file__), 'assets', 'borders', 'frames')
        
        if not os.path.exists(frames_dir):
            return
        
        # 加载所有边框预览图
        for filename in os.listdir(frames_dir):
            if filename.endswith('.png'):
                try:
                    img_path = os.path.join(frames_dir, filename)
                    img = Image.open(img_path).convert('RGBA')
                    # 缩小到缩略图尺寸
                    img.thumbnail((60, 60), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(img)
                    border_id = filename.replace('.png', '')
                    self.border_preview_images[border_id] = photo
                    self.border_photo_refs.append(photo)
                except Exception as e:
                    print(f"加载边框预览失败 {filename}: {e}")
    
    def create_left_panel(self, parent):
        """创建左侧面板 - 现代深色风格"""
        panel = tk.Frame(
            parent, 
            bg=COLORS['panel_bg'], 
            width=150,
            relief=tk.FLAT,
            bd=0,
            highlightthickness=0
        )
        
        # 尺寸选择 - 紧凑风格
        size_label = tk.Label(
            panel,
            text='尺寸',
            font=('SF Pro Text', 10),
            bg=COLORS['panel_bg'],
            fg=COLORS['text_secondary'],
            anchor='w'
        )
        size_label.pack(fill=tk.X, padx=8, pady=(12, 4))
        
        size_frame = tk.Frame(panel, bg=COLORS['panel_bg'])
        size_frame.pack(fill=tk.X, padx=4, pady=(0, 6))
        
        # 保存尺寸按钮引用 (使用Label替代Button，解决macOS颜色不显示问题)
        self.size_preset_buttons = {}
        
        for preset in SIZE_PRESETS:
            is_selected = preset['id'] == self.current_size_preset['id']
            # 使用Label而非Button，macOS上Button的fg颜色不生效
            btn = tk.Label(
                size_frame,
                text=f"{preset['name']}\n{preset['width']}×{preset['height']}",
                bg=COLORS['selected_bg'] if is_selected else COLORS['bg_tertiary'],
                fg=COLORS['text_bright'] if is_selected else COLORS['text_primary'],
                font=('SF Pro Text', 9),
                pady=6,
                padx=8,
                cursor='hand2',
                anchor='center'
            )
            btn.pack(fill=tk.X, padx=2, pady=1)
            btn.bind('<Button-1>', lambda e, p=preset: self.select_size_preset(p))
            self.size_preset_buttons[preset['id']] = btn
            
            # 鼠标悬停效果
            def on_enter(e, b=btn, pid=preset['id']):
                if self.current_size_preset['id'] != pid:
                    b.config(bg=COLORS['hover'])
            def on_leave(e, b=btn, pid=preset['id']):
                if self.current_size_preset['id'] != pid:
                    b.config(bg=COLORS['bg_tertiary'])
            btn.bind('<Enter>', on_enter)
            btn.bind('<Leave>', on_leave)
        
        # 分隔线
        separator1 = tk.Frame(panel, bg=COLORS['separator'], height=1)
        separator1.pack(fill=tk.X, padx=8, pady=8)
        
        # 上传图片 - 紧凑风格
        upload_label = tk.Label(
            panel,
            text='操作',
            font=('SF Pro Text', 10),
            bg=COLORS['panel_bg'],
            fg=COLORS['text_secondary'],
            anchor='w'
        )
        upload_label.pack(fill=tk.X, padx=8, pady=(0, 4))
        
        upload_frame = tk.Frame(panel, bg=COLORS['panel_bg'])
        upload_frame.pack(fill=tk.X, padx=4, pady=(0, 6))
        
        # 使用Label替代Button
        upload_btn = tk.Label(
            upload_frame,
            text='📁 上传图片',
            bg=COLORS['btn_primary'],
            fg=COLORS['text_bright'],
            font=('SF Pro Text', 10, 'bold'),
            pady=8,
            padx=8,
            cursor='hand2'
        )
        upload_btn.pack(fill=tk.X, padx=2, pady=2)
        upload_btn.bind('<Button-1>', lambda e: self.upload_image())
        upload_btn.bind('<Enter>', lambda e: upload_btn.config(bg=COLORS['accent_hover']))
        upload_btn.bind('<Leave>', lambda e: upload_btn.config(bg=COLORS['btn_primary']))
        
        reset_btn = tk.Label(
            upload_frame,
            text='🔄 重置画布',
            bg=COLORS['bg_tertiary'],
            fg=COLORS['text_primary'],
            font=('SF Pro Text', 10),
            pady=8,
            padx=8,
            cursor='hand2'
        )
        reset_btn.pack(fill=tk.X, padx=2, pady=2)
        reset_btn.bind('<Button-1>', lambda e: self.reset_image())
        reset_btn.bind('<Enter>', lambda e: reset_btn.config(bg=COLORS['hover']))
        reset_btn.bind('<Leave>', lambda e: reset_btn.config(bg=COLORS['bg_tertiary']))
        
        # 分隔线
        separator2 = tk.Frame(panel, bg=COLORS['separator'], height=1)
        separator2.pack(fill=tk.X, padx=8, pady=8)
        
        # 预设主题区域
        theme_label = tk.Label(
            panel,
            text='预设主题',
            font=('SF Pro Text', 10),
            bg=COLORS['panel_bg'],
            fg=COLORS['text_secondary'],
            anchor='w'
        )
        theme_label.pack(fill=tk.X, padx=8, pady=(0, 4))
        
        # 预设主题网格 (2列4行)
        self.left_preset_grid = tk.Frame(panel, bg=COLORS['panel_bg'])
        self.left_preset_grid.pack(fill=tk.X, padx=4, pady=(0, 6))
        
        # 初始化预设主题按钮
        self.update_left_preset_display()
        
        # 自动保存预设勾选框
        self.auto_save_preset_var = tk.BooleanVar(value=True)  # 默认勾选
        auto_save_check = tk.Checkbutton(
            panel,
            text='导出时自动保存预设',
            variable=self.auto_save_preset_var,
            font=('SF Pro Text', 9),
            bg=COLORS['panel_bg'],
            fg=COLORS['text_secondary'],
            selectcolor=COLORS['bg_tertiary'],
            activebackground=COLORS['panel_bg'],
            activeforeground=COLORS['text_primary'],
            cursor='hand2'
        )
        auto_save_check.pack(fill=tk.X, padx=8, pady=(0, 8))
        
        return panel
    
    def create_center_panel(self, parent):
        """创建中间画布面板 - 现代深色风格"""
        panel = tk.Frame(
            parent,
            bg=COLORS['bg'],
            relief=tk.FLAT,
            bd=0,
            highlightthickness=0
        )
        
        # 工具栏 - 现代深色风格
        toolbar = tk.Frame(panel, bg=COLORS['bg_secondary'], height=44)
        toolbar.pack(fill=tk.X, padx=0, pady=0)
        
        # 左侧按钮 - 使用Label替代Button
        left_buttons = tk.Frame(toolbar, bg=COLORS['bg_secondary'])
        left_buttons.pack(side=tk.LEFT, padx=8, pady=6)
        
        btn_undo = tk.Label(
            left_buttons,
            text='↶ 撤销',
            font=('SF Pro Text', 10),
            bg=COLORS['bg_tertiary'],
            fg=COLORS['text_primary'],
            padx=12,
            pady=6,
            cursor='hand2'
        )
        btn_undo.pack(side=tk.LEFT, padx=(0, 4))
        btn_undo.bind('<Button-1>', lambda e: self.undo())
        btn_undo.bind('<Enter>', lambda e: btn_undo.config(bg=COLORS['hover']))
        btn_undo.bind('<Leave>', lambda e: btn_undo.config(bg=COLORS['bg_tertiary']))
        
        btn_redo = tk.Label(
            left_buttons,
            text='↷ 重做',
            font=('SF Pro Text', 10),
            bg=COLORS['bg_tertiary'],
            fg=COLORS['text_primary'],
            padx=12,
            pady=6,
            cursor='hand2'
        )
        btn_redo.pack(side=tk.LEFT, padx=(0, 4))
        btn_redo.bind('<Button-1>', lambda e: self.redo())
        btn_redo.bind('<Enter>', lambda e: btn_redo.config(bg=COLORS['hover']))
        btn_redo.bind('<Leave>', lambda e: btn_redo.config(bg=COLORS['bg_tertiary']))
        
        # 中间：一键随机按钮
        center_frame = tk.Frame(toolbar, bg=COLORS['bg_secondary'])
        center_frame.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
        
        self.random_btn = tk.Label(
            center_frame,
            text='🎲 摇一摇爆文骰',
            font=('SF Pro Text', 11, 'bold'),
            bg=COLORS['accent'],
            fg='white',
            padx=16,
            pady=8,
            cursor='hand2'
        )
        self.random_btn.pack(pady=(8, 8))
        self.random_btn.bind('<Button-1>', lambda e: self.one_click_randomize())
        self.random_btn.bind('<Enter>', lambda e: self.random_btn.config(bg='#2563DE')) # Darker Accent
        self.random_btn.bind('<Leave>', lambda e: self.random_btn.config(bg=COLORS['accent']))
        
        # 右侧导出按钮 - 使用Label替代Button
        right_buttons = tk.Frame(toolbar, bg=COLORS['bg_secondary'])
        right_buttons.pack(side=tk.RIGHT, padx=8, pady=6)
        
        btn_export = tk.Label(
            right_buttons,
            text='💾 导出',
            bg=COLORS['success'],
            fg=COLORS['text_bright'],
            font=('SF Pro Text', 10, 'bold'),
            padx=14,
            pady=6,
            cursor='hand2'
        )
        btn_export.pack(side=tk.RIGHT)
        btn_export.bind('<Button-1>', lambda e: self.export_image())
        btn_export.bind('<Enter>', lambda e: btn_export.config(bg='#28A745'))
        btn_export.bind('<Leave>', lambda e: btn_export.config(bg=COLORS['success']))
        
        # 画布 - 按比例计算显示尺寸（占可用空间的90%）
        preset = self.current_size_preset
        # 获取窗口尺寸，计算可用空间（减去左右面板）
        window_width = self.winfo_screenwidth() * 0.85  # 窗口宽度
        window_height = self.winfo_screenheight() * 0.85  # 窗口高度
        # 左面板约120px，右面板约320px，工具栏约50px，边距约40px
        available_width = int((window_width - 120 - 320 - 40) * 0.9)
        available_height = int((window_height - 50 - 40) * 0.9)
        
        ratio = preset['width'] / preset['height']
        
        if ratio > available_width / available_height:
            # 宽图，以宽度为准
            display_width = available_width
            display_height = int(display_width / ratio)
        else:
            # 高图或方图，以高度为准
            display_height = available_height
            display_width = int(display_height * ratio)
        
        self.canvas_widget = CanvasWidget(
            panel,
            width=display_width,
            height=display_height
        )
        self.canvas_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        return panel
    
    def create_right_panel(self, parent):
        """创建右侧面板 - 现代深色风格"""
        panel = tk.Frame(
            parent,
            bg=COLORS['panel_bg'],
            width=240,
            relief=tk.FLAT,
            bd=0,
            highlightthickness=0
        )
        
        # 配置 ttk 标签页样式 (备用)
        style = ttk.Style()
        style.theme_use('default')
        
        # --- 自定义两行标签页实现 ---
        # 标签页定义: (id, emoji, name)
        self.tab_definitions = [
            # 第一行 (Row 0) - 核心编辑
            ('basic', '📐', '编辑'),
            ('background', '🎨', '背景'),
            ('border', '🖼️', '边框'),
            ('text', '🔤', '文字'),
            # 第二行 (Row 1) - 装饰与工具
            ('sticker', '✨', '贴纸'),
            ('layer', '📚', '图层'),
            ('history', '📝', '记录'),
            ('batch', '⚡', '批量'),
        ]
        
        # 标签页容器
        self.tab_header_frame = tk.Frame(panel, bg=COLORS['panel_bg'])
        self.tab_header_frame.pack(fill=tk.X, padx=0, pady=0)
        
        # 两行标签按钮
        self.tab_row_frames = [
            tk.Frame(self.tab_header_frame, bg=COLORS['panel_bg']),
            tk.Frame(self.tab_header_frame, bg=COLORS['panel_bg'])
        ]
        
        self.tab_buttons = {}
        self.tab_frames = {}
        self.current_tab_id = 'background'
        self.current_active_row = 0
        
        # 创建标签按钮
        for i, (tab_id, emoji, name) in enumerate(self.tab_definitions):
            row = i // 4  # 0-3 在第一行, 4-7 在第二行
            
            btn = tk.Label(
                self.tab_row_frames[row],
                text=f'{emoji} {name}',
                font=('SF Pro Text', 9),
                bg=COLORS['bg_tertiary'],
                fg=COLORS['text_secondary'],
                padx=6, pady=4,
                cursor='hand2'
            )
            btn.pack(side=tk.LEFT, padx=1, pady=2)
            btn.bind('<Button-1>', lambda e, tid=tab_id: self.switch_tab(tid))
            self.tab_buttons[tab_id] = btn
        
        # 内容容器
        self.tab_content_frame = tk.Frame(panel, bg=COLORS['panel_bg'])
        self.tab_content_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建各标签页内容Frame
        for tab_id, _, _ in self.tab_definitions:
            frame = tk.Frame(self.tab_content_frame, bg=COLORS['panel_bg'])
            self.tab_frames[tab_id] = frame
        
        # 初始化各标签页内容
        self.create_background_tab(self.tab_frames['background'])
        self.create_border_tab(self.tab_frames['border'])
        self.create_sticker_tab(self.tab_frames['sticker'])
        self.create_text_tab(self.tab_frames['text'])
        self.create_basic_tools_tab(self.tab_frames['basic'])
        self.create_batch_tab(self.tab_frames['batch'])
        self.create_layer_tab(self.tab_frames['layer'])
        self.create_history_tab(self.tab_frames['history'])
        
        # 初始显示
        self._update_tab_rows()
        # [UX] 默认打开文字Tab
        self.switch_tab('text')
        
        # [UX] 启动时自动点击爆文骰子 (不记录历史)
        # 延迟一点执行等待界面加载完毕
        self.after(500, lambda: self.one_click_randomize(record_history=False))
        
        # 绑定 Tab 键切换标签
        self.bind('<Tab>', self.next_tab)
        
        return panel
    
    def switch_tab(self, tab_id):
        """切换标签页"""
        if tab_id == self.current_tab_id:
            return
        
        # 更新当前标签页
        self.current_tab_id = tab_id
        
        # 判断激活的是哪一行
        tab_index = [t[0] for t in self.tab_definitions].index(tab_id)
        new_active_row = tab_index // 4
        
        # 如果激活行变化，需要交换行顺序
        if new_active_row != self.current_active_row:
            self.current_active_row = new_active_row
            self._update_tab_rows()
        
        # 更新按钮样式
        for tid, btn in self.tab_buttons.items():
            if tid == tab_id:
                btn.config(bg=COLORS['panel_bg'], fg=COLORS['accent'])
            else:
                btn.config(bg=COLORS['bg_tertiary'], fg=COLORS['text_secondary'])
        
        # 隐藏所有内容，显示当前内容
        for tid, frame in self.tab_frames.items():
            frame.pack_forget()
        self.tab_frames[tab_id].pack(fill=tk.BOTH, expand=True)
        
        # 如果是历史记录Tab，刷新显示
        if tab_id == 'history':
            self.update_history_display()
    
    def _update_tab_rows(self):
        """更新标签行顺序：激活行在下面"""
        for row_frame in self.tab_row_frames:
            row_frame.pack_forget()
        
        if self.current_active_row == 0:
            # Row 1 在上，Row 0 在下
            self.tab_row_frames[1].pack(fill=tk.X)
            self.tab_row_frames[0].pack(fill=tk.X)
        else:
            # Row 0 在上，Row 1 在下
            self.tab_row_frames[0].pack(fill=tk.X)
            self.tab_row_frames[1].pack(fill=tk.X)
    
    def create_basic_tools_tab(self, parent):
        """基础工具标签页 - 现代风格"""
        # 创建滚动区域
        scroll_canvas = tk.Canvas(parent, bg=COLORS['panel_bg'], highlightthickness=0)
        scrollbar = tk.Scrollbar(parent, orient='vertical', command=scroll_canvas.yview)
        scroll_frame = tk.Frame(scroll_canvas, bg=COLORS['panel_bg'])
        
        scroll_frame.bind('<Configure>', lambda e: scroll_canvas.configure(scrollregion=scroll_canvas.bbox('all')))
        scroll_canvas.create_window((0, 0), window=scroll_frame, anchor='nw')
        scroll_canvas.configure(yscrollcommand=scrollbar.set)
        
        scroll_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 绑定鼠标滚轮
        self.bind_mousewheel(scroll_frame, scroll_canvas)
        
        # 图片操作标题
        tk.Label(
            scroll_frame, text='🔄 变换操作', font=('SF Pro Display', 13, 'bold'),
            bg=COLORS['panel_bg'], fg=COLORS['text_primary'], anchor='w'
        ).pack(fill=tk.X, padx=16, pady=(16, 8))
        
        transform_frame = tk.Frame(scroll_frame, bg=COLORS['panel_bg'])
        transform_frame.pack(fill=tk.X, padx=12, pady=(0, 12))
        
        transforms = [
            ('↺ 逆时针90°', lambda: self.apply_transform('rotate', -90)),
            ('↻ 顺时针90°', lambda: self.apply_transform('rotate', 90)),
            ('⇄ 水平翻转', lambda: self.apply_transform('flip_h')),
            ('⇅ 垂直翻转', lambda: self.apply_transform('flip_v')),
        ]
        
        for text, command in transforms:
            btn = tk.Label(
                transform_frame, text=text, bg=COLORS['bg_tertiary'], fg=COLORS['text_primary'],
                font=('SF Pro Text', 11), pady=10, cursor='hand2'
            )
            btn.pack(fill=tk.X, padx=4, pady=2)
            btn.bind('<Button-1>', lambda e, c=command: c())
            btn.bind('<Enter>', lambda e, b=btn: b.config(bg=COLORS['hover']))
            btn.bind('<Leave>', lambda e, b=btn: b.config(bg=COLORS['bg_tertiary']))
        
        # 滤镜标题
        tk.Label(
            scroll_frame, text='🎨 滤镜效果', font=('SF Pro Display', 13, 'bold'),
            bg=COLORS['panel_bg'], fg=COLORS['text_primary'], anchor='w'
        ).pack(fill=tk.X, padx=16, pady=(12, 8))
        
        filter_frame = tk.Frame(scroll_frame, bg=COLORS['panel_bg'])
        filter_frame.pack(fill=tk.X, padx=12, pady=(0, 12))
        
        filters = [
            ('🖤 黑白', 'grayscale'),
            ('🔆 锐化', 'sharpen'),
            ('🌫️ 模糊', 'blur'),
            ('✨ 平滑', 'smooth'),
            ('📐 轮廓', 'contour'),
            ('🗿 浮雕', 'emboss'),
        ]
        
        filter_grid = tk.Frame(filter_frame, bg=COLORS['panel_bg'])
        filter_grid.pack(fill=tk.X)
        
        # 初始化滤镜状态和按钮引用
        self.active_filters = set()  # 当前激活的滤镜
        self.filter_buttons = {}  # 按钮引用
        self.filter_base_texts = {}  # 原始文本
        
        for idx, (text, filter_type) in enumerate(filters):
            row, col = idx // 2, idx % 2
            btn = tk.Label(
                filter_grid, text=text, bg=COLORS['bg_tertiary'], fg=COLORS['text_primary'],
                font=('SF Pro Text', 10), pady=8, padx=8, cursor='hand2', width=10
            )
            btn.grid(row=row, column=col, padx=2, pady=2, sticky='ew')
            btn.bind('<Button-1>', lambda e, f=filter_type, b=btn: self.toggle_filter(f, b))
            btn.bind('<Enter>', lambda e, b=btn: b.config(bg=COLORS['hover']) if b.cget('bg') != COLORS['accent'] else None)
            btn.bind('<Leave>', lambda e, b=btn, f=filter_type: b.config(bg=COLORS['accent'] if f in self.active_filters else COLORS['bg_tertiary']))
            
            self.filter_buttons[filter_type] = btn
            self.filter_base_texts[filter_type] = text
        
        filter_grid.columnconfigure(0, weight=1)
        filter_grid.columnconfigure(1, weight=1)
        
        # 调整标题
        tk.Label(
            scroll_frame, text='⚡ 图片调整', font=('SF Pro Display', 13, 'bold'),
            bg=COLORS['panel_bg'], fg=COLORS['text_primary'], anchor='w'
        ).pack(fill=tk.X, padx=16, pady=(12, 8))
        
        adjust_frame = tk.Frame(scroll_frame, bg=COLORS['panel_bg'])
        adjust_frame.pack(fill=tk.X, padx=16, pady=(0, 12))
        
        # 亮度行
        brightness_row = tk.Frame(adjust_frame, bg=COLORS['panel_bg'])
        brightness_row.pack(fill=tk.X, pady=(0, 8))
        
        tk.Label(brightness_row, text='亮度', font=('SF Pro Text', 10), width=6,
            bg=COLORS['panel_bg'], fg=COLORS['text_secondary'], anchor='w').pack(side=tk.LEFT)
        
        self.brightness_scale = tk.Scale(
            brightness_row, from_=0.2, to=2.0, resolution=0.1, orient=tk.HORIZONTAL,
            bg=COLORS['bg_tertiary'], fg=COLORS['text_primary'], highlightthickness=0,
            troughcolor=COLORS['separator'], length=150, showvalue=True
        )
        self.brightness_scale.set(1.0)
        self.brightness_scale.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.brightness_scale.bind('<ButtonRelease-1>', lambda e: self.apply_adjustment('brightness'))
        
        brightness_reset = tk.Label(brightness_row, text='⟲', font=('SF Pro Text', 12),
            bg=COLORS['bg_tertiary'], fg=COLORS['text_primary'], padx=6, pady=2, cursor='hand2')
        brightness_reset.pack(side=tk.RIGHT, padx=(4, 0))
        brightness_reset.bind('<Button-1>', lambda e: self.reset_single_adjustment('brightness'))
        brightness_reset.bind('<Enter>', lambda e: brightness_reset.config(bg=COLORS['hover']))
        brightness_reset.bind('<Leave>', lambda e: brightness_reset.config(bg=COLORS['bg_tertiary']))
        
        # 对比度行
        contrast_row = tk.Frame(adjust_frame, bg=COLORS['panel_bg'])
        contrast_row.pack(fill=tk.X, pady=(0, 8))
        
        tk.Label(contrast_row, text='对比度', font=('SF Pro Text', 10), width=6,
            bg=COLORS['panel_bg'], fg=COLORS['text_secondary'], anchor='w').pack(side=tk.LEFT)
        
        self.contrast_scale = tk.Scale(
            contrast_row, from_=0.2, to=2.0, resolution=0.1, orient=tk.HORIZONTAL,
            bg=COLORS['bg_tertiary'], fg=COLORS['text_primary'], highlightthickness=0,
            troughcolor=COLORS['separator'], length=150, showvalue=True
        )
        self.contrast_scale.set(1.0)
        self.contrast_scale.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.contrast_scale.bind('<ButtonRelease-1>', lambda e: self.apply_adjustment('contrast'))
        
        contrast_reset = tk.Label(contrast_row, text='⟲', font=('SF Pro Text', 12),
            bg=COLORS['bg_tertiary'], fg=COLORS['text_primary'], padx=6, pady=2, cursor='hand2')
        contrast_reset.pack(side=tk.RIGHT, padx=(4, 0))
        contrast_reset.bind('<Button-1>', lambda e: self.reset_single_adjustment('contrast'))
        contrast_reset.bind('<Enter>', lambda e: contrast_reset.config(bg=COLORS['hover']))
        contrast_reset.bind('<Leave>', lambda e: contrast_reset.config(bg=COLORS['bg_tertiary']))
        
        # 饱和度行
        saturation_row = tk.Frame(adjust_frame, bg=COLORS['panel_bg'])
        saturation_row.pack(fill=tk.X, pady=(0, 8))
        
        tk.Label(saturation_row, text='饱和度', font=('SF Pro Text', 10), width=6,
            bg=COLORS['panel_bg'], fg=COLORS['text_secondary'], anchor='w').pack(side=tk.LEFT)
        
        self.saturation_scale = tk.Scale(
            saturation_row, from_=0.0, to=2.0, resolution=0.1, orient=tk.HORIZONTAL,
            bg=COLORS['bg_tertiary'], fg=COLORS['text_primary'], highlightthickness=0,
            troughcolor=COLORS['separator'], length=150, showvalue=True
        )
        self.saturation_scale.set(1.0)
        self.saturation_scale.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.saturation_scale.bind('<ButtonRelease-1>', lambda e: self.apply_adjustment('saturation'))
        
        saturation_reset = tk.Label(saturation_row, text='⟲', font=('SF Pro Text', 12),
            bg=COLORS['bg_tertiary'], fg=COLORS['text_primary'], padx=6, pady=2, cursor='hand2')
        saturation_reset.pack(side=tk.RIGHT, padx=(4, 0))
        saturation_reset.bind('<Button-1>', lambda e: self.reset_single_adjustment('saturation'))
        saturation_reset.bind('<Enter>', lambda e: saturation_reset.config(bg=COLORS['hover']))
        saturation_reset.bind('<Leave>', lambda e: saturation_reset.config(bg=COLORS['bg_tertiary']))
        
        # 重置按钮
        reset_btn = tk.Label(
            scroll_frame, text='🔄 重置图片', bg=COLORS['accent'], fg='white',
            font=('SF Pro Text', 11, 'bold'), pady=10, cursor='hand2'
        )
        reset_btn.pack(fill=tk.X, padx=16, pady=(8, 16))
        reset_btn.bind('<Button-1>', lambda e: self.reset_image_and_sliders())
        reset_btn.bind('<Enter>', lambda e: reset_btn.config(bg='#0066CC'))
        reset_btn.bind('<Leave>', lambda e: reset_btn.config(bg=COLORS['accent']))
    
    def create_decoration_tab(self, parent):
        """装饰标签页 - 现代风格"""
        # 贴纸部分
        sticker_label = tk.Label(
            parent,
            text='贴纸',
            font=('SF Pro Display', 13, 'bold'),
            bg=COLORS['panel_bg'],
            fg=COLORS['text_primary'],
            anchor='w'
        )
        sticker_label.pack(fill=tk.X, padx=16, pady=(16, 8))
        
        # 贴纸网格
        sticker_grid = tk.Frame(parent, bg=COLORS['panel_bg'])
        sticker_grid.pack(fill=tk.X, padx=12, pady=(0, 16))
        
        for idx, sticker in enumerate(STICKER_LIST):
            row = idx // 4
            col = idx % 4
            
            # 使用Label替代Button
            if sticker['id'] in self.sticker_images:
                # 使用PNG图片
                btn = tk.Label(
                    sticker_grid,
                    image=self.sticker_images[sticker['id']],
                    bg=COLORS['bg_tertiary'],
                    cursor='hand2'
                )
            else:
                # 使用emoji
                btn = tk.Label(
                    sticker_grid,
                    text=sticker['emoji'],
                    font=(get_emoji_font_name(), 28),
                    bg=COLORS['bg_tertiary'],
                    width=2,
                    height=1,
                    cursor='hand2'
                )
            btn.grid(row=row, column=col, padx=4, pady=4)
            btn.bind('<Button-1>', lambda e, s=sticker: self.add_sticker(s))
            btn.bind('<Enter>', lambda e, b=btn: b.config(bg=COLORS['hover']))
            btn.bind('<Leave>', lambda e, b=btn: b.config(bg=COLORS['bg_tertiary']))
        
        # 分隔线
        separator = tk.Frame(parent, bg=COLORS['separator'], height=1)
        separator.pack(fill=tk.X, padx=16, pady=12)
        
        # 边框部分
        border_label = tk.Label(
            parent,
            text='边框',
            font=('SF Pro Display', 13, 'bold'),
            bg=COLORS['panel_bg'],
            fg=COLORS['text_primary'],
            anchor='w'
        )
        border_label.pack(fill=tk.X, padx=16, pady=(8, 8))
        
        # 边框分类选择
        category_frame = tk.Frame(parent, bg=COLORS['panel_bg'])
        category_frame.pack(fill=tk.X, padx=16, pady=(0, 8))
        
        self.border_category_buttons = {}
        for category_id, category_info in BORDER_CATEGORIES.items():
            is_selected = category_id == self.selected_border_category
            btn = tk.Label(
                category_frame,
                text=category_info['name'],
                bg=COLORS['selected_bg'] if is_selected else COLORS['bg_tertiary'],
                fg=COLORS['text_bright'] if is_selected else COLORS['text_primary'],
                font=('SF Pro Text', 10, 'bold' if is_selected else 'normal'),
                padx=12,
                pady=8,
                cursor='hand2'
            )
            btn.pack(side=tk.LEFT, padx=2)
            btn.bind('<Button-1>', lambda e, c=category_id: self.select_border_category(c))
            self.border_category_buttons[category_id] = btn
        
        # 颜色选择
        color_label = tk.Label(
            parent,
            text='颜色',
            font=('SF Pro Text', 11),
            bg=COLORS['panel_bg'],
            fg=COLORS['text_secondary'],
            anchor='w'
        )
        color_label.pack(fill=tk.X, padx=16, pady=(8, 4))
        
        color_grid = tk.Frame(parent, bg=COLORS['panel_bg'])
        color_grid.pack(fill=tk.X, padx=16, pady=(0, 8))
        
        self.border_color_buttons = {}
        current_category = BORDER_CATEGORIES[self.selected_border_category]
        for idx, color_id in enumerate(current_category['colors']):
            if color_id in BORDER_COLORS:
                color_info = BORDER_COLORS[color_id]
                row = idx // 6
                col = idx % 6
                
                # 使用Canvas替代Button显示颜色
                btn = tk.Canvas(
                    color_grid,
                    bg=color_info['preview'],
                    width=28,
                    height=20,
                    highlightthickness=2 if color_id == self.selected_border_color else 1,
                    highlightbackground=COLORS['accent'] if color_id == self.selected_border_color else COLORS['separator'],
                    cursor='hand2'
                )
                btn.grid(row=row, column=col, padx=3, pady=3)
                btn.bind('<Button-1>', lambda e, c=color_id: self.select_border_color(c))
                self.border_color_buttons[color_id] = btn
        
        # 边框样式网格（滚动）
        style_container = tk.Frame(parent, bg=COLORS['panel_bg'])
        style_container.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 12))
        
        style_canvas = tk.Canvas(
            style_container,
            bg=COLORS['panel_bg'],
            highlightthickness=0,
            bd=0
        )
        style_scrollbar = tk.Scrollbar(
            style_container,
            orient='vertical',
            command=style_canvas.yview
        )
        self.border_style_frame = tk.Frame(style_canvas, bg=COLORS['panel_bg'])
        
        style_canvas.create_window((0, 0), window=self.border_style_frame, anchor='nw')
        style_canvas.configure(yscrollcommand=style_scrollbar.set)
        
        # 初始化边框样式显示
        self.update_border_styles_display()
        
        self.border_style_frame.update_idletasks()
        style_canvas.config(scrollregion=style_canvas.bbox('all'))
        
        style_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        style_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def select_border_category(self, category_id):
        """选择边框分类"""
        self.selected_border_category = category_id
        
        # 更新分类按钮样式 (Label)
        for cat_id, btn in self.border_category_buttons.items():
            if cat_id == category_id:
                btn.config(
                    bg=COLORS['selected_bg'],
                    fg=COLORS['text_bright'],
                    font=('SF Pro Text', 10, 'bold')
                )
            else:
                btn.config(
                    bg=COLORS['bg_tertiary'],
                    fg=COLORS['text_primary'],
                    font=('SF Pro Text', 10)
                )
        
        # 更新边框样式显示
        self.update_border_styles_display()
    
    def select_border_color(self, color_id):
        """选择边框颜色"""
        self.selected_border_color = color_id
        
        # 同步更新 border_config 的颜色 (从 BORDER_COLORS 获取实际颜色值)
        from constants import BORDER_COLORS
        if color_id in BORDER_COLORS:
            self.border_config['color'] = BORDER_COLORS[color_id]['hex']
        
        # 更新颜色按钮样式
        for c_id, btn in self.border_color_buttons.items():
            if c_id == color_id:
                btn.config(highlightthickness=2, highlightbackground=COLORS['accent'])
            else:
                btn.config(highlightthickness=1, highlightbackground=COLORS['separator'])
        
        # 更新边框样式显示
        self.update_border_styles_display()
    
    def update_border_styles_display(self):
        """更新边框样式显示"""
        # 清空现有内容
        for widget in self.border_style_frame.winfo_children():
            widget.destroy()
        
        # 获取当前分类的样式
        category = BORDER_CATEGORIES[self.selected_border_category]
        
        for style in category['styles']:
            # 构建边框ID
            border_id = f"{self.selected_border_category}_{style}_{self.selected_border_color}"
            
            # 创建边框按钮
            btn_frame = tk.Frame(self.border_style_frame, bg='white', highlightthickness=1, highlightbackground=COLORS['separator'])
            btn_frame.pack(fill=tk.X, padx=4, pady=4)
            
            # 如果有预览图，显示预览图
            if border_id in self.border_preview_images:
                img_label = tk.Label(
                    btn_frame,
                    image=self.border_preview_images[border_id],
                    bg='white',
                    cursor='hand2'
                )
                img_label.pack(side=tk.LEFT, padx=8, pady=8)
                img_label.bind('<Button-1>', lambda e, bid=border_id: self.apply_border(bid))
            
            # 显示边框名称
            name = BORDER_STYLE_NAMES.get(style, style)
            color_name = BORDER_COLORS.get(self.selected_border_color, {}).get('name', '')
            full_name = f"{name} - {color_name}"
            
            name_label = tk.Label(
                btn_frame,
                text=full_name,
                font=('SF Pro Text', 11),
                bg='white',
                fg=COLORS['text_primary'],
                anchor='w',
                cursor='hand2'
            )
            name_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8, pady=12)
            name_label.bind('<Button-1>', lambda e, bid=border_id: self.apply_border(bid))
            
            # 悬停效果
            def on_enter(e, frame=btn_frame):
                frame.config(bg=COLORS['hover'])
                for child in frame.winfo_children():
                    child.config(bg=COLORS['hover'])
            
            def on_leave(e, frame=btn_frame):
                frame.config(bg='white')
                for child in frame.winfo_children():
                    child.config(bg='white')
            
            btn_frame.bind('<Enter>', on_enter)
            btn_frame.bind('<Leave>', on_leave)
            for child in btn_frame.winfo_children():
                child.bind('<Enter>', on_enter)
                child.bind('<Leave>', on_leave)
    
    def apply_border(self, border_id):
        """应用边框 - 直接生效"""
        # 解析border_id: category_style_color
        parts = border_id.split('_')
        if len(parts) >= 3:
            category = parts[0]
            style = parts[1]
            color = parts[2]
            
            # 加载边框图片
            frames_dir = os.path.join(os.path.dirname(__file__), 'assets', 'borders', 'frames')
            border_path = os.path.join(frames_dir, f"{border_id}.png")
            
            if os.path.exists(border_path):
                try:
                    # 应用到画布
                    border_img = Image.open(border_path).convert('RGBA')
                    self.canvas_widget.apply_border_image(border_img)
                    print(f"✓ 边框已应用: {border_id}")
                except Exception as e:
                    print(f"应用边框失败: {e}")
            else:
                print(f"边框文件不存在: {border_path}")
    
    def create_text_tab(self, parent):
        """文字编辑标签页"""
        from image_processor import TextLayer
        from tkinter import ttk
        
        # 滚动区域
        scroll_canvas = tk.Canvas(parent, bg=COLORS['panel_bg'], highlightthickness=0)
        scrollbar = tk.Scrollbar(parent, orient='vertical', command=scroll_canvas.yview)
        text_frame = tk.Frame(scroll_canvas, bg=COLORS['panel_bg'])
        
        text_frame.bind('<Configure>', lambda e: scroll_canvas.configure(scrollregion=scroll_canvas.bbox('all')))
        scroll_canvas.create_window((0, 0), window=text_frame, anchor='nw')
        scroll_canvas.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        scroll_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 绑定滚轮
        self.bind_mousewheel(text_frame, scroll_canvas)
        
        # [FEATURE] AI 爆文生成
        ai_frame = tk.Frame(text_frame, bg=COLORS['panel_bg'])
        ai_frame.pack(fill=tk.X, padx=12, pady=(12, 0))
        
        # 顶部按钮行
        ai_header = tk.Frame(ai_frame, bg=COLORS['panel_bg'])
        ai_header.pack(fill=tk.X)
        
        # AI 展开按钮 (左对齐，优化样式)
        self.ai_toggle_btn = tk.Label(ai_header, text='✨ AI 帮我写', font=('SF Pro Display', 11, 'bold'),
                                     bg=COLORS['panel_bg'], fg=COLORS['accent'],  # Transparent background
                                     padx=0, pady=6, cursor='hand2', relief='flat', anchor='w')
        self.ai_toggle_btn.pack(side=tk.LEFT, anchor='w', padx=12) # Padding via pack
        self.ai_toggle_btn.bind('<Button-1>', lambda e: self._toggle_ai_panel())
        
        # Hover effect
        self.ai_toggle_btn.bind('<Enter>', lambda e: self.ai_toggle_btn.config(fg=COLORS['accent_hover']))
        self.ai_toggle_btn.bind('<Leave>', lambda e: self.ai_toggle_btn.config(fg=COLORS['accent']))
        
        # [NEW] Key 设置按钮 (放在标题旁，默认隐藏)
        self.ai_config_btn = tk.Label(ai_header, text='⚙️', font=('SF Pro Text', 12),
                                     bg=COLORS['panel_bg'], fg=COLORS['text_secondary'],
                                     cursor='hand2')
        # 初始不显示，展开时才显示
        self.ai_config_btn.bind('<Button-1>', lambda e: self._configure_api_key())
        Tooltip(self.ai_config_btn, "配置 DeepSeek API Key", delay=200)
        
        # AI 输入面板 (默认隐藏)
        self.ai_panel = tk.Frame(ai_frame, bg=COLORS['bg_secondary'], padx=12, pady=12)
        self.ai_panel_visible = False
        
        # 使用固定宽度的标签列，使输入框对齐
        label_width = 5  # 字符数
        
        # 主题输入 (Row 0)
        tk.Label(self.ai_panel, text='主题:', font=('SF Pro Text', 10), width=label_width, anchor='e',
                 bg=COLORS['bg_secondary'], fg=COLORS['text_secondary']).grid(row=0, column=0, sticky='e', pady=6)
        
        self.ai_topic_entry = ModernStyles.create_entry(self.ai_panel, width=20)
        self.ai_topic_entry.grid(row=0, column=1, sticky='w', padx=(8, 0), pady=6)
        
        self.ai_topic_entry = ModernStyles.create_entry(self.ai_panel, width=20)
        self.ai_topic_entry.grid(row=0, column=1, sticky='w', padx=(8, 0), pady=6)
        # [MOVED] Key 设置按钮移至标题栏
        self.ai_topic_entry.insert(0, '')
        Tooltip(self.ai_topic_entry, '输入具体主题，如「SCL90心理测试」「iPhone16体验」\n越具体，AI 理解越准确', delay=500)
        
        # 风格选择 (Row 1)
        tk.Label(self.ai_panel, text='风格:', font=('SF Pro Text', 10), width=label_width, anchor='e',
                 bg=COLORS['bg_secondary'], fg=COLORS['text_secondary']).grid(row=1, column=0, sticky='e', pady=6)
        
        self.ai_style_var = tk.StringVar(value="随机")
        style_cb = ModernStyles.create_combobox(self.ai_panel, self.ai_style_var,
                                              values=["随机", "温柔干货", "趣味测评", "走心文案"], 
                                              width=17)
        style_cb.grid(row=1, column=1, sticky='w', padx=(8, 0), pady=6)
        
        # 保存到文件 (Row 2) - Fixed alignment
        tk.Label(self.ai_panel, text='保存:', font=('SF Pro Text', 10), width=label_width, anchor='e',
                 bg=COLORS['bg_secondary'], fg=COLORS['text_secondary']).grid(row=2, column=0, sticky='ne', pady=6)
        
        save_btn_frame = tk.Frame(self.ai_panel, bg=COLORS['bg_secondary'])
        save_btn_frame.grid(row=2, column=1, sticky='w', padx=(8, 0), pady=6)
        
        # 下载模版按钮 (Link style)
        def _download_ai_template():
            import shutil
            template_path = os.path.join(os.path.dirname(__file__), 'assets', 'template', '文案保存模版.xlsx')
            if os.path.exists(template_path):
                save_path = filedialog.asksaveasfilename(
                    defaultextension='.xlsx',
                    filetypes=[('Excel 文件', '*.xlsx')],
                    initialfile='AI文案保存模版.xlsx'
                )
                if save_path:
                    shutil.copy(template_path, save_path)
                    messagebox.showinfo('下载成功', f'模版已保存到:\n{save_path}')
            else:
                messagebox.showerror('错误', '模版文件不存在')
                
        download_tpl_btn = tk.Label(save_btn_frame, text='下载模版', font=('SF Pro Text', 9, 'underline'),
                                   bg=COLORS['bg_secondary'], fg=COLORS['accent'], cursor='hand2')
        download_tpl_btn.pack(side=tk.LEFT, padx=(0, 8))
        download_tpl_btn.bind('<Button-1>', lambda e: _download_ai_template())
        
        # 选择保存文件 & 打开按钮 (Button style)
        saved_ai_path = getattr(self, 'ai_save_path', '')
        self.ai_save_path_var = tk.StringVar(value=saved_ai_path)
        
        def _select_ai_save_file():
            path = filedialog.askopenfilename(
                filetypes=[('Excel 文件', '*.xlsx')],
                title='选择 AI 文案保存文件'
            )
            if path:
                self.ai_save_path_var.set(path)
                self.ai_save_path = path
                self.ai_save_path_label.config(text=os.path.basename(path)) # Show filename only
                self.save_settings()
                Tooltip(self.ai_save_path_label, path) # Show full path on hover
                
        select_file_btn = tk.Label(save_btn_frame, text='选择文件', font=('SF Pro Text', 9),
                                  bg=COLORS['bg_tertiary'], fg='#FFFFFF', padx=8, pady=3, cursor='hand2') # High contrast
        select_file_btn.pack(side=tk.LEFT, padx=(0, 4))
        select_file_btn.bind('<Button-1>', lambda e: _select_ai_save_file())
        select_file_btn.bind('<Enter>', lambda e: select_file_btn.config(bg=COLORS['accent']))
        select_file_btn.bind('<Leave>', lambda e: select_file_btn.config(bg=COLORS['bg_tertiary']))
        
        # 提示图标
        tip_label = tk.Label(save_btn_frame, text='?', font=('SF Pro Text', 9, 'bold'),
                            bg=COLORS['bg_tertiary'], fg=COLORS['text_secondary'], width=2, cursor='hand2')
        tip_label.pack(side=tk.LEFT, padx=(0, 4))
        Tooltip(tip_label, '使用说明:\n1. 先下载Excel模版\n2. 选择保存过的模版文件\n3. 生成的文案会自动追加写入', delay=100)
        
        # 打开按钮
        def _open_ai_save_file():
            path = self.ai_save_path_var.get()
            if path and os.path.exists(path):
                self.open_directory(path)
            else:
                self.show_toast('请先选择文件')
                
        ai_open_btn = tk.Label(save_btn_frame, text='打开', font=('SF Pro Text', 9),
                              bg=COLORS['bg_tertiary'], fg='#FFFFFF', padx=8, pady=3, cursor='hand2')
        ai_open_btn.pack(side=tk.LEFT)
        ai_open_btn.bind('<Button-1>', lambda e: _open_ai_save_file())
        ai_open_btn.bind('<Enter>', lambda e: ai_open_btn.config(bg=COLORS['accent']))
        ai_open_btn.bind('<Leave>', lambda e: ai_open_btn.config(bg=COLORS['bg_tertiary']))
        
        # 当前选择的文件显示 (换行显示)
        initial_path_text = os.path.basename(saved_ai_path) if saved_ai_path else '未选择文件'
        self.ai_save_path_label = tk.Label(self.ai_panel, text=initial_path_text, font=('SF Pro Text', 8),
                                          bg=COLORS['bg_secondary'], fg=COLORS['text_tertiary'], anchor='w')
        self.ai_save_path_label.grid(row=3, column=1, sticky='w', padx=(8, 0), pady=(0, 6))
        if saved_ai_path: Tooltip(self.ai_save_path_label, saved_ai_path)
        
        # 生成按钮 (Row 4)
        self.ai_generate_btn = ModernStyles.create_button(self.ai_panel, text='🤖 立即生成',
                                                         command=self._generate_ai_copy,
                                                         variant='primary')
        self.ai_generate_btn.grid(row=4, column=0, columnspan=2, sticky='we', pady=(12, 0))
        
        # 结果显示标签
        self.ai_status_label = tk.Label(self.ai_panel, text='', font=('SF Pro Text', 9),
                                       bg=COLORS['bg_secondary'], fg=COLORS['text_tertiary'])
        self.ai_status_label.grid(row=5, column=0, columnspan=2, pady=(8,0))
        
        # 1. 文字内容输入 (可调整大小)
        tk.Label(text_frame, text='📝 文字内容', font=('SF Pro Display', 12, 'bold'),
                 bg=COLORS['panel_bg'], fg=COLORS['text_primary']).pack(fill=tk.X, padx=12, pady=(12, 4))
        
        # 文本框容器
        text_entry_container = tk.Frame(text_frame, bg=COLORS['panel_bg'])
        text_entry_container.pack(fill=tk.X, padx=12, pady=(0, 8)) # Fill X
        
        # 增加默认高度和宽度
        self.text_content_entry = ModernStyles.create_text_area(text_entry_container, 
                                                              height=6, width=1, wrap=tk.WORD) # width=1 lets it expand
        self.text_content_entry.pack(side=tk.TOP, fill=tk.X, expand=True) # Fill X
        # 实时预览：每次按键更新画布
        self.text_content_entry.bind('<KeyRelease>', lambda e: self._on_text_preview())
        # 高亮检测：仅在换行或移出时触发
        self.text_content_entry.bind('<Return>', lambda e: self._on_detect_keywords())
        self.text_content_entry.bind('<FocusOut>', lambda e: self._on_detect_keywords())
        self.text_content_entry.bind('<FocusOut>', lambda e: self._on_detect_keywords())
        self._keyword_detect_job = None  # 用于防抖
        self._preview_timer = None       # 用于渲染防抖
        
        # 调整大小的手柄
        resize_handle = tk.Label(text_entry_container, text='⋮⋮', font=('SF Pro Text', 8),
                                 bg=COLORS['bg_tertiary'], fg=COLORS['text_secondary'],
                                 cursor='bottom_right_corner', padx=2, pady=0)
        resize_handle.pack(side=tk.RIGHT, anchor='se')
        
        # 拖拽调整大小
        def on_resize_drag(event):
            # 获取文本框当前位置
            entry_x = self.text_content_entry.winfo_x()
            entry_y = self.text_content_entry.winfo_y()
            # 计算新尺寸(相对于文本框左上角)
            new_w = max(15, (event.x_root - self.text_content_entry.winfo_rootx()) // 8)  # 字符宽度
            new_h = max(2, (event.y_root - self.text_content_entry.winfo_rooty()) // 16)   # 行高
            self.text_content_entry.config(width=new_w, height=new_h)
        
        resize_handle.bind('<B1-Motion>', on_resize_drag)
        
        # 字符计数器
        self.char_count_label = tk.Label(text_entry_container, text='0 / 100', font=('SF Pro Text', 9),
                                         bg=COLORS['panel_bg'], fg=COLORS['text_secondary'])
        self.char_count_label.pack(anchor='e', padx=4)
        
        # 关键词高亮 + 清除文字 (移到文字框下方)
        text_actions_frame = tk.Frame(text_entry_container, bg=COLORS['panel_bg'])
        text_actions_frame.pack(fill=tk.X, pady=(4, 0))
        
        self.highlight_enabled_var = tk.BooleanVar(value=True)
        tk.Checkbutton(text_actions_frame, text='🔍 自动高亮', variable=self.highlight_enabled_var,
                      bg=COLORS['panel_bg'], fg=COLORS['text_primary'],
                      selectcolor=COLORS['accent'], activebackground=COLORS['panel_bg'],
                      font=('SF Pro Text', 9),
                      command=self._on_highlight_toggle).pack(side=tk.LEFT)
        
        # 高亮颜色 (默认随机)
        self.highlight_color_var = tk.StringVar(value='random')
        # 用户要求删除切换颜色的方块，默认使用随机多巴胺/马卡龙色
        tk.Label(text_actions_frame, text='(随机糖果色)', font=('SF Pro Text', 9),
                bg=COLORS['panel_bg'], fg=COLORS['text_secondary']).pack(side=tk.LEFT, padx=2)

        
        # 存储自动检测的关键词 (内部使用)
        self._auto_keywords = []
        
        
        def _on_setting_release(action_name):
            self._auto_apply_text()
            self.save_history(action_name)
        
        # 2. 字体设置
        font_frame = tk.Frame(text_frame, bg=COLORS['panel_bg'])
        font_frame.pack(fill=tk.X, padx=12, pady=4)
        
        tk.Label(font_frame, text='字体:', font=('SF Pro Text', 10),
                 bg=COLORS['panel_bg'], fg=COLORS['text_secondary']).pack(side=tk.LEFT)
        
        from image_processor import TextLayer
        from tkinter import ttk
        
        font_map = TextLayer.FONT_NAMES
        font_values = list(font_map.values())
        default_font_name = font_map.get('yuanti', 'ST圆体 (默认)')
        
        self.font_family_var = tk.StringVar(value=default_font_name)
        
        #样式调整
        style = ttk.Style()
        style.theme_use('default') 
        style.configure("TCombobox", fieldbackground=COLORS['bg_secondary'], background=COLORS['bg_secondary'], foreground='#333333')
        
        font_combo = ttk.Combobox(font_frame, textvariable=self.font_family_var, values=font_values, 
                                  state="readonly", width=12)
        font_combo.pack(side=tk.LEFT, padx=4)
        
        def on_font_change(event):
            self._auto_apply_text()
            self.save_history("切换字体")
            
        font_combo.bind('<<ComboboxSelected>>', on_font_change)
        
        # 3. 字号设置
        size_frame = tk.Frame(text_frame, bg=COLORS['panel_bg'])
        size_frame.pack(fill=tk.X, padx=12, pady=4)
        
        tk.Label(size_frame, text='字号:', font=('SF Pro Text', 10),
                 bg=COLORS['panel_bg'], fg=COLORS['text_secondary']).pack(side=tk.LEFT)
        
        # [FIX] 初始化字号时根据当前预设计算
        init_font_size = 48
        if hasattr(self, 'current_size_preset'):
            init_font_size = self._get_default_font_size(self.current_size_preset)
                
        self.font_size_var = tk.IntVar(value=init_font_size)
        self.font_size_scale = tk.Scale(size_frame, from_=12, to=120, orient=tk.HORIZONTAL,
                             variable=self.font_size_var, bg=COLORS['panel_bg'], 
                             fg=COLORS['text_primary'], highlightthickness=0,
                             troughcolor=COLORS['bg_secondary'], length=100,
                             command=lambda v: self.update_text_preview())
        self.font_size_scale.pack(side=tk.LEFT, padx=(8, 0))
        self.font_size_scale.bind('<ButtonRelease-1>', lambda e: _on_setting_release("设置字号"))
        
        self.font_size_label = tk.Label(size_frame, text='48', font=('SF Pro Text', 10),
                                        bg=COLORS['panel_bg'], fg=COLORS['text_primary'], width=4)
        self.font_size_label.pack(side=tk.LEFT)
        
        # [UX] 颜色设置 - 紧凑版 (单行)
        color_section = tk.Frame(text_frame, bg=COLORS['panel_bg'])
        color_section.pack(fill=tk.X, padx=12, pady=4)
        
        tk.Label(color_section, text='颜色:', font=('SF Pro Text', 10),
                 bg=COLORS['panel_bg'], fg=COLORS['text_secondary']).pack(side=tk.LEFT)
                 
        self.text_color_var = tk.StringVar(value='#333333')
        
        def _set_text_color_with_history(color):
            self.set_text_color(color)
            self.save_history("设置文字颜色")
            
        # 常用精选色 (基础黑白 + 热门色)
        compact_colors = ['#333333', '#FFFFFF', '#FF2D55', '#FF9500', '#FFCC00', 
                         '#34C759', '#007AFF', '#AF52DE', '#FFB7B2', '#B2EBF2']
        
        for c in compact_colors:
            cb = tk.Canvas(color_section, width=18, height=18, bg=c, highlightthickness=1,
                          highlightbackground=COLORS['separator'], cursor='hand2')
            cb.pack(side=tk.LEFT, padx=1)
            cb.bind('<Button-1>', lambda e, color=c: _set_text_color_with_history(color))
            
        # 自定义颜色按钮 (紧凑)
        self.text_color_preview = tk.Canvas(color_section, width=18, height=18, 
                                            bg='#333333', highlightthickness=1,
                                            highlightbackground=COLORS['separator'])
        self.text_color_preview.pack(side=tk.LEFT, padx=(4, 2))
        self.text_color_preview.bind('<Button-1>', lambda e: self.open_text_color_picker())
        
        custom_btn = tk.Label(color_section, text='🎨', font=('SF Pro Text', 12),
                             bg=COLORS['panel_bg'], fg=COLORS['text_primary'], 
                             cursor='hand2')
        custom_btn.pack(side=tk.LEFT, padx=0)
        custom_btn.bind('<Button-1>', lambda e: self.open_text_color_picker())
        
        # [UX] 对齐与位置合并 (单行)
        align_pos_frame = tk.Frame(text_frame, bg=COLORS['panel_bg'])
        align_pos_frame.pack(fill=tk.X, padx=12, pady=4)
        
        # 左侧放对齐
        tk.Label(align_pos_frame, text='对齐:', font=('SF Pro Text', 10),
                 bg=COLORS['panel_bg'], fg=COLORS['text_secondary']).pack(side=tk.LEFT)
        
        self.text_align_var = tk.StringVar(value='left')
        align_icons = [('⬚≡', 'left'), ('≡', 'center'), ('≡⬚', 'right')]
        for icon, val in align_icons:
            btn = tk.Label(align_pos_frame, text=icon, font=('SF Pro Text', 14),
                          bg=COLORS['bg_tertiary'], fg=COLORS['text_primary'],
                          padx=6, pady=2, cursor='hand2')
            btn.pack(side=tk.LEFT, padx=1)
            btn.bind('<Button-1>', lambda e, v=val: self._set_align_with_history(v))
            
        # 中间分隔
        tk.Label(align_pos_frame, text='|', font=('SF Pro Text', 10),
                 bg=COLORS['panel_bg'], fg=COLORS['separator']).pack(side=tk.LEFT, padx=8)

        # 右侧放位置
        tk.Label(align_pos_frame, text='位置:', font=('SF Pro Text', 10),
                 bg=COLORS['panel_bg'], fg=COLORS['text_secondary']).pack(side=tk.LEFT)
                 
        self.text_position_var = tk.StringVar(value='center')
        pos_icons = [('⬆', 'top'), ('⬌', 'center'), ('⬇', 'bottom')]
        for icon, val in pos_icons:
            btn = tk.Label(align_pos_frame, text=icon, font=('SF Pro Text', 14),
                          bg=COLORS['bg_tertiary'], fg=COLORS['text_primary'],
                          padx=6, pady=2, cursor='hand2')
            btn.pack(side=tk.LEFT, padx=1)
            btn.bind('<Button-1>', lambda e, v=val: self._set_position_with_history(v))
            
        # [UX] 样式设置 (粗体/斜体/下划线/缩进) - 紧凑行
        style_frame = tk.Frame(text_frame, bg=COLORS['panel_bg'])
        style_frame.pack(fill=tk.X, padx=12, pady=4)
        
        tk.Label(style_frame, text='样式:', font=('SF Pro Text', 10),
                 bg=COLORS['panel_bg'], fg=COLORS['text_secondary']).pack(side=tk.LEFT)
        
        self.text_bold_var = tk.BooleanVar(value=False)
        self.text_italic_var = tk.BooleanVar(value=False)
        self.text_underline_var = tk.BooleanVar(value=False)
        self.text_indent_var = tk.BooleanVar(value=True)
        
        style_btns = [('B', self.text_bold_var, 'bold'), 
                      ('I', self.text_italic_var, 'italic'), 
                      ('U̲', self.text_underline_var, 'underline')]
                      
        for icon, var, name in style_btns:
            btn = tk.Checkbutton(style_frame, text=icon, variable=var,
                                font=('SF Pro Text', 11, 'bold' if name == 'bold' else 'italic' if name == 'italic' else 'normal'),
                                bg=COLORS['bg_tertiary'], fg=COLORS['text_primary'],
                                selectcolor=COLORS['accent'], activebackground=COLORS['bg_tertiary'],
                                indicatoron=False, padx=6, pady=2,
                                command=lambda: self._apply_style_with_history("切换文字样式"))
            btn.pack(side=tk.LEFT, padx=2)
            
        # 缩进复选框
        tk.Checkbutton(style_frame, text="首行缩进", variable=self.text_indent_var,
                       font=('SF Pro Text', 9), bg=COLORS['panel_bg'], fg=COLORS['text_primary'],
                       selectcolor=COLORS['accent'], activebackground=COLORS['panel_bg'],
                       command=lambda: self._apply_style_with_history("切换缩进")).pack(side=tk.LEFT, padx=8)
        
        # 7. 边距设置
        margin_frame = tk.Frame(text_frame, bg=COLORS['panel_bg'])
        margin_frame.pack(fill=tk.X, padx=12, pady=4)
        
        tk.Label(margin_frame, text='边距:', font=('SF Pro Text', 10),
                 bg=COLORS['panel_bg'], fg=COLORS['text_secondary']).pack(side=tk.LEFT)
        
        self.text_margin_var = tk.IntVar(value=20)
        margin_scale = tk.Scale(margin_frame, from_=0, to=100, orient=tk.HORIZONTAL,
                               variable=self.text_margin_var, bg=COLORS['panel_bg'],
                               fg=COLORS['text_primary'], highlightthickness=0,
                               troughcolor=COLORS['bg_secondary'], length=80,
                               command=lambda v: self.update_text_preview())
        margin_scale.pack(side=tk.LEFT, padx=(8, 0))
        margin_scale.bind('<ButtonRelease-1>', lambda e: _on_setting_release("设置文字边距"))
        
        # 8. 描边设置
        shadow_frame = tk.Frame(text_frame, bg=COLORS['panel_bg'])
        shadow_frame.pack(fill=tk.X, padx=12, pady=2)
        
        self.text_shadow_var = tk.BooleanVar(value=False)  # 保留变量但不显示UI
        
        self.text_stroke_var = tk.BooleanVar(value=False)
        tk.Checkbutton(shadow_frame, text='描边', variable=self.text_stroke_var,
                      bg=COLORS['panel_bg'], fg=COLORS['text_primary'],
                      selectcolor=COLORS['accent'], activebackground=COLORS['panel_bg'],
                      font=('SF Pro Text', 10),
                      command=lambda: self._apply_style_with_history("切换描边")).pack(side=tk.LEFT)
        
        # 描边宽度滑块
        stroke_frame = tk.Frame(text_frame, bg=COLORS['panel_bg'])
        stroke_frame.pack(fill=tk.X, padx=12, pady=2)
        
        tk.Label(stroke_frame, text='宽度:', font=('SF Pro Text', 9),
                 bg=COLORS['panel_bg'], fg=COLORS['text_secondary']).pack(side=tk.LEFT)
        
        self.stroke_width_var = tk.IntVar(value=2)
        stroke_scale = tk.Scale(stroke_frame, from_=1, to=10, orient=tk.HORIZONTAL,
                               variable=self.stroke_width_var, bg=COLORS['panel_bg'],
                               fg=COLORS['text_primary'], highlightthickness=0,
                               troughcolor=COLORS['bg_secondary'], length=60,
                               command=lambda v: self.update_text_preview())
        stroke_scale.pack(side=tk.LEFT, padx=(4, 0))
        stroke_scale.bind('<ButtonRelease-1>', lambda e: _on_setting_release("设置描边宽度"))
        
        # 描边颜色 (同一行，9个颜色)
        self.stroke_color_var = tk.StringVar(value='#000000')
        stroke_colors = ['#000000', '#FFFFFF', '#FF2D55', '#FF9500', '#FFCC00', '#34C759', '#007AFF', '#5856D6', '#AF52DE']
        for c in stroke_colors:
            sc = tk.Canvas(stroke_frame, width=14, height=14, bg=c, highlightthickness=1,
                          highlightbackground=COLORS['separator'], cursor='hand2')
            sc.pack(side=tk.LEFT, padx=1)
            sc.bind('<Button-1>', lambda e, color=c: self._set_stroke_color_with_history(color))
        
        # 清除文字按钮 (放在面板底部，避免误点)
        clear_frame = tk.Frame(text_frame, bg=COLORS['panel_bg'])
        clear_frame.pack(fill=tk.X, padx=12, pady=(16, 4))
        
        clear_btn = tk.Label(clear_frame, text='🗑️ 清除文字', font=('SF Pro Text', 10),
                            bg=COLORS['bg_tertiary'], fg=COLORS['danger'], 
                            padx=10, pady=4, cursor='hand2')
        clear_btn.pack(side=tk.RIGHT)
        clear_btn.bind('<Button-1>', lambda e: self.clear_text_layers())

    
    def _on_text_preview(self):
        """实时预览：每次按键时更新画布（不触发关键词检测）"""
        # 更新字符计数
        if hasattr(self, 'text_content_entry') and hasattr(self, 'char_count_label'):
            content = self.text_content_entry.get('1.0', 'end-1c')
            char_count = len(content)
            max_chars = 100
            if char_count > max_chars:
                content = content[:max_chars]
                self.text_content_entry.delete('1.0', tk.END)
                self.text_content_entry.insert('1.0', content)
                char_count = max_chars
            
            color = COLORS['danger'] if char_count >= max_chars else COLORS['text_secondary']
            self.char_count_label.config(text=f'{char_count} / {max_chars}', fg=color)
        
        # [OPTIMIZE] 渲染防抖 (300ms)
        # 避免输入过快时频繁渲染导致卡顿
        if hasattr(self, '_preview_timer') and self._preview_timer:
            self.after_cancel(self._preview_timer)
        self._preview_timer = self.after(300, self._auto_apply_text)
        
        # 如果启用了自动高亮，延时触发关键词检测 (Debounce 800ms)
        if hasattr(self, 'highlight_enabled_var') and self.highlight_enabled_var.get():
            if hasattr(self, '_highlight_timer') and self._highlight_timer:
                self.after_cancel(self._highlight_timer)
            self._highlight_timer = self.after(800, self._auto_detect_silent)
    
    def _set_align(self, val):
        """设置对齐方式"""
        self.text_align_var.set(val)
        self._auto_apply_text()
        
    def _set_align_with_history(self, val):
        self._set_align(val)
        self.save_history(f"设置文字对齐")
    
    def _set_position(self, val):
        """设置位置"""
        self.text_position_var.set(val)
        self._auto_apply_text()
        
    def _set_position_with_history(self, val):
        self._set_position(val)
        self.save_history(f"设置文字位置")
        
    def _set_stroke_color(self, color):
        self.stroke_color_var.set(color)
        self.update_text_preview()
    def _set_stroke_color_with_history(self, color):
        self._set_stroke_color(color)
        self.save_history(f"设置描边颜色")
    
    def _set_stroke_color(self, color):
        """设置描边颜色"""
        self.stroke_color_var.set(color)
        self._auto_apply_text()
    
    def _on_detect_keywords(self):
        """仅在换行或移出时触发关键词检测"""
        self._auto_detect_silent()
        self.save_history("编辑文字内容")
    
    def _on_highlight_toggle(self):
        """切换自动高亮"""
        # 如果启用了高亮，先检测关键词
        if self.highlight_enabled_var.get():
            self._auto_detect_silent()
        self.update_text_preview()
        self.save_history("编辑文字内容")
    
    def _auto_detect_silent(self):
        """静默自动检测关键词并自动应用到画布"""
        import re
        if not hasattr(self, 'text_content_entry'):
            return
        
        content = self.text_content_entry.get('1.0', 'end-1c')
        if not content.strip() or len(content.strip()) < 2:
            self._auto_keywords = []
            return
        
        keywords = []
        
        # 使用 jieba 关键词提取
        try:
            import jieba.analyse
            jieba_keywords = jieba.analyse.extract_tags(content, topK=5, withWeight=False)
            keywords.extend(jieba_keywords)
        except:
            pass
        
        # 检测英文单词
        english_words = re.findall(r'[a-zA-Z]{2,}', content)
        for word in english_words:
            if word.lower() not in [k.lower() for k in keywords]:
                keywords.append(word)
        
        # 检测 #标签
        hashtags = re.findall(r'#\w+', content)
        for tag in hashtags:
            cleaned = tag.lstrip('#')
            if cleaned not in keywords:
                keywords.append(cleaned)
        
        # 存储关键词并自动应用到画布
        self._auto_keywords = list(dict.fromkeys(keywords))[:8]
        self._auto_apply_text()
        
    def _toggle_ai_panel(self):
        """展开/收起 AI 面板"""
        if not hasattr(self, 'ai_panel'): return
        
        if self.ai_panel_visible:
            self.ai_panel.forget()
            self.ai_toggle_btn.config(text='✨ AI 帮我写', fg=COLORS['accent'])
            # 隐藏设置按钮
            if hasattr(self, 'ai_config_btn'):
                self.ai_config_btn.pack_forget()
            self.ai_panel_visible = False
        else:
            self.ai_panel.pack(fill=tk.X, padx=0, pady=(0, 12))
            self.ai_toggle_btn.config(text='✨ AI 帮我写 (点击收起)', fg=COLORS['accent']) # Keep consistent branding
            # 显示设置按钮
            if hasattr(self, 'ai_config_btn'):
                self.ai_config_btn.pack(side=tk.LEFT, padx=5)
            self.ai_panel_visible = True
            
    def _generate_ai_copy(self):
        """调用 AI 生成文案"""
        topic = self.ai_topic_entry.get().strip()
        if not topic:
            self.show_toast("请输入文案主题")
            return
            
        # UI 状态更新
        self.ai_generate_btn.config(text='⏳ 生成中...', state='disabled', bg=COLORS['text_tertiary'])
        self.ai_status_label.config(text='正在请求 AI 创意...', fg=COLORS['text_primary'])
        self.update_idletasks()
        
        # 获取参数
        style = self.ai_style_var.get()
        
        from modules.ai_writer import AIWriter
        
        def on_success(results):
            # 回到主线程更新 UI
            self.after(0, lambda: self._on_ai_success(results))
            
        def on_error(err_msg):
            self.after(0, lambda: self._on_ai_error(err_msg))
            
        # [MODIFIED] 使用配置的 API Key
        api_key = getattr(self, 'deepseek_api_key', None)
        writer = AIWriter(api_key=api_key)
        
        writer.generate_copy_async(topic, style=style, 
                                  callback=on_success, error_callback=on_error)

    def _configure_api_key(self):
        """配置 API Key (存储到独立文件，简单加密)"""
        # 创建自定义对话框
        dialog = tk.Toplevel(self)
        dialog.title("配置 DeepSeek API")
        dialog.geometry("520x550") # 增加高度以容纳更大的按钮区域
        dialog.resizable(True, True) # 允许调整大小以防万一
        dialog.transient(self)
        
        # [FIX] Force update to ensure geometry is applied and window is ready
        dialog.update_idletasks()
        
        # 居中显示
        try:
            x = self.winfo_rootx() + (self.winfo_width() - 520) // 2
            y = self.winfo_rooty() + (self.winfo_height() - 550) // 2
            dialog.geometry(f"+{x}+{y}")
        except:
            pass
            
        dialog.configure(bg=COLORS['bg'])
        
        # 1. 标题区
        tk.Label(dialog, text="DeepSeek API 设置", font=('SF Pro Display', 14, 'bold'),
                 bg=COLORS['bg'], fg=COLORS['text_primary']).pack(pady=(25, 15))
                 
        # 2. 说明区 (移除文件路径提示)
        instruction_frame = tk.Frame(dialog, bg=COLORS['bg_secondary'], padx=20, pady=20)
        instruction_frame.pack(fill=tk.X, padx=25, pady=5)
        
        steps = [
            "1. 访问 DeepSeek 开放平台 (https://platform.deepseek.com)",
            "2. 登录账号并进入「API Keys」菜单",
            "3. 点击「创建 API Key」，复制生成的 Key (以 sk- 开头)",
            "4. 将 Key 粘贴到下方，点击保存即可"
        ]
        
        for step in steps:
            tk.Label(instruction_frame, text=step, font=('SF Pro Text', 11),
                     bg=COLORS['bg_secondary'], fg=COLORS['text_secondary'], anchor='w', justify='left').pack(fill=tk.X, pady=3)
        
        # 3. 输入区
        # 3. 输入区
        input_container = tk.Frame(dialog, bg=COLORS['bg'])
        input_container.pack(fill=tk.X, padx=25, pady=20)
        
        tk.Label(input_container, text="API Key:", font=('SF Pro Text', 11, 'bold'),
                 bg=COLORS['bg'], fg=COLORS['text_primary']).pack(anchor='w', pady=(0, 8))
        
        # 输入框容器 (用于水平排列输入框和按钮)
        entry_row = tk.Frame(input_container, bg=COLORS['bg'])
        entry_row.pack(fill=tk.X)
        
        # 显示当前 Key (掩码处理)
        current_real_key = self.deepseek_api_key
        display_val = self._mask_api_key(current_real_key) if current_real_key else ""
        self._is_key_masked = True # 状态标记
        
        # 输入框
        entry = tk.Entry(entry_row, font=('Monaco', 12), 
                        bg=COLORS['input_bg'], fg=COLORS['text_primary'],
                        insertbackground=COLORS['text_primary'],
                        relief='flat', highlightthickness=1, 
                        highlightbackground=COLORS['input_border'],
                        highlightcolor=COLORS['accent'])
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=6)
        entry.insert(0, display_val)
        
        # 按钮容器
        action_btns = tk.Frame(entry_row, bg=COLORS['bg'])
        action_btns.pack(side=tk.LEFT, padx=(8, 0))
        
        def toggle_visibility():
            # 切换显示/隐藏
            current_text = entry.get()
            # 如果当前是占位符或空，不做处理
            if not self.deepseek_api_key or current_text.startswith("请输入"):
                return
                
            if self._is_key_masked:
                # 切换到明文
                entry.delete(0, tk.END)
                entry.insert(0, self.deepseek_api_key)
                eye_btn.config(text='🙈',  fg=COLORS['accent']) # 指示变为"隐藏"
                self._is_key_masked = False
            else:
                # 切换到掩码
                entry.delete(0, tk.END)
                entry.insert(0, self._mask_api_key(self.deepseek_api_key))
                eye_btn.config(text='👁️', fg=COLORS['text_secondary'])
                self._is_key_masked = True
                
        def copy_key():
            # 复制 Key
            if self.deepseek_api_key:
                self.clipboard_clear()
                self.clipboard_append(self.deepseek_api_key)
                self.update() # 确保剪贴板写入
                messagebox.showinfo("复制成功", "API Key 已复制到剪贴板", parent=dialog)
            else:
                messagebox.showwarning("无内容", "当前没有保存的 API Key", parent=dialog)

        # 小眼睛 (查看/隐藏)
        eye_btn = tk.Label(action_btns, text='👁️', font=('SF Pro Text', 14),
                          bg=COLORS['bg'], fg=COLORS['text_secondary'],
                          cursor='hand2', width=3)
        eye_btn.pack(side=tk.LEFT)
        eye_btn.bind('<Button-1>', lambda e: toggle_visibility())
        Tooltip(eye_btn, "显示/隐藏明文", delay=200)

        # 复制按钮
        copy_btn = tk.Label(action_btns, text='📋', font=('SF Pro Text', 14),
                           bg=COLORS['bg'], fg=COLORS['text_secondary'],
                           cursor='hand2', width=3)
        copy_btn.pack(side=tk.LEFT, padx=(4, 0))
        copy_btn.bind('<Button-1>', lambda e: copy_key())
        Tooltip(copy_btn, "复制 API Key", delay=200)

        # 占位符处理
        if not display_val:
            entry.insert(0, "请输入 sk- 开头的 API Key")
            entry.config(fg=COLORS['text_tertiary'])
            
        def on_focus_in(e):
            val = entry.get()
            if val == display_val or val.startswith("请输入") or '*' in val:
                entry.delete(0, tk.END)
                entry.config(fg=COLORS['text_primary'])
        
        entry.bind('<FocusIn>', on_focus_in)
        
        # 4. 按钮区
        btn_frame = tk.Frame(dialog, bg=COLORS['bg'])
        btn_frame.pack(fill=tk.X, padx=25, pady=(10, 20))
        
        def do_save():
            val = entry.get().strip()
            # 如果输入没变(还是掩码)，则不更新
            if val == display_val and '*' in val:
                dialog.destroy()
                return
            
            # 允许清除 (空值)
            if not val or val == "请输入 sk- 开头的 API Key":
                if messagebox.askyesno("确认清除", "确定要清除 API Key 吗？", parent=dialog):
                    self.deepseek_api_key = ""
                    self._save_api_key_to_file("")
                    messagebox.showinfo("已清除", "API Key 已清除。", parent=dialog)
                    dialog.destroy()
                return

            if not val.startswith("sk-") and len(val) > 10:
                # 简单的前缀检查 warning
                if not messagebox.askyesno("格式提示", "Key 通常以 sk- 开头，是否继续保存？", parent=dialog):
                    return
                
            self.deepseek_api_key = val
            self._save_api_key_to_file(val)
            messagebox.showinfo("保存成功", "API Key 已安全保存。", parent=dialog)
            dialog.destroy()
            
        def do_cancel():
            dialog.destroy()
            
        # 按钮样式区
        btn_frame = tk.Frame(dialog, bg=COLORS['bg'])
        btn_frame.pack(fill=tk.X, padx=30, pady=(20, 30))
        
        # 保存按钮 (Primary)
        save_btn = tk.Label(btn_frame, text="保存设置", font=('SF Pro Text', 12, 'bold'),
                           bg=COLORS['accent'], fg='#FFFFFF', 
                           padx=24, pady=10, cursor='hand2')
        save_btn.pack(side=tk.RIGHT, padx=(12, 0))
        save_btn.bind('<Button-1>', lambda e: do_save())
        
        # 取消按钮 (Secondary - 幽灵按钮风格)
        cancel_btn = tk.Label(btn_frame, text="取消", font=('SF Pro Text', 12),
                             bg=COLORS['bg_secondary'], fg=COLORS['text_primary'], 
                             padx=20, pady=10, cursor='hand2')
        cancel_btn.pack(side=tk.RIGHT)
        cancel_btn.bind('<Button-1>', lambda e: do_cancel())
        
        # Hover Effects
        def on_save_enter(e):
            save_btn.config(bg=COLORS['accent_hover'])
        def on_save_leave(e):
            save_btn.config(bg=COLORS['accent'])
            
        def on_cancel_enter(e):
            cancel_btn.config(bg=COLORS['hover'], fg=COLORS['text_bright'])
        def on_cancel_leave(e):
            cancel_btn.config(bg=COLORS['bg_secondary'], fg=COLORS['text_primary'])
            
        save_btn.bind('<Enter>', on_save_enter)
        save_btn.bind('<Leave>', on_save_leave)
        cancel_btn.bind('<Enter>', on_cancel_enter)
        cancel_btn.bind('<Leave>', on_cancel_leave)

        # [FIX] Wait for visibility before grabbing focus to ensure content renders
        dialog.wait_visibility()
        dialog.grab_set()
        
    def _mask_api_key(self, key):
        """掩码处理：显示首尾，中间掩盖 8 位"""
        if not key or len(key) < 12:
            return key
        # 保留前sk-xxxx 和 后4位
        # 例如 sk-1234567890abcdef (len 20) -> sk-1234********cdef
        # 中间替换为8个*
        prefix = key[:7] # sk- + 4 chars
        suffix = key[-4:]
        return f"{prefix}{'*' * 8}{suffix}"

    def _encrypt_key(self, key):
        """简单加密算法 (Base64 反转 + 混淆)"""
        import base64
        if not key: return ""
        # 1. 简单混淆: 反转字符串
        reversed_key = key[::-1]
        # 2. Base64 编码
        encoded = base64.b64encode(reversed_key.encode('utf-8')).decode('utf-8')
        # 3. 再次反转作为结果
        return encoded[::-1]

    def _decrypt_key(self, encrypted_key):
        """解密算法"""
        import base64
        if not encrypted_key: return ""
        try:
            # 1. 反转回 Base64
            b64_str = encrypted_key[::-1]
            # 2. Base64 解码
            decoded_bytes = base64.b64decode(b64_str)
            reversed_key = decoded_bytes.decode('utf-8')
            # 3. 反转回明文
            return reversed_key[::-1]
        except:
            return ""

    def _load_api_key(self):
        """加载 API Key"""
        try:
            config_dir = os.path.join(os.path.dirname(__file__), 'config')
            key_file = os.path.join(config_dir, 'api_key.secret')
            if os.path.exists(key_file):
                with open(key_file, 'r', encoding='utf-8') as f:
                    encrypted = f.read().strip()
                    return self._decrypt_key(encrypted)
        except Exception as e:
            print(f"Error loading API Key: {e}")
        return ""
        
    def _save_api_key_to_file(self, key):
        """保存 API Key (加密)"""
        try:
            config_dir = os.path.join(os.path.dirname(__file__), 'config')
            if not os.path.exists(config_dir):
                os.makedirs(config_dir)
            
            key_file = os.path.join(config_dir, 'api_key.secret')
            encrypted = self._encrypt_key(key)
            with open(key_file, 'w', encoding='utf-8') as f:
                f.write(encrypted)
        except Exception as e:
            print(f"Error saving API Key: {e}")
            messagebox.showerror("保存失败", f"无法写入配置文件: {e}")

    def _on_ai_success(self, results):
        """AI 生成成功回调"""
        self.ai_generate_btn.config(text='🤖 立即生成', state='normal', bg=COLORS['accent'])
        self.show_toast(f"成功生成 {len(results)} 条文案")
        
        if not results:
            self.ai_status_label.config(text='AI 未返回内容', fg=COLORS['danger'])
            return
            
        # 自动填充第一条
        first_copy = results[0]
        self.text_content_entry.delete('1.0', tk.END)
        self.text_content_entry.insert('1.0', first_copy)
        
        # 保存到 Excel 文件 (如果已选择)
        save_path = self.ai_save_path_var.get() if hasattr(self, 'ai_save_path_var') else ''
        if save_path and os.path.exists(save_path):
            try:
                import openpyxl
                wb = openpyxl.load_workbook(save_path)
                ws = wb.active
                topic = self.ai_topic_entry.get().strip()
                style = self.ai_style_var.get()
                from datetime import datetime
                datetime_str = datetime.now().strftime('%Y-%m-%d %H:%M')
                # 找第一个空行（从第3行开始，第1-2行是表头）
                next_row = 3
                for row in range(3, ws.max_row + 2):
                    if not ws.cell(row=row, column=4).value:  # D列（文字内容）为空
                        next_row = row
                        break
                # 写入数据 (模版列: A:图片名, B:主题, C:风格, D:文字内容, E:AI生成时间)
                ws.cell(row=next_row, column=2, value=topic)  # B: 主题
                ws.cell(row=next_row, column=3, value=style)  # C: 风格
                ws.cell(row=next_row, column=4, value=first_copy)  # D: 文字内容
                ws.cell(row=next_row, column=5, value=datetime_str)  # E: AI生成时间
                wb.save(save_path)
                self.ai_status_label.config(text=f'已保存到 Excel (第 {next_row} 行)', fg=COLORS['success'])
            except Exception as e:
                print(f"保存 Excel 失败: {e}")
                self.ai_status_label.config(text='保存失败，请检查文件', fg=COLORS['warning'])
        else:
            if len(results) > 1:
                self.ai_status_label.config(text=f'已填充第 1 条 (共 {len(results)} 条，可重试生成)', fg=COLORS['success'])
            else:
                self.ai_status_label.config(text='文案已填入', fg=COLORS['success'])
        
        # 无论是否保存 Excel，都要记录历史并触发画布渲染
        self.save_history("AI生成文案")
        self._auto_detect_silent()
            
    def _on_ai_error(self, err_msg):
        """AI 生成失败回调"""
        self.ai_generate_btn.config(text='🤖 立即生成', state='normal', bg=COLORS['accent'])
        self.ai_status_label.config(text='生成失败，请重试', fg=COLORS['danger'])
        print(f"AI Error: {err_msg}")
        self.show_toast("API 请求失败，请检查网络")
    
    def _on_highlight_toggle(self):
        """高亮开关切换时触发"""
        # 1. 获取当前开关状态
        enabled = self.highlight_enabled_var.get()
        
        # 2. 如果开启，立即执行一次完整的关键词检测 (不使用静默方法，确保拿到结果)
        if enabled:
            content = self.text_content_entry.get('1.0', 'end-1c')
            keywords = []
            if content and len(content.strip()) >= 1:
                # 提取关键词
                try:
                    import jieba.analyse
                    keywords.extend(jieba.analyse.extract_tags(content, topK=5))
                except:
                    pass
                
                # 英文和标签
                import re
                keywords.extend(re.findall(r'[a-zA-Z]{2,}', content))
                keywords.extend([t.lstrip('#') for t in re.findall(r'#\w+', content)])
            
            # 去重并保存
            self._auto_keywords = list(dict.fromkeys(keywords))[:8]
        else:
            # 关闭时清空
            self._auto_keywords = []
            
        # 3. 强制重新应用文字 (直接调用应用方法，不走 preview 的 timer 逻辑)
        print(f"[DEBUG] Toggle Highlight: {enabled}, Keywords: {self._auto_keywords}")
        self._auto_apply_text()
        self.save_history("切换自动高亮")
    
    def _apply_style_with_history(self, action_name="调整文字样式"):
        """应用文字样式并保存历史"""
        self._auto_apply_text()
        self.save_history(action_name)

    def _auto_apply_text(self):
        """自动应用文字到画布"""
        from image_processor import TextLayer
        
        content = self.text_content_entry.get('1.0', 'end-1c').strip() if hasattr(self, 'text_content_entry') else ''
        if not content:
            # 自动应用为空时，静默清除，不弹窗提示
            self.text_layers = []
            if hasattr(self, 'current_text_layer'):
                self.current_text_layer = None
            if hasattr(self, 'canvas_widget'):
                self.canvas_widget.clear_text_layer()
            if hasattr(self, 'image_processor'):
                self.image_processor.clear_text_layers()
            return

        # 获取字体键名 (反向查找)
        font_name = self.font_family_var.get() if hasattr(self, 'font_family_var') else '苹方 (默认)'
        font_family = 'yuanti'
        found = False
        for k, v in TextLayer.FONT_NAMES.items():
            if v == font_name:
                font_family = k
                found = True
                break
        
        # 检查是否需要保留自定义位置
        custom_pos = None
        if hasattr(self, 'current_text_layer') and self.current_text_layer:
            if getattr(self.current_text_layer, 'position', '') == 'custom':
                custom_pos = (self.current_text_layer.rel_x, self.current_text_layer.rel_y)
        
        # 创建文字层
        text_layer = TextLayer(
            content=content,
            font_size=self.font_size_var.get() if hasattr(self, 'font_size_var') else 48,
            color=self.text_color_var.get() if hasattr(self, 'text_color_var') else '#333333',
            font_family=font_family,
            align=self.text_align_var.get() if hasattr(self, 'text_align_var') else 'left',
            position='custom' if custom_pos else (self.text_position_var.get() if hasattr(self, 'text_position_var') else 'top'),
            margin=self.text_margin_var.get() if hasattr(self, 'text_margin_var') else 20,
            shadow={
                'enabled': self.text_shadow_var.get() if hasattr(self, 'text_shadow_var') else False,
                'color': '#000000',
                'offset': (2, 2),
                'blur': 4
            },
            stroke={
                'enabled': self.text_stroke_var.get() if hasattr(self, 'text_stroke_var') else False,
                'color': self.stroke_color_var.get() if hasattr(self, 'stroke_color_var') else '#000000',
                'width': self.stroke_width_var.get() if hasattr(self, 'stroke_width_var') else 2
            },
            highlight={
                'enabled': self.highlight_enabled_var.get() if hasattr(self, 'highlight_enabled_var') else True,
                'keywords': self._auto_keywords if hasattr(self, '_auto_keywords') else [],
                'color': self.highlight_color_var.get() if hasattr(self, 'highlight_color_var') else '#FFB7B2',
                'style': 'random' if (hasattr(self, 'highlight_color_var') and self.highlight_color_var.get() == 'random') else 'marker'
            },
            bold=self.text_bold_var.get() if hasattr(self, 'text_bold_var') else False,
            italic=self.text_italic_var.get() if hasattr(self, 'text_italic_var') else False,
            underline=self.text_underline_var.get() if hasattr(self, 'text_underline_var') else False,
            indent=self.text_indent_var.get() if hasattr(self, 'text_indent_var') else True
        )
        
        # 恢复自定义位置坐标
        if custom_pos:
            text_layer.rel_x, text_layer.rel_y = custom_pos
        
        # 存储并应用
        self.current_text_layer = text_layer
        
        # 预览时不写入 ImageProcessor，而是作为独立 Item 添加到 Canvas
        self.image_processor.clear_text_layers()
        
        # [WYSIWYG FIX] 预览应该模拟导出尺寸，然后缩小显示
        # 直接使用当前选中的预设对象，确保与导出逻辑一致
        preset_width = self.current_size_preset['width']
        preset_height = self.current_size_preset['height']
        
        # 画布显示尺寸
        cw = self.canvas_widget.width if self.canvas_widget.width > 10 else 800
        ch = self.canvas_widget.height if self.canvas_widget.height > 10 else 600
        
        # 计算从画布到导出的缩放比例 (和 batch_export 相同)
        preview_scale = preset_width / cw if cw > 0 else 1.0
        
        # 计算导出尺寸下的边框宽度 (与导出逻辑统一，只检查 width > 0)
        export_border_width = 0
        if hasattr(self, 'border_config') and self.border_config.get('width', 0) > 0:
            export_border_width = int(self.border_config.get('width', 0) * preview_scale)
            # [FIX] 动态调整安全边距：横屏多留白，竖屏少留白
            if preset_width > preset_height:
                # 横屏 (16:9等): 增加更多边距 (30 -> 60) 以防止压边，并配合宽度限制
                export_border_width += int(60 * preview_scale)
            else:
                # 竖屏 (9:16等): 恢复较小边距 (10) 避免内容偏左/过窄
                export_border_width += int(10 * preview_scale)
            
        print(f"[DEBUG] PREVIEW: border_width_raw={self.border_config.get('width')}, export_border_width={export_border_width}")
        
        # 强制刷新关键词 (如果是高亮模式且关键词为空)
        if self.highlight_enabled_var.get() and not self._auto_keywords:
             pass
        
        # [关键] 使用导出尺寸渲染，和导出时完全一致
        # [FIX] font_size 已经是预设尺寸下的像素值，所以 render 时 scale 应为 1.0
        # 如果使用 preview_scale (>1)，会导致字号被再次放大
        # [FIX] 传入 safe_margin_y，防止顶部/底部被遮挡
        text_img, x, y = text_layer.render(preset_width, preset_height, scale=1.0, 
                                          safe_margin_x=export_border_width, 
                                          safe_margin_y=export_border_width)
        
        if text_img:
            # 缩小回预览尺寸
            display_scale = cw / preset_width
            new_w = int(text_img.width * display_scale)
            new_h = int(text_img.height * display_scale)
            if new_w > 0 and new_h > 0:
                from PIL import Image
                text_img = text_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                x = int(x * display_scale)
                y = int(y * display_scale)
            self.canvas_widget.add_text_layer_item(text_img, x, y)
    
    def on_text_transform(self, action, **kwargs):
        """处理文字层的交互变换"""
        if not hasattr(self, 'current_text_layer') or not self.current_text_layer:
            return
            
        if action == 'move':
            # 更新相对坐标
            x, y = kwargs.get('x'), kwargs.get('y')
            cw, ch = self.canvas_widget.width, self.canvas_widget.height
            
            if cw > 0 and ch > 0:
                self.current_text_layer.rel_x = x / cw
                self.current_text_layer.rel_y = y / ch
                # 标记为自定义位置
                self.current_text_layer.position = 'custom'
                
        elif action == 'scale':
            # 更新字号
            factor = kwargs.get('factor', 1.0)
            if hasattr(self, 'font_size_var'):
                current_size = self.font_size_var.get()
                new_size = max(12, min(500, int(current_size * factor)))
                if new_size != current_size:
                    self.font_size_var.set(new_size)
                    # 重新应用文字 (重新渲染)
                    self._auto_apply_text()
    
    def set_text_color(self, color):
        """设置文字颜色"""
        self.text_color_var.set(color)
        # 更新颜色预览
        if hasattr(self, 'text_color_preview'):
            self.text_color_preview.config(bg=color)
        
        # 必须调用 _auto_apply_text 以更新 current_text_layer (用于导出)
        # 并确保重绘
        self._auto_apply_text()
    
    def open_text_color_picker(self):
        """打开自定义颜色选择器"""
        from color_wheel_picker import ColorWheelPicker
        
        def on_color_selected(color):
            self.set_text_color(color)
            self.save_history("设置文字颜色")
        
        picker = ColorWheelPicker(
            self, 
            callback=on_color_selected,
            initial_color=self.text_color_var.get()
        )
    
    def set_highlight_color(self, color):
        """设置高亮颜色"""
        # print(f"[DEBUG] Set highlight color: {color}")
        self.highlight_color_var.set(color)
        # 高亮颜色改变也需要重新应用文字
        self._auto_apply_text()
    
    def auto_detect_keywords(self):
        """自动检测关键字 (使用 jieba 智能提取)"""
        import re
        if not hasattr(self, 'text_content_entry'):
            return
        
        content = self.text_content_entry.get('1.0', 'end-1c')
        if not content.strip():
            return
        
        keywords = []
        
        # 尝试使用 jieba 关键词提取
        try:
            import jieba.analyse
            # 使用 TF-IDF 提取关键词 (最多5个)
            jieba_keywords = jieba.analyse.extract_tags(content, topK=5, withWeight=False)
            keywords.extend(jieba_keywords)
        except ImportError:
            pass  # jieba 未安装，使用备用方案
        except Exception as e:
            print(f"[DEBUG] jieba 关键词提取失败: {e}")
        
        # 备用: 检测英文单词 (中文中的英文通常是品牌/专有名词)
        english_words = re.findall(r'[a-zA-Z]{2,}', content)
        for word in english_words:
            if word.lower() not in [k.lower() for k in keywords]:
                keywords.append(word)
        
        # 检测 #标签
        hashtags = re.findall(r'#\w+', content)
        for tag in hashtags:
            cleaned = tag.lstrip('#')
            if cleaned not in keywords:
                keywords.append(cleaned)
        
        # 去重并更新输入框
        unique_keywords = list(dict.fromkeys(keywords))[:8]  # 最多8个
        if hasattr(self, 'highlight_keywords_entry'):
            self.highlight_keywords_entry.delete(0, 'end')
            self.highlight_keywords_entry.insert(0, ','.join(unique_keywords))
            self.highlight_enabled_var.set(True)
            self._auto_apply_text()
            self.show_toast(f'检测到 {len(unique_keywords)} 个关键词')
    
    def update_text_preview(self):
        """更新文字预览 (实时)"""
        # 更新字号显示
        if hasattr(self, 'font_size_label'):
            self.font_size_label.config(text=str(self.font_size_var.get()))
        
        # 更新配置 (保持状态同步)
        self.current_text_config = {
            'content': self.text_content_entry.get('1.0', tk.END).strip() if hasattr(self, 'text_content_entry') else '',
            'font_size': self.font_size_var.get() if hasattr(self, 'font_size_var') else 48,
            'color': self.text_color_var.get() if hasattr(self, 'text_color_var') else '#FFFFFF',
            'font_family': self.font_family_var.get() if hasattr(self, 'font_family_var') else 'yuanti',
            'align': self.text_align_var.get() if hasattr(self, 'text_align_var') else 'center',
            'position': self.text_position_var.get() if hasattr(self, 'text_position_var') else 'center',
            'margin': self.text_margin_var.get() if hasattr(self, 'text_margin_var') else 20,
            'indent': self.text_indent_var.get() if hasattr(self, 'text_indent_var') else True,
            'shadow': {
                'enabled': self.text_shadow_var.get() if hasattr(self, 'text_shadow_var') else False,
                'color': '#000000',
                'offset': (2, 2),
                'blur': 4
            },
            'stroke': {
                'enabled': self.text_stroke_var.get() if hasattr(self, 'text_stroke_var') else False,
                'color': '#000000',
                'width': self.stroke_width_var.get() if hasattr(self, 'stroke_width_var') else 2
            },
            'highlight': {
                'enabled': self.highlight_enabled_var.get() if hasattr(self, 'highlight_enabled_var') else False,
                'keywords': self._auto_keywords if hasattr(self, '_auto_keywords') else [],
                'color': self.highlight_color_var.get() if hasattr(self, 'highlight_color_var') else '#FFB7B2'
            },
            'bold': self.text_bold_var.get() if hasattr(self, 'text_bold_var') else False,
            'italic': self.text_italic_var.get() if hasattr(self, 'text_italic_var') else False,
            'underline': self.text_underline_var.get() if hasattr(self, 'text_underline_var') else False
        }
        
        # [FIX] 使用统一的 _auto_apply_text 逻辑，确保缩放一致
        # 之前的 set_text_preview 使用了错误的缩放逻辑 (基于画布尺寸而非预设尺寸)
        self._auto_apply_text()
    
    def apply_text_to_canvas(self):
        """应用文字到画布"""
        from image_processor import TextLayer
        
        content = self.text_content_entry.get('1.0', tk.END).strip()
        if not content:
            self.show_toast('请输入文字内容')
            return
        
        # 创建文字层
        # 获取高亮关键字列表
        keywords = []
        if hasattr(self, 'highlight_keywords_entry'):
            kw_text = self.highlight_keywords_entry.get().strip()
            if kw_text:
                keywords = [k.strip() for k in kw_text.split(',') if k.strip()]
        
        text_layer = TextLayer(
            content=content,
            font_size=self.font_size_var.get(),
            color=self.text_color_var.get(),
            font_family=self.font_family_var.get(),
            align=self.text_align_var.get(),
            position=self.text_position_var.get(),
            margin=self.text_margin_var.get(),
            shadow={
                'enabled': self.text_shadow_var.get(),
                'color': '#000000',
                'offset': (2, 2),
                'blur': 4
            },
            stroke={
                'enabled': self.text_stroke_var.get(),
                'color': '#000000',
                'width': self.stroke_width_var.get()
            },
            highlight={
                'enabled': self.highlight_enabled_var.get() if hasattr(self, 'highlight_enabled_var') else False,
                'keywords': keywords,
                'color': self.highlight_color_var.get() if hasattr(self, 'highlight_color_var') else '#FFB7B2'
            },
            bold=self.text_bold_var.get() if hasattr(self, 'text_bold_var') else False,
            italic=self.text_italic_var.get() if hasattr(self, 'text_italic_var') else False,
            underline=self.text_underline_var.get() if hasattr(self, 'text_underline_var') else False,
            indent=self.text_indent_var.get() if hasattr(self, 'text_indent_var') else True
        )
        
        self.text_layers = [text_layer]  # 目前只支持一个文字层
        self.canvas_widget.set_text_layer(text_layer)
        self.save_history('添加文字')
        self.show_toast('文字已应用')
    
    def clear_text_layers(self):
        """清除所有文字层 (带确认)"""
        # 检查是否有内容需要清除
        has_content = False
        if hasattr(self, 'text_content_entry'):
            content = self.text_content_entry.get('1.0', 'end-1c').strip()
            if content:
                has_content = True
        
        if not has_content:
            self.show_toast('没有文字需要清除')
            return
        
        # 第一次确认
        if not messagebox.askyesno('确认清除', '确定要清除所有文字内容吗？'):
            return
        
        # 第二次确认
        if not messagebox.askyesno('再次确认', '此操作不可撤销，确定要清除吗？'):
            return
        
        # 执行清除
        self.text_layers = []
        if hasattr(self, 'canvas_widget'):
            self.canvas_widget.clear_text_layer()
        # 清空输入框
        if hasattr(self, 'text_content_entry'):
            self.text_content_entry.delete('1.0', tk.END)
        # 更新字符计数
        if hasattr(self, 'char_count_label'):
            self.char_count_label.config(text='0 / 100', fg=COLORS['text_secondary'])
        self.show_toast('文字已清除')
    
    def create_batch_tab(self, parent):
        """批量处理标签页 - 现代风格"""
        # 滚动区域
        scroll_canvas = tk.Canvas(parent, bg=COLORS['panel_bg'], highlightthickness=0)
        scrollbar = tk.Scrollbar(parent, orient='vertical', command=scroll_canvas.yview)
        batch_frame = tk.Frame(scroll_canvas, bg=COLORS['panel_bg'])
        
        batch_frame.bind('<Configure>', lambda e: scroll_canvas.configure(scrollregion=scroll_canvas.bbox('all')))
        scroll_canvas.create_window((0, 0), window=batch_frame, anchor='nw')
        scroll_canvas.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        scroll_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # [UX] 0. 使用说明模块 (Compact Tooltip Version)
        help_container = tk.Frame(batch_frame, bg=COLORS['panel_bg'])
        help_container.pack(fill=tk.X, padx=12, pady=(12, 0))
        
        help_label = tk.Label(help_container, text='💡 批量处理指南 (鼠标悬停查看)', font=('SF Pro Text', 10),
                             bg=COLORS['bg_secondary'], fg=COLORS['text_secondary'], 
                             padx=10, pady=6, cursor='hand2', anchor='w') # [UI] 靠左对齐
        help_label.pack(anchor='w', fill=tk.X)
        
        steps_text = (
            "1. 选择「输入目录」：自动扫描加载目录下的所有图片\n"
            "2. 开启「批量配文」(可选)：支持 Excel 自动映射文案\n"
            "3. 调整「随机选项」：为每张图生成独特的边框和样式\n"
            "4. 点击底部的「批量生成并导出」按钮"
        )
        Tooltip(help_label, steps_text, delay=200)
        
        # 1. 输出目录设置 (放在最上面)
        output_header_frame = tk.Frame(batch_frame, bg=COLORS['panel_bg'])
        output_header_frame.pack(fill=tk.X, padx=12, pady=(12, 4))
        
        tk.Label(output_header_frame, text='📤 图片输出目录', font=('SF Pro Display', 12, 'bold'),
                 bg=COLORS['panel_bg'], fg=COLORS['text_primary']).pack(side=tk.LEFT)
                 
        output_dir_btn = tk.Label(output_header_frame, text='选择', font=('SF Pro Text', 10),
                                  bg=COLORS['accent'], fg='white', padx=10, pady=4, cursor='hand2')
        output_dir_btn.pack(side=tk.LEFT, padx=(10, 0))
        output_dir_btn.bind('<Button-1>', lambda e: self.select_output_dir())
        
        output_open_btn = tk.Label(output_header_frame, text='打开', font=('SF Pro Text', 10),
                                   bg=COLORS['bg_tertiary'], fg=COLORS['text_primary'], padx=10, pady=4, cursor='hand2')
        output_open_btn.pack(side=tk.LEFT, padx=(4, 0))
        output_open_btn.bind('<Button-1>', lambda e: self.open_directory(self.batch_output_dir))
        
        self.output_dir_label = tk.Label(batch_frame, text=self.batch_output_dir or '未设置',
                                         font=('SF Pro Text', 9), bg=COLORS['bg_secondary'],
                                         fg=COLORS['text_secondary'], anchor='w', padx=8, pady=6)
        self.output_dir_label.pack(fill=tk.X, padx=12)
        
        # --- 分割线 1 ---
        tk.Frame(batch_frame, height=1, bg=COLORS['separator']).pack(fill=tk.X, padx=12, pady=(16, 12))
        
        # 2. 启用批量导入配图 勾选框
        self.batch_enable_images = tk.BooleanVar(value=True)
        enable_images_check = ModernToggleCheckbutton(
            batch_frame, text='启用批量导入配图', 
            variable=self.batch_enable_images,
            bg=COLORS['panel_bg'], font=('SF Pro Text', 11, 'bold')
        )
        enable_images_check.pack(anchor='w', padx=12, pady=(0, 8), fill=tk.X)
        Tooltip(enable_images_check, '启用后将从输入目录批量加载图片进行处理')

        # 图片位置和缩放选项 (紧跟勾选框下方)
        match_canvas_check = ModernToggleCheckbutton(
            batch_frame, text='图片位置和缩放（参考预设/原图全尺寸）', 
            variable=self.batch_match_canvas,
            bg=COLORS['panel_bg'], font=('SF Pro Text', 11)
        )
        match_canvas_check.pack(anchor='w', padx=24, pady=(0, 12), fill=tk.X)
        Tooltip(match_canvas_check, '批量处理时，按照当前画布上图片的位置和缩放比例来放置每张图片')

        # [NEW] 图片作为透明背景 (用户请求)
        self.batch_image_as_bg = tk.BooleanVar(value=False)
        image_as_bg_check = ModernToggleCheckbutton(
            batch_frame, text='图片作为透明背景 (50%透明度)', 
            variable=self.batch_image_as_bg,
            bg=COLORS['panel_bg'], font=('SF Pro Text', 11)
        )
        image_as_bg_check.pack(anchor='w', padx=24, pady=(0, 12), fill=tk.X)
        Tooltip(image_as_bg_check, '勾选后，批量导入的图片将作为半透明背景显示，不抢文字重点')
        
        # 3. 输入目录设置
        input_header_frame = tk.Frame(batch_frame, bg=COLORS['panel_bg'])
        input_header_frame.pack(fill=tk.X, padx=12, pady=(0, 4))
        
        tk.Label(input_header_frame, text='📁 图片输入目录', font=('SF Pro Display', 12, 'bold'),
                 bg=COLORS['panel_bg'], fg=COLORS['text_primary']).pack(side=tk.LEFT)
                 
        input_dir_btn = tk.Label(input_header_frame, text='选择', font=('SF Pro Text', 10),
                                 bg=COLORS['accent'], fg='white', padx=10, pady=4, cursor='hand2')
        input_dir_btn.pack(side=tk.LEFT, padx=(10, 0))
        input_dir_btn.bind('<Button-1>', lambda e: self.select_input_dir())
        
        input_open_btn = tk.Label(input_header_frame, text='打开', font=('SF Pro Text', 10),
                                  bg=COLORS['bg_tertiary'], fg=COLORS['text_primary'], padx=10, pady=4, cursor='hand2')
        input_open_btn.pack(side=tk.LEFT, padx=(4, 0))
        input_open_btn.bind('<Button-1>', lambda e: self.open_directory(self.batch_input_dir))
        
        self.input_dir_label = tk.Label(batch_frame, text=self.batch_input_dir or '未设置',
                                        font=('SF Pro Text', 9), bg=COLORS['bg_secondary'],
                                        fg=COLORS['text_secondary'], anchor='w', padx=8, pady=6)
        self.input_dir_label.pack(fill=tk.X, padx=12)
        
        # [REMOVED] 3. 操作区域标题 (用户请求删除)
        tk.Frame(batch_frame, height=12, bg=COLORS['panel_bg']).pack(fill=tk.X)
        
        # [UX] 状态显示区域 (置于扫描按钮上方)
        status_info_frame = tk.Frame(batch_frame, bg=COLORS['panel_bg'])
        status_info_frame.pack(fill=tk.X, padx=12, pady=(12, 4))
        
        self.batch_count_label = tk.Label(
            status_info_frame, text='已加载: 0 张',
            bg=COLORS['panel_bg'], fg=COLORS['text_primary'],
            font=('SF Pro Display', 11, 'bold'), anchor='w'
        )
        self.batch_count_label.pack(side=tk.LEFT)
        
        self.batch_status_label = tk.Label(
            status_info_frame, text='待处理: 0 张 | 本次已处理: 0 张',
            bg=COLORS['panel_bg'], fg=COLORS['text_secondary'],
            font=('SF Pro Text', 10), anchor='w'
        )
        self.batch_status_label.pack(side=tk.LEFT, padx=(10, 0))

        # 从目录加载按钮
        load_from_dir_btn = tk.Label(
            batch_frame, text='🔄 重新扫描输入目录',
            bg=COLORS['warning'], fg='white',
            font=('SF Pro Text', 11, 'bold'), pady=10, cursor='hand2'
        )
        load_from_dir_btn.pack(anchor='w', padx=12, pady=(4, 12), ipadx=10)
        load_from_dir_btn.bind('<Button-1>', lambda e: self.load_from_input_dir())
        
        # --- 分割线 2 (替代"批量文字"标题) ---
        tk.Frame(batch_frame, height=1, bg=COLORS['separator']).pack(fill=tk.X, padx=12, pady=(0, 12))
                 
        text_dir_frame = tk.Frame(batch_frame, bg=COLORS['panel_bg'])
        text_dir_frame.pack(fill=tk.X, padx=12, pady=(0, 12))
        
        # 启用文字目录勾选框
        text_dir_check = ModernToggleCheckbutton(text_dir_frame, text='启用批量配文', 
                      variable=self.batch_use_text_dir,
                      bg=COLORS['panel_bg'], font=('SF Pro Text', 11),
                      select_color=COLORS['accent'])
        text_dir_check.pack(anchor='w', pady=(0, 8), fill=tk.X)
        Tooltip(text_dir_check, '勾选后将尝试为每张图片添加文字 (源自Excel文件)；若未找到对应文字，则使用当前编辑器内容')
        
        # 文字目录选择
        text_dir_select_frame = tk.Frame(text_dir_frame, bg=COLORS['panel_bg'])
        text_dir_select_frame.pack(fill=tk.X, pady=(0, 0))
        
        text_dir_btn = tk.Label(text_dir_select_frame, text='选择 Excel 数据表', font=('SF Pro Text', 10),
                               bg=COLORS['bg_tertiary'], fg=COLORS['text_primary'], padx=8, pady=4, cursor='hand2')
        text_dir_btn.pack(side=tk.LEFT)
        text_dir_btn.bind('<Button-1>', lambda e: self.select_excel_file())
        
        # 模板下载按钮
        template_btn = tk.Label(text_dir_select_frame, text='下载模版', font=('SF Pro Text', 10),
                               bg=COLORS['bg_tertiary'], fg=COLORS['accent'], padx=8, pady=4, cursor='hand2')
        template_btn.pack(side=tk.LEFT, padx=(4, 0))
        template_btn.bind('<Button-1>', lambda e: self.download_excel_template())
        
        text_open_btn = tk.Label(text_dir_select_frame, text='打开', font=('SF Pro Text', 10),
                                bg=COLORS['bg_tertiary'], fg=COLORS['text_primary'], padx=8, pady=4, cursor='hand2')
        text_open_btn.pack(side=tk.LEFT, padx=(4, 0))
        text_open_btn.bind('<Button-1>', lambda e: self.open_directory(self.batch_text_dir))
        
        self.text_dir_label = tk.Label(text_dir_frame, text=self.batch_text_dir if self.batch_text_dir else '未选择文件',
                                       font=('SF Pro Text', 9), bg=COLORS['bg_secondary'],
                                       fg=COLORS['text_secondary'], anchor='w', padx=8, pady=4)
        self.text_dir_label.pack(fill=tk.X, pady=(4, 0))
        
        tk.Label(text_dir_frame, text='和AI帮写共用模版，自动读取"文字内容"列',
                font=('SF Pro Text', 8), bg=COLORS['panel_bg'], fg=COLORS['text_tertiary']
                ).pack(anchor='w', pady=(4, 0))

        # --- 随机化选项区域 (结构统一化) ---
        random_header_frame = tk.Frame(batch_frame, bg=COLORS['panel_bg'])
        random_header_frame.pack(fill=tk.X, padx=12, pady=(0, 4))
        
        tk.Label(random_header_frame, text='🎲 随机化选项', font=('SF Pro Display', 12, 'bold'),
                 bg=COLORS['panel_bg'], fg=COLORS['text_secondary']).pack(side=tk.LEFT)
                 
        random_frame = tk.Frame(batch_frame, bg=COLORS['panel_bg'])
        random_frame.pack(fill=tk.X, padx=12, pady=(0, 12))
        
        # 使用 Grid 布局放置选项
        ModernToggleCheckbutton(random_frame, text='随机边框颜色', variable=self.batch_random_color,
                      bg=COLORS['panel_bg'], font=('SF Pro Text', 10)
                      ).grid(row=0, column=0, sticky='w', padx=(0, 15), pady=5)
        
        ModernToggleCheckbutton(random_frame, text='随机线条样式', variable=self.batch_random_style,
                      bg=COLORS['panel_bg'], font=('SF Pro Text', 10)
                      ).grid(row=0, column=1, sticky='w', padx=0, pady=5)
                      
        ModernToggleCheckbutton(random_frame, text='随机边框图案', variable=self.batch_random_pattern,
                       bg=COLORS['panel_bg'], font=('SF Pro Text', 10)
                       ).grid(row=1, column=0, sticky='w', pady=5)

        ModernToggleCheckbutton(random_frame, text='随机文字高亮', variable=self.batch_random_highlight,
                       bg=COLORS['panel_bg'], font=('SF Pro Text', 10)
                       ).grid(row=1, column=1, sticky='w', pady=5)

        ModernToggleCheckbutton(random_frame, text='随机字体样式', variable=self.batch_random_font_style,
                       bg=COLORS['panel_bg'], font=('SF Pro Text', 10)
                       ).grid(row=2, column=0, sticky='w', pady=5)

        ModernToggleCheckbutton(random_frame, text='随机背景样式', variable=self.batch_random_background_style,
                       bg=COLORS['panel_bg'], font=('SF Pro Text', 10)
                       ).grid(row=2, column=1, sticky='w', pady=5)
        
        ModernToggleCheckbutton(random_frame, text='随机添加贴纸', variable=self.batch_random_stickers,
                       bg=COLORS['panel_bg'], font=('SF Pro Text', 10)
                       ).grid(row=3, column=0, sticky='w', pady=(5, 0))

        
        # 5. 批量导出按钮
        batch_export_btn = tk.Label(
            batch_frame, text='⚡ 批量生成并导出',
            bg=COLORS['success'], fg='white',
            font=('SF Pro Text', 11, 'bold'), pady=12, cursor='hand2'
        )
        batch_export_btn.pack(anchor='w', padx=12, pady=4, ipadx=10)
        batch_export_btn.bind('<Button-1>', lambda e: self.batch_export())
        
        # 6. 日志输出框
        # 6. 日志输出框
        log_header_frame = tk.Frame(batch_frame, bg=COLORS['panel_bg'])
        log_header_frame.pack(fill=tk.X, padx=12, pady=(20, 4))
        
        tk.Label(log_header_frame, text='📋 处理日志', font=('SF Pro Display', 12, 'bold'),
                 bg=COLORS['panel_bg'], fg=COLORS['text_primary'], anchor='w').pack(side=tk.LEFT)
        
        # 复制日志按钮 (放在标题后面)
        copy_btn = tk.Label(log_header_frame, text='[复制日志]', font=('SF Pro Text', 10),
                           bg=COLORS['panel_bg'], fg=COLORS['accent'], cursor='hand2')
        copy_btn.pack(side=tk.LEFT, padx=(10, 0))
        copy_btn.bind('<Button-1>', lambda e: self.copy_batch_log())
        
        log_frame = tk.Frame(batch_frame, bg=COLORS['bg_secondary'])
        log_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 12))
        
        self.batch_log_text = tk.Text(log_frame, height=20, font=('Menlo', 9),
                                       bg=COLORS['bg'], fg=COLORS['text_secondary'],
                                       wrap=tk.WORD, state=tk.DISABLED,
                                       highlightthickness=1, highlightbackground=COLORS['separator'])
        log_scrollbar = tk.Scrollbar(log_frame, command=self.batch_log_text.yview)
        self.batch_log_text.configure(yscrollcommand=log_scrollbar.set)
        
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.batch_log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 7. 底部说明
        tip_text = "支持格式：JPG, JPEG, PNG, BMP, GIF"
        tk.Label(batch_frame, text=tip_text, font=('SF Pro Text', 9),
                 bg=COLORS['panel_bg'], fg=COLORS['text_secondary'], anchor='w',
                 padx=12, pady=12).pack(fill=tk.X)

    def copy_batch_log(self):
        """复制批量处理日志到剪贴板"""
        if hasattr(self, 'batch_log_text'):
            content = self.batch_log_text.get('1.0', tk.END).strip()
            if content:
                self.title_bar.clipboard_clear()
                self.title_bar.clipboard_append(content)
                self.title_bar.update() # 必须 update 才能写入剪贴板
                self.show_toast("日志已复制到剪贴板")
            else:
                self.show_toast("日志内容为空")

    def update_batch_status_text(self):
        """更新批量处理状态文本"""
        if not hasattr(self, 'batch_images') or not self.batch_images:
            return
            
        # Since we always process provided images (unique filenames), pending is just the total count
        pending = len(self.batch_images)
            
        # 本次已处理保持不变，或者如果不希望跟“重新生成”状态挂钩也可以
        processed_text = getattr(self, 'current_session_processed', 0)
        
        if hasattr(self, 'batch_status_label'):
            self.batch_status_label.config(text=f'待处理: {pending} 张 | 本次已处理: {processed_text} 张')
    
    def select_size_preset(self, preset):
        """选择尺寸预设"""
        old_preset_id = self.current_size_preset['id']
        self.current_size_preset = preset
        self.image_processor.set_canvas_size(preset['width'], preset['height'])
        
        # 计算适合显示区域的画布尺寸（占可用空间的90%）
        window_width = self.winfo_width() or self.winfo_screenwidth() * 0.85
        window_height = self.winfo_height() or self.winfo_screenheight() * 0.85
        # 左面板约120px，右面板约320px，工具栏约50px，边距约40px
        available_width = int((window_width - 120 - 320 - 40) * 0.9)
        available_height = int((window_height - 50 - 40) * 0.9)
        
        ratio = preset['width'] / preset['height']
        
        if ratio > available_width / available_height:
            # 宽图，以宽度为准
            display_width = available_width
            display_height = int(display_width / ratio)
        else:
            # 高图或方图，以高度为准
            display_height = available_height
            display_width = int(display_height * ratio)
        
        self.canvas_widget.resize_canvas(display_width, display_height)
        
        # 更新按钮选中效果 (Label)
        if hasattr(self, 'size_preset_buttons'):
            for pid, btn in self.size_preset_buttons.items():
                if pid == preset['id']:
                    btn.config(bg=COLORS['selected_bg'], fg=COLORS['text_bright'])
                else:
                    btn.config(bg=COLORS['bg_tertiary'], fg=COLORS['text_primary'])
        
        # 如果已有图片，重新调整大小
        # [FIX] 无论是否有图片，都需要刷新画布以重新应用边框
        # self.refresh_canvas 内部会处理无图片的情况 (清除主图并应用边框)
        self.refresh_canvas()
            
        # [OPTIMIZE] 响应式文字优化
        # 使用统一的辅助方法计算字号
        optimal_font_size = self._get_default_font_size(preset)
        
        # 更新字号设置
        if hasattr(self, 'font_size_var'):
            self.font_size_var.set(optimal_font_size)
            if hasattr(self, 'font_size_scale'):
                self.font_size_scale.set(optimal_font_size)
            if hasattr(self, 'font_size_label'):
                self.font_size_label.config(text=str(optimal_font_size))
        
        # [FIX] 同步更新配置，确保批量导出时即使没有创建文字层也能使用正确字号
        if hasattr(self, 'current_text_config'):
            self.current_text_config['font_size'] = optimal_font_size
                
        # 如果当前有文字层，更新其字号并重新应用
        if hasattr(self, 'current_text_layer') and self.current_text_layer:
            self.current_text_layer.font_size = optimal_font_size
            # 重新渲染文字
            self._auto_apply_text()
            
    def _get_default_font_size(self, preset):
        """根据预设ID获取默认字号"""
        pid = preset.get('id')
        
        # 1. 2寸证件照 -> 30
        if pid == 'id_photo_2inch':
            return 30
            
        # 2. 正方形 / 自定义 -> 60
        if pid in ['square_1_1', 'custom', 'custom_size']:
            return 60
            
        # 3. 小红书 / 海报 -> 96
        if pid in ['xiaohongshu_3_4', 'post_16_9', 'post_9_16']:
            return 96
            
        # 4. 其他 (如1寸) -> 使用面积公式
        area = preset['width'] * preset['height']
        # Formula: sqrt(Area * 0.4 / 100)
        optimal = int((area * 0.4 / 100) ** 0.5)
        return max(24, min(150, optimal))
        
        # 重新应用背景颜色
        if hasattr(self, 'background_color') and self.background_color:
            self.canvas_widget.set_background_color(self.background_color)
        
        # 延迟重新应用边框（等待画布更新完成）
        self.after(50, self.reapply_border_after_resize)
        
        print(f"✓ 尺寸设置: {preset['name']} ({preset['width']}×{preset['height']})")
    
    def reapply_border_after_resize(self):
        """尺寸调整后重新应用边框"""
        if hasattr(self, 'border_config') and self.border_config['width'] > 0:
            self.canvas_widget.apply_custom_border(self.border_config)
    
    def apply_transform(self, transform_type, angle=None):
        """应用变换操作"""
        if not self.image_processor.current_image:
            messagebox.showwarning('提示', '请先上传图片！')
            return
        
        if transform_type == 'rotate':
            self.image_processor.rotate_image(angle)
            action_name = f"旋转{abs(angle)}°"
        elif transform_type == 'flip_h':
            self.image_processor.flip_image(horizontal=True)
            action_name = "水平翻转"
        elif transform_type == 'flip_v':
            self.image_processor.flip_image(horizontal=False)
            action_name = "垂直翻转"
        else:
            return
        
        self.image_processor.resize_to_canvas(maintain_ratio=True)
        self.refresh_canvas()
        self.save_history(action_name)
    
    def toggle_filter(self, filter_type, btn):
        """切换滤镜状态"""
        if not self.image_processor.current_image:
            messagebox.showwarning('提示', '请先上传图片！')
            return
        
        filter_names = {
            'grayscale': '黑白', 'sharpen': '锐化', 'blur': '模糊',
            'smooth': '平滑', 'contour': '轮廓', 'emboss': '浮雕'
        }
        
        if filter_type in self.active_filters:
            # 取消滤镜 - 重置图片并重新应用其他活跃滤镜
            self.active_filters.discard(filter_type)
            btn.config(
                text=self.filter_base_texts[filter_type],
                bg=COLORS['bg_tertiary'],
                fg=COLORS['text_primary']  # 恢复原文字颜色
            )
            # 从原始图片开始重新应用所有活跃滤镜
            self.reapply_all_filters()
            self.save_history(f"取消{filter_names.get(filter_type, filter_type)}滤镜")
        else:
            # 应用滤镜
            self.active_filters.add(filter_type)
            btn.config(
                text=self.filter_base_texts[filter_type] + " ✓",
                bg=COLORS['accent'],
                fg='white'  # 白色文字确保可读性
            )
            self.image_processor.apply_filter(filter_type)
            self.refresh_canvas()
            self.save_history(f"应用{filter_names.get(filter_type, filter_type)}滤镜")
    
    def reapply_all_filters(self):
        """重新应用所有活跃滤镜"""
        # 从原始图片开始
        self.image_processor.reset_image()
        if self.image_processor.current_image:
            self.image_processor.resize_to_canvas(maintain_ratio=True)
            # 重新应用所有活跃滤镜
            for f_type in self.active_filters:
                self.image_processor.apply_filter(f_type)
            self.refresh_canvas()
    
    def apply_filter(self, filter_type):
        """应用滤镜（单次应用，不可切换）"""
        if not self.image_processor.current_image:
            messagebox.showwarning('提示', '请先上传图片！')
            return
        
        filter_names = {
            'grayscale': '黑白', 'sharpen': '锐化', 'blur': '模糊',
            'smooth': '平滑', 'contour': '轮廓', 'emboss': '浮雕'
        }
        
        self.image_processor.apply_filter(filter_type)
        self.refresh_canvas()
        self.save_history(f"应用{filter_names.get(filter_type, filter_type)}滤镜")
    
    def apply_adjustment(self, adjust_type):
        """应用图片调整"""
        if not self.image_processor.current_image:
            messagebox.showwarning('提示', '请先上传图片！')
            return
        
        if adjust_type == 'brightness':
            factor = self.brightness_scale.get()
            self.image_processor.adjust_brightness(factor)
            action_name = f"亮度调整({factor})"
        elif adjust_type == 'contrast':
            factor = self.contrast_scale.get()
            self.image_processor.adjust_contrast(factor)
            action_name = f"对比度调整({factor})"
        elif adjust_type == 'saturation':
            factor = self.saturation_scale.get()
            self.image_processor.adjust_saturation(factor)
            action_name = f"饱和度调整({factor})"
        else:
            return
        
        self.refresh_canvas()
        self.save_history(action_name)
    
    def reset_image_and_sliders(self):
        """重置图片和滑块"""
        self.image_processor.reset_image()
        if self.image_processor.current_image:
            self.image_processor.resize_to_canvas(maintain_ratio=True)
            self.refresh_canvas()
            
            # 重置滑块
            if hasattr(self, 'brightness_scale'):
                self.brightness_scale.set(1.0)
            if hasattr(self, 'contrast_scale'):
                self.contrast_scale.set(1.0)
            if hasattr(self, 'saturation_scale'):
                self.saturation_scale.set(1.0)
            
            self.save_history("重置图片")
    
    def reset_single_adjustment(self, adjust_type):
        """重置单个调整滑块"""
        if not self.image_processor.current_image:
            messagebox.showwarning('提示', '请先上传图片！')
            return
        
        if adjust_type == 'brightness' and hasattr(self, 'brightness_scale'):
            self.brightness_scale.set(1.0)
        elif adjust_type == 'contrast' and hasattr(self, 'contrast_scale'):
            self.contrast_scale.set(1.0)
        elif adjust_type == 'saturation' and hasattr(self, 'saturation_scale'):
            self.saturation_scale.set(1.0)
        
        # 从原始图片重新应用所有当前调整值
        self.image_processor.reset_image()
        if self.image_processor.current_image:
            self.image_processor.resize_to_canvas(maintain_ratio=True)
            
            # 重新应用活跃滤镜
            for f_type in getattr(self, 'active_filters', []):
                self.image_processor.apply_filter(f_type)
            
            # 应用当前滑块值
            if hasattr(self, 'brightness_scale') and self.brightness_scale.get() != 1.0:
                self.image_processor.adjust_brightness(self.brightness_scale.get())
            if hasattr(self, 'contrast_scale') and self.contrast_scale.get() != 1.0:
                self.image_processor.adjust_contrast(self.contrast_scale.get())
            if hasattr(self, 'saturation_scale') and self.saturation_scale.get() != 1.0:
                self.image_processor.adjust_saturation(self.saturation_scale.get())
            
            self.refresh_canvas()
            name_map = {'brightness': '亮度', 'contrast': '对比度', 'saturation': '饱和度'}
            self.save_history(f"重置{name_map.get(adjust_type, adjust_type)}")
    
    def upload_image(self):
        """上传图片"""
        file_path = filedialog.askopenfilename(
            title='选择图片',
            filetypes=[
                ('图片文件', '*.jpg *.jpeg *.png *.bmp *.gif'),
                ('所有文件', '*.*')
            ]
        )
        
        if file_path:
            if self.image_processor.load_image(file_path):
                self.image_processor.resize_to_canvas(maintain_ratio=True)
                self.refresh_canvas()
                self.save_history("上传图片")
                # messagebox.showinfo('成功', '图片上传成功！')
            else:
                messagebox.showerror('错误', '图片加载失败！')
    
    def reset_image(self):
        """重置图片"""
        self.image_processor.reset_image()
        if self.image_processor.current_image:
            self.image_processor.resize_to_canvas(maintain_ratio=True)
            self.refresh_canvas()
            self.save_history("重置图片")
    
    def add_sticker(self, sticker):
        """添加贴纸（兼容旧方法）"""
        # 如果有PNG图片文件，优先使用图片
        sticker_path = os.path.join(os.path.dirname(__file__), 'assets', 'stickers', sticker.get('file', ''))
        if os.path.exists(sticker_path):
            try:
                # 加载PNG贴纸，但还是用emoji显示（因为canvas_widget当前使用emoji）
                # TODO: 后续可以支持真正的图片贴纸
                self.canvas_widget.add_sticker(sticker['emoji'], font_size=48)
            except Exception as e:
                print(f"加载贴纸图片失败: {e}")
                self.canvas_widget.add_sticker(sticker['emoji'], font_size=48)
        else:
            self.canvas_widget.add_sticker(sticker['emoji'], font_size=48)
        
        self.save_history("添加贴纸")
        self.update_layer_list()
    
    def add_sticker_from_file(self, category_type, filename):
        """从文件添加贴纸 - 直接加载PNG图片"""
        file_path = os.path.join(
            os.path.dirname(__file__),
            'assets', 'stickers',
            category_type,
            filename
        )
        
        if not os.path.exists(file_path):
            print(f"贴纸文件不存在: {file_path}")
            return
        
        # 直接加载PNG图片并添加到画布
        try:
            # 检查缓存
            cache_key = f"{category_type}/{filename}"
            if cache_key in self.sticker_image_cache:
                # 从缓存获取
                img = self.sticker_image_cache[cache_key].copy()
            else:
                # 加载新图片
                img = Image.open(file_path).convert('RGBA')
                # 缓存原始图片（保持高分辨率）
                self.sticker_image_cache[cache_key] = img.copy()
            
            # 调整大小为合适的尺寸（96像素，增大一倍以保持清晰度）
            sticker_size = 96
            img = img.resize((sticker_size, sticker_size), Image.Resampling.LANCZOS)
            
            # 添加到画布
            self.canvas_widget.add_sticker_image(img, size=sticker_size, category=category_type, image_path=file_path)
            
            self.save_history("添加贴纸")
            self.update_layer_list()
        except Exception as e:
            print(f"加载贴纸图片失败 {file_path}: {e}")
            # 降级方案：尝试使用emoji字符
            base_name = filename.replace('_3d.png', '').replace('_fluent_3d.png', '').replace('.png', '')
            emoji_char = '🎨'
            for sticker in STICKER_LIST:
                sticker_id = sticker.get('id', '')
                if sticker_id == base_name or base_name in sticker_id or sticker_id in base_name:
                    emoji_char = sticker.get('emoji', '🎨')
                    break
            self.canvas_widget.add_sticker(emoji_char, font_size=48)
            self.save_history("添加贴纸")
            self.update_layer_list()
    
    def rotate_image(self, angle):
        """旋转图片"""
        if self.image_processor.base_image:
            rotated = self.image_processor.base_image.rotate(angle, expand=True)
            self.image_processor.base_image = rotated
            self.image_processor.current_image = rotated
            self.image_processor.resize_to_canvas(maintain_ratio=True)
            self.refresh_canvas()
            self.save_history("旋转图片")
    
    def flip_image(self, direction):
        """翻转图片"""
        if self.image_processor.base_image:
            from PIL import Image as PILImage
            if direction == 'horizontal':
                flipped = self.image_processor.base_image.transpose(PILImage.FLIP_LEFT_RIGHT)
            else:  # vertical
                flipped = self.image_processor.base_image.transpose(PILImage.FLIP_TOP_BOTTOM)
            
            self.image_processor.base_image = flipped
            self.image_processor.current_image = flipped
            self.image_processor.resize_to_canvas(maintain_ratio=True)
            self.refresh_canvas()
            self.save_history("翻转图片")
    
    def select_border(self, border):
        """选择边框"""
        self.current_border = border
        self.canvas_widget.add_border(border)
        self.save_history("选择边框")
    
    def delete_selected_sticker(self):
        """删除选中的贴纸"""
        if self.canvas_widget.delete_selected_sticker():
            self.save_history("删除贴纸")
            self.update_layer_list()
            messagebox.showinfo('成功', '贴纸已删除')
        else:
            messagebox.showwarning('提示', '请先点击选择要删除的贴纸')
    
    def refresh_canvas(self):
        """刷新画布"""
        current_image = self.image_processor.get_current_image()
        if current_image:
            self.canvas_widget.display_image(current_image)
        else:
            # 没有图片时清除画布上的主图片
            self.canvas_widget.clear_main_image()
            
        # 恢复背景图案
        if hasattr(self, 'background_pattern'):
            self.canvas_widget.set_background_pattern(
                self.background_pattern,
                self.background_color,
                self.background_pattern_color,
                self.background_pattern_size
            )
        
        # 始终应用边框配置 (无论是否有图片)
        self.canvas_widget.apply_custom_border(self.border_config)
            
        # 确保顺序生效后再强制定序一次 (处理异步渲染)
        self.after(50, lambda: self.canvas_widget._ensure_layer_order())
        
        # 更新图层列表 (如果已创建)
        if hasattr(self, 'update_layer_list'):
            self.update_layer_list()
    
    def export_image(self):
        """导出图片 (支持无图片导出，仅背景+文字)"""
        # 不再强制要求上传图片
        
        # 生成默认文件名
        default_name = f"tupian_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        
        file_path = filedialog.asksaveasfilename(
            title='保存图片',
            defaultextension='.png',
            initialfile=default_name,
            filetypes=[
                ('PNG图片', '*.png'),
                ('JPEG图片', '*.jpg'),
                ('所有文件', '*.*')
            ]
        )
        
        if file_path:
            try:
                # 获取导出参数
                preset_width = self.current_size_preset['width']
                preset_height = self.current_size_preset['height']
                
                # 使用 ExportManager 创建图片
                final_img = self.export_manager.create_export_image(
                    preset_width=preset_width,
                    preset_height=preset_height,
                    background_color=self.background_color,
                    background_pattern=self.background_pattern,
                    background_pattern_color=self.background_pattern_color,
                    background_pattern_size=self.background_pattern_size,
                    main_image=self.image_processor.current_image,
                    main_image_id=self.canvas_widget.main_image_id,
                    canvas_widget=self.canvas_widget, 
                    text_layers=getattr(self, 'current_text_layer', None),
                    stickers=self.canvas_widget.get_stickers(),
                    border_config=self.border_config
                )
                
                # 保存文件
                final_img.save(file_path)
                
                # 根据勾选框状态决定是否自动保存预设
                save_msg = f'图片已保存到:\n{file_path}'
                if hasattr(self, 'auto_save_preset_var') and self.auto_save_preset_var.get():
                    self.save_preset_theme(silent=True)
                    save_msg += '\n\n✓ 主题预设已自动保存'
                
                # 询问是否打开目录
                if messagebox.askyesno('导出成功', save_msg + '\n\n是否打开所在目录？'):
                    try:
                        folder_path = os.path.dirname(file_path)
                        if hasattr(self, 'open_directory'):
                            self.open_directory(folder_path, select_file=file_path)
                        else:
                            subprocess.run(['open', '-R', file_path])
                    except Exception as e:
                        print(f"打开目录失败: {e}")
                        
            except Exception as e:
                import traceback
                traceback.print_exc()
                messagebox.showerror('导出失败', f'导出过程中发生错误:\n{str(e)}')
    
    def select_input_dir(self):
        """选择输入目录"""
        dir_path = filedialog.askdirectory(title='选择输入目录', initialdir=self.batch_input_dir or None)
        if dir_path:
            self.batch_input_dir = dir_path
            self.input_dir_label.config(text=dir_path)
            self.save_settings()
            # [UX] 自动加载图片，无需手动点击按钮
            self.after(100, self.load_from_input_dir)
    
    def select_output_dir(self):
        """选择输出目录"""
        dir_path = filedialog.askdirectory(title='选择输出目录', initialdir=self.batch_output_dir or None)
        if dir_path:
            self.batch_output_dir = dir_path
            self.output_dir_label.config(text=dir_path)
            self.save_settings()
    
    def download_excel_template(self):
        """下载 Excel 模板"""
        template_source = os.path.join('assets', 'template', '文案保存模版.xlsx')
        if not os.path.exists(template_source):
             messagebox.showerror('错误', '找不到模板文件！')
             return

        save_path = filedialog.asksaveasfilename(
            title='保存模板',
            initialfile='文案保存模版.xlsx',
            defaultextension='.xlsx',
            filetypes=[('Excel 文件', '*.xlsx')]
        )
        if save_path:
            try:
                import shutil
                shutil.copy2(template_source, save_path)
                messagebox.showinfo('成功', f'模板已保存到:\n{save_path}')
                
                # 询问是否立即打开
                if messagebox.askyesno('提示', '是否立即打开模板文件？'):
                    # 尝试打开文件
                    if sys.platform == 'darwin':
                        subprocess.run(['open', save_path])
                    elif sys.platform == 'win32':
                        os.startfile(save_path)
                    else:
                        subprocess.run(['xdg-open', save_path])
                        
            except Exception as e:
                messagebox.showerror('错误', f'保存模板失败: {e}')

    def select_excel_file(self):
        """选择 Excel 文件"""
        file_path = filedialog.askopenfilename(
            title='选择文案Excel数据表',
            filetypes=[('Excel 文件', '*.xlsx'), ('Excel 97-2003', '*.xls')],
            initialdir=os.path.dirname(self.batch_text_dir) if self.batch_text_dir else None
        )
        if file_path:
            self.batch_text_dir = file_path 
            if hasattr(self, 'text_dir_label'):
                self.text_dir_label.config(text=file_path)
            self.save_settings()
    
    def show_toast(self, message, duration=2000):
        """显示非阻塞的 Toast 提示"""
        toast = tk.Toplevel(self)
        toast.overrideredirect(True)  # 无边框
        
        # 计算位置（居中显示）
        window_width = self.winfo_width()
        window_height = self.winfo_height()
        window_x = self.winfo_rootx()
        window_y = self.winfo_rooty()
        
        # 创建内容
        frame = tk.Frame(toast, bg='#333333', padx=20, pady=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(frame, text=message, fg='white', bg='#333333', 
                 font=('SF Pro Text', 11)).pack()
        
        # 调整大小和位置
        toast.update_idletasks()
        toast_width = toast.winfo_width()
        toast_height = toast.winfo_height()
        
        x = window_x + (window_width - toast_width) // 2
        y = window_y + (window_height - toast_height) // 2 + 100 #稍微偏下
        
        toast.geometry(f"{toast_width}x{toast_height}+{x}+{y}")
        
        # 确保在最上层
        toast.attributes('-topmost', True)
        toast.lift()
        
        # 设置圆角效果（macOS特有，Windows可能不生效但也不报错）
        try:
            toast.attributes('-transparent', True) # 尝试透明
        except:
            pass
            
        # 自动关闭
        toast.after(duration, toast.destroy)

    def load_from_input_dir(self):
        """从输入目录加载图片"""
        if not self.batch_input_dir:
            self.show_toast('请先设置输入目录')
            return
        
        if not os.path.isdir(self.batch_input_dir):
            messagebox.showerror('错误', '输入目录不存在')
            return
        
        # 获取目录中所有图片
        extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.gif')
        all_images = []
        for f in os.listdir(self.batch_input_dir):
            if f.lower().endswith(extensions):
                all_images.append(os.path.join(self.batch_input_dir, f))
        
        self.batch_images = all_images
        
        # 统计已处理（历史）和未处理
        # 注意：这里的 pending 是基于历史记录的，用于增量处理
        pending = [p for p in all_images if os.path.basename(p) not in self.processed_images]
        
        # 重置当前会话的“本次已处理”计数
        self.current_session_processed = 0
        
        self.batch_count_label.config(text=f'已加载: {len(all_images)} 张图片')
        if hasattr(self, 'batch_status_label'):
             # UI显示：待处理(增量) | 本次已处理
             self.batch_status_label.config(text=f'待处理: {len(pending)} 张 | 本次已处理: 0 张')
        
        if all_images:
            self.show_toast(f'成功加载 {len(all_images)} 张图片')
        else:
            messagebox.showwarning('提示', '目录中没有图片文件')
    
    def batch_upload(self):
        """批量上传图片"""
        file_paths = filedialog.askopenfilenames(
            title='批量选择图片',
            filetypes=[
                ('图片文件', '*.jpg *.jpeg *.png *.bmp *.gif'),
                ('所有文件', '*.*')
            ]
        )
        
        if file_paths:
            self.batch_images = list(file_paths)
            self.batch_count_label.config(text=f'已选择: {len(self.batch_images)} 张图片')
            messagebox.showinfo('成功', f'已选择 {len(self.batch_images)} 张图片')
    
    def get_random_color(self):
        """随机获取颜色 (马卡龙 + 多巴胺色系)"""
        import random
        from constants import MACARON_COLORS, DOPAMINE_COLORS
        return random.choice(MACARON_COLORS + DOPAMINE_COLORS)
    
    def get_random_highlight_color(self):
        """随机获取高亮颜色 (仅限亮色)"""
        import random
        from constants import BRIGHT_HIGHLIGHT_COLORS
        return random.choice(BRIGHT_HIGHLIGHT_COLORS)

    def get_random_line_style(self):
        """随机获取线条样式"""
        import random
        from constants import LINE_STYLES
        return random.choice(LINE_STYLES)['id']

    def get_random_pattern(self):
        """随机获取边框图案"""
        import random
        from constants import BORDER_PATTERNS
        # 排除 'none'
        patterns = [p['id'] for p in BORDER_PATTERNS if p['id'] != 'none']
        return random.choice(patterns) if patterns else 'dots'

    def one_click_randomize(self, record_history=True):
        """摇一摇爆文骰：带动画的随机效果"""
        if hasattr(self, 'is_randomizing') and self.is_randomizing:
            return
            
        self.is_randomizing = True
        self.random_step_count = 0
        self.max_random_steps = 6 # 用户指定6次
        self.dice_icons = ['⚀', '⚁', '⚂', '⚃', '⚄', '⚅']
        
        # 禁用按钮交互
        if hasattr(self, 'random_btn'):
            self.original_btn_text = self.random_btn.cget('text')
            
        # 开始动画序列
        self._animate_random_sequence(record_history)
        
    def _animate_random_sequence(self, record_history=True):
        """执行随机动画序列"""
        import random
        
        # 更新骰子图标
        if hasattr(self, 'random_btn'):
            dice = self.dice_icons[self.random_step_count % len(self.dice_icons)]
            self.random_btn.config(text=f'{dice} 摇一摇...')
            
        # 应用随机样式 (不保存历史，除非最后一次且启用记录)
        is_last = (self.random_step_count >= self.max_random_steps - 1)
        # 仅在最后一步且 record_history=True 时保存历史
        should_save = is_last and record_history
        self._apply_random_style(save_history=should_save)
        
        if not is_last:
            self.random_step_count += 1
            # 动效时间递增: 50, 100, 150... 
            # 或者固定快速播放: 100ms
            delay = 100 + (self.random_step_count * 20)
            self.after(delay, lambda: self._animate_random_sequence(record_history))
        else:
            # 动画结束
            self.is_randomizing = False
            if hasattr(self, 'random_btn'):
                self.random_btn.config(text='🎲 摇一摇爆文骰')
            # self.show_toast("爆文样式已生成！")

    def _apply_random_style(self, save_history=True):
        """应用随机样式（内部实现）"""
        import random
        from constants import BORDER_PATTERNS
        
        if save_history:
            self.save_history("一键随机")
            
        if not hasattr(self, 'canvas_widget'): return

        # 1. 随机背景 (50% 纯色, 50% 图案)
        if random.random() < 0.5:
            # 纯色
            new_bg = self.get_random_color()
            self.set_background_color(new_bg)
            self.set_bg_pattern('none')
            self.background_pattern = 'none'
        else:
            # 图案
            # 仅使用支持的背景图案
            bg_patterns = ['stripe', 'dots', 'grid', 'horizontal', 'vertical']
            new_pattern = random.choice(bg_patterns)
            new_pat_col = self.get_random_color()
            # 随机底色
            new_bg = self.get_random_color()
            
            self.set_background_color(new_bg)
            self.set_bg_pattern(new_pattern)
            self.background_pattern_color = new_pat_col
            self.background_pattern_size = random.randint(15, 40)
            
            self.canvas_widget.set_background_pattern(
                 new_pattern, new_bg, new_pat_col, self.background_pattern_size
            )
            # 同步UI
            if hasattr(self, 'bg_pattern_color_canvas'):
                 self.bg_pattern_color_canvas.config(bg=new_pat_col)
            if hasattr(self, 'bg_pattern_size_scale'):
                 self.bg_pattern_size_scale.set(self.background_pattern_size)
                 if hasattr(self, 'bg_pattern_size_label'):
                     self.bg_pattern_size_label.config(text=f'{self.background_pattern_size}px')

        # 2. 随机边框
        new_border = self.border_config.copy()
        new_border['color'] = self.get_random_color()
        
        # 30% 概率纯线条，70% 概率图案
        if random.random() < 0.3:
             new_border['pattern'] = 'none'
             new_border['line_style'] = self.get_random_line_style()
        else:
             new_border['pattern'] = self.get_random_pattern()
             new_border['pattern_size'] = random.randint(10, 30)
             
        # 应用边框
        self.border_config = new_border
        self.canvas_widget.apply_custom_border(new_border)
        
        # 同步边框UI
        self.selected_border_color = new_border['color']
        if hasattr(self, 'border_color_canvas'):
             self.border_color_canvas.config(bg=new_border['color'])
        if hasattr(self, 'border_color_hex_label'):
             self.border_color_hex_label.config(text=new_border['color'])


        # 3. 随机文字样式 (如果有文字)
        if hasattr(self, 'text_content_entry'):
            current_text = self.text_content_entry.get('1.0', tk.END).strip()
            if current_text:
                # 随机字体
                fonts = ['yuanti', 'kaiti', 'songti', 'heiti', 'pingfang', 'Arial']
                new_font = random.choice(fonts)
                if hasattr(self, 'font_var'):
                    font_display_map = {
                        'yuanti': 'ST圆体 (默认)', 'kaiti': '楷体', 'songti': '宋体',
                        'heiti': '黑体', 'pingfang': '苹方', 'Arial': 'Arial'
                    }
                    self.font_var.set(font_display_map.get(new_font, new_font))
                
                # 计算背景亮度以选择对比文字颜色
                bg_color = getattr(self, 'background_color', '#FFFFFF')
                try:
                    r = int(bg_color[1:3], 16)
                    g = int(bg_color[3:5], 16)
                    b = int(bg_color[5:7], 16)
                    brightness = (r * 299 + g * 587 + b * 114) / 1000
                except:
                    brightness = 200
                    
                # 如果背景亮，用深色文字；否则用浅色文字
                if brightness > 128:
                    text_color_pool = ['#000000', '#1C1C1E', '#2C2C2E', '#3A3A3C', '#48484A']
                else:
                    text_color_pool = ['#FFFFFF', '#F5F5F7', '#E5E5E7', '#D1D1D6', '#C7C7CC']
                    
                new_text_color = random.choice(text_color_pool)
                if hasattr(self, 'text_color_canvas'):
                    self.text_color_canvas.config(bg=new_text_color)
                if hasattr(self, 'text_color_var'):
                    self.text_color_var.set(new_text_color)
                    
                # 总是使用 'random' 高亮颜色，让每个关键词颜色不同
                if hasattr(self, 'highlight_color_var'):
                    self.highlight_color_var.set('random')
                
                # 触发重新渲染
                self._auto_apply_text()

        # 4. 随机贴纸内容 (保持位置不变)
        current_stickers = self.canvas_widget.get_stickers()
        if current_stickers:
            # 需要清空并重建贴纸以更新内容
            # 先收集旧数据
            old_stickers_data = [] 
            for s in current_stickers:
                old_stickers_data.append(s.copy())
                
            self.canvas_widget.delete_selected_sticker()
            self.canvas_widget.stickers = [] # 清空数据 List
            self.canvas_widget.canvas.delete('sticker') # 清空 Canvas 对应 Tag
            
            sticker_base_dir = os.path.join(os.path.dirname(__file__), 'assets', 'stickers')
            
            for s in old_stickers_data:
                category = s.get('category', 'fluent_3d')
                if not category: category = 'fluent_3d'
                
                target_dir = os.path.join(sticker_base_dir, category)
                if not os.path.exists(target_dir): 
                    target_dir = os.path.join(sticker_base_dir, 'fluent_3d')
                
                candidates = []
                if os.path.exists(target_dir):
                    candidates = [os.path.join(target_dir, f) for f in os.listdir(target_dir) if f.lower().endswith('.png')]
                
                if candidates:
                    new_path = random.choice(candidates)
                    try:
                        img = Image.open(new_path).convert('RGBA')
                        size = s['size']
                        img = img.resize((size, size), Image.Resampling.LANCZOS)
                        
                        self.canvas_widget.add_sticker_image(
                             img, 
                             size=size, 
                             category=category, 
                             image_path=new_path,
                             x=s['x'], 
                             y=s['y']
                        )
                    except Exception as e: 
                        print(f"Failed to replace sticker: {e}")
                else:
                    # 如果找不到候选，且原图也不存在，则跳过
                     pass
        
        # 提示（可选，或者静默）
        # messagebox.showinfo("提示", "已应用随机风格！")


    def open_directory(self, path, select_file=None):
        """打开目录，支持选中文件"""
        if not os.path.exists(path):
            self.show_toast(f"目录不存在: {path}")
            return
            
        import platform
        import subprocess
        
        system = platform.system()
        try:
            if system == 'Darwin':  # macOS
                if select_file and os.path.exists(select_file):
                    subprocess.run(['open', '-R', select_file])
                else:
                    subprocess.run(['open', path])
            elif system == 'Windows':  # Windows
                if select_file and os.path.exists(select_file):
                    subprocess.run(['explorer', '/select,', os.path.normpath(select_file)])
                else:
                    os.startfile(path)
            else:  # Linux
                subprocess.run(['xdg-open', path])
        except Exception as e:
            self.show_toast(f"无法打开目录: {e}")
            print(f"Open directory error: {e}")
            messagebox.showerror('错误', f'无法打开目录: {e}')

    def _load_text_mapping(self, source_path):
        """加载文字映射 (统一模版格式)，优先读取未使用的行"""
        mapping = {}
        sequential_list = []
        
        if not source_path or not os.path.isfile(source_path):
            return None, []
            
        try:
            import openpyxl
            from datetime import datetime
            
            wb = openpyxl.load_workbook(source_path, data_only=False)
            ws = wb.active
            
            has_update = False
            current_date = datetime.now().strftime('%Y-%m-%d')
            
            # 收集所有可用行 (从第3行开始，第1-2行是表头)
            # 模版列: A:图片名, B:主题, C:风格, D:文字内容, E:使用日期, F:使用时间
            unused_rows = []  # 没有使用日期的行
            used_rows = []    # 有使用日期的行 (备用)
            
            for row_idx in range(3, ws.max_row + 1):
                content = ws.cell(row=row_idx, column=4).value  # D: 文字内容
                use_date = ws.cell(row=row_idx, column=5).value  # E: 使用日期
                img_name = ws.cell(row=row_idx, column=1).value  # A: 图片名
                
                if not content:
                    continue  # 跳过没有内容的行
                    
                content = str(content).strip()
                row_data = {
                    'row': row_idx,
                    'content': content,
                    'img_name': str(img_name).strip() if img_name else None
                }
                
                if not use_date:
                    unused_rows.append(row_data)
                else:
                    used_rows.append(row_data)
            
            # 优先使用未使用的行，然后是已使用的行
            all_rows = unused_rows + used_rows
            
            for row_data in all_rows:
                content = row_data['content']
                img_name = row_data['img_name']
                row_idx = row_data['row']
                
                if img_name:
                    # 有图片名，加入映射
                    mapping[img_name] = content
                else:
                    # 无图片名，加入顺序列表 (使用 dict 格式兼容 batch_processor)
                    sequential_list.append({'content': content, '文字内容': content})
                
                # 标记为已使用 (写入当前日期到 E 列)
                ws.cell(row=row_idx, column=5, value=current_date)
                has_update = True
            
            if has_update:
                try:
                    wb.save(source_path)
                    print(f"[INFO] 已更新 Excel 使用日期: {source_path}")
                except Exception as e:
                    print(f"[ERROR] 无法回写 Excel: {e}")
                    self.show_toast(f"无法更新Excel: 文件被占用?")
                    
        except Exception as e:
            print(f"读取 Excel 失败: {e}")
            self.show_toast(f"读取 Excel 失败: {e}")
                
        return mapping, sequential_list

    def _dismiss_batch_help(self):
        """关闭批量处理使用说明"""
        self.show_batch_help = False
        if hasattr(self, 'batch_help_frame'):
            self.batch_help_frame.pack_forget()
        self.save_settings()

    def batch_export(self):
        """批量导出图片"""
        if not self.batch_images and not (self.batch_use_text_dir.get() and self.batch_text_dir):
            messagebox.showwarning('提示', '请先加载图片 或 启用批量文字！')
            return
        
        # 使用记忆的输出目录或选择新目录
        output_dir = self.batch_output_dir
        if not output_dir or not os.path.isdir(output_dir):
            output_dir = filedialog.askdirectory(title='选择输出目录', initialdir=self.batch_output_dir or None)
            if output_dir:
                self.batch_output_dir = output_dir
                if hasattr(self, 'output_dir_label'):
                    self.output_dir_label.config(text=output_dir)
                self.save_settings()
        
        if not output_dir:
            return

        # 准备配置参数
        preset_config = {
            'width': self.current_size_preset['width'],
            'height': self.current_size_preset['height']
        }
        
        random_options = {
            'color': self.batch_random_color.get(),
            'style': self.batch_random_style.get(),
            'pattern': self.batch_random_pattern.get(),
            'background': self.batch_random_background_style.get(),
            'stickers': self.batch_random_stickers.get()
        }
        
        # 加载 Excel 映射
        text_mapping = {}
        text_sequence = []
        if self.batch_use_text_dir.get() and self.batch_text_dir and os.path.exists(self.batch_text_dir):
            try:
                text_mapping, text_sequence = self._load_text_mapping(self.batch_text_dir)
            except Exception as e:
                self.batch_log(f"预加载 Excel 失败: {e}")
                
        text_config = {
            'use_text_dir': self.batch_use_text_dir.get(),
            'text_dir': self.batch_text_dir,
            'text_mapping': text_mapping,
            'text_sequence': text_sequence,
            'template_layer': getattr(self, 'current_text_layer', None),
            'default_font_size': self.font_size_var.get() if hasattr(self, 'font_size_var') else 48,
            'default_font_family': self.font_family_var.get() if hasattr(self, 'font_family_var') else 'PingFang SC'
        }
        
        background_config = {
            'color': self.background_color,
            'pattern': self.background_pattern,
            'pattern_color': self.background_pattern_color,
            'pattern_size': self.background_pattern_size
        }
        
        # 查找字体 Key (从中文名称反查)
        # Font map: key -> display_name
        current_font_name = self.font_family_var.get() if hasattr(self, 'font_family_var') else 'ST圆体 (默认)'
        font_key = 'yuanti'
        if hasattr(self, 'image_processor'):
             # 使用 TextLayer 类属性
             from image_processor import TextLayer
             for k, v in TextLayer.FONT_NAMES.items():
                 if v == current_font_name:
                     font_key = k
                     break
        else:
             # 手动简单映射
             display_map = {'ST圆体 (默认)': 'yuanti', '苹方': 'pingfang', '冬青黑体': 'hiragino', 
                            'ST黑体': 'heiti', 'ST宋体': 'songti', 'ST楷体': 'kaiti'}
             font_key = display_map.get(current_font_name, 'yuanti')

        text_config.update({'default_font_family': font_key})
        
        # 确定处理列表
        images_to_process = self.batch_images if self.batch_images else [None] * len(text_sequence)
        if not images_to_process:
             messagebox.showwarning('提示', '未找到有效的图片或文字数据！')
             return

        # 启动处理生成器
        self.batch_log(f"═══ 开始批量处理 ═══")
        self.batch_log(f"待处理: {len(images_to_process)} 项")
        
        # 使用生成器更新 UI
        try:
            for progress in self.batch_processor.process_batch(
                images_to_process=images_to_process,
                output_dir=output_dir,
                preset_config=preset_config,
                base_border_config=self.border_config,
                random_options=random_options,
                text_config=text_config,
                sticker_config=self.canvas_widget.get_stickers(),
                background_config=background_config,
                canvas_widget=self.canvas_widget,
                match_canvas_geom=self.batch_match_canvas.get(),
                image_as_bg=self.batch_image_as_bg.get() if hasattr(self, 'batch_image_as_bg') else False # [NEW] 传入背景模式参数
            ):
                if hasattr(self, 'progress_var'):
                    self.progress_var.set(progress)
                self.update()
                
            self.show_toast(f"批量处理完成！")
            
            # 询问打开目录
            if messagebox.askyesno('完成', f'处理完成，是否打开输出目录？'):
                 try:
                     folder_path = output_dir
                     if hasattr(self, 'open_directory'):
                         self.open_directory(folder_path)
                     else:
                         subprocess.run(['open', '-R', folder_path])
                 except:
                     pass
                     
        except Exception as e:
            import traceback
            traceback.print_exc()
            messagebox.showerror('错误', f"批量处理中断: {str(e)}")

    def save_history(self, action_name="操作"):
        """保存历史记录"""
        import copy
        from datetime import datetime
        
        # 创建状态快照
        # 创建状态快照
        state = {
            'timestamp': datetime.now().strftime('%H:%M:%S'),
            'action': action_name,
            'border_config': copy.deepcopy(self.border_config),
            'background_color': self.background_color,
            'background_pattern': self.background_pattern,
            'background_pattern_color': self.background_pattern_color,
            'background_pattern_size': self.background_pattern_size,
            'image': self.image_processor.current_image.copy() if self.image_processor.current_image else None,
            'stickers': copy.deepcopy(self.canvas_widget.stickers) if hasattr(self.canvas_widget, 'stickers') else [],
            # 保存文字配置
            'text_config': {
                'content': self.text_content_entry.get('1.0', 'end-1c') if hasattr(self, 'text_content_entry') else '',
                'color': self.text_color_var.get() if hasattr(self, 'text_color_var') else '#333333',
                'font_family': self.font_family_var.get() if hasattr(self, 'font_family_var') else '苹方 (默认)',
                'font_size': self.font_size_scale.get() if hasattr(self, 'font_size_scale') else 48,
                'align': self.text_align_var.get() if hasattr(self, 'text_align_var') else 'center',
                'position': self.text_position_var.get() if hasattr(self, 'text_position_var') else 'bottom',
                'margin': self.text_margin_var.get() if hasattr(self, 'text_margin_var') else 20,
                'bold': self.text_bold_var.get() if hasattr(self, 'text_bold_var') else False,
                'italic': self.text_italic_var.get() if hasattr(self, 'text_italic_var') else False,
                'underline': self.text_underline_var.get() if hasattr(self, 'text_underline_var') else False,
                'shadow_enabled': self.text_shadow_var.get() if hasattr(self, 'text_shadow_var') else False,
                'stroke_enabled': self.text_stroke_var.get() if hasattr(self, 'text_stroke_var') else False,
                'stroke_width': self.stroke_width_var.get() if hasattr(self, 'stroke_width_var') else 2,
                'stroke_color': self.stroke_color_var.get() if hasattr(self, 'stroke_color_var') else '#000000',
                'highlight_enabled': self.highlight_enabled_var.get() if hasattr(self, 'highlight_enabled_var') else True
            }
        }
        
        # 如果不是在历史末尾，删除后面的记录
        if self.history_index < len(self.history_stack) - 1:
            self.history_stack = self.history_stack[:self.history_index + 1]
        
        # 添加新记录
        self.history_stack.append(state)
        self.history_index = len(self.history_stack) - 1
        
        # 限制历史记录数量
        if len(self.history_stack) > self.max_history:
            self.history_stack.pop(0)
            self.history_index -= 1
        
        # 更新历史记录UI（如果存在）
        if hasattr(self, 'history_listbox'):
            self.update_history_display()
    
    def undo(self):
        """撤销"""
        if self.history_index > 0:
            self.history_index -= 1
            self.restore_state(self.history_stack[self.history_index])
            if hasattr(self, 'history_listbox'):
                self.update_history_display()
        else:
            messagebox.showinfo('提示', '没有更多可撤销的操作')
    
    def redo(self):
        """重做"""
        if self.history_index < len(self.history_stack) - 1:
            self.history_index += 1
            self.restore_state(self.history_stack[self.history_index])
            if hasattr(self, 'history_listbox'):
                self.update_history_display()
        else:
            messagebox.showinfo('提示', '没有更多可重做的操作')
    
    def restore_state(self, state):
        """恢复到指定状态"""
        import copy
        
        # 恢复边框配置
        self.border_config = copy.deepcopy(state['border_config'])
        
        # 恢复背景配置
        self.background_color = state['background_color']
        self.background_pattern = state['background_pattern']
        self.background_pattern_color = state['background_pattern_color']
        self.background_pattern_size = state['background_pattern_size']
        
        # 恢复图片
        if state['image']:
            self.image_processor.current_image = state['image'].copy()
        
        # 清空并恢复贴纸
        self.canvas_widget.canvas.delete('sticker')
        self.canvas_widget.stickers = []
        if state.get('stickers'):
            for sticker_data in state['stickers']:
                # 重新创建贴纸
                visible = sticker_data.get('visible', True)
                
                if sticker_data.get('is_image') and sticker_data.get('image'):
                    # 恢复图片贴纸
                    # 使用保存的PIL图片对象
                    pil_img = sticker_data['image']
                    
                    # 确保尺寸一致 (虽然保存时应该是当前尺寸)
                    current_size = sticker_data.get('size', 96)
                    
                    # 重新渲染图片
                    # 注意: 直接使用 add_sticker_image 的逻辑，但需要手动处理 ID 和列表
                    # 或者我们可以调用 canvas_widget.add_sticker_image 但那会产生新的 sticker 数据
                    # 这里我们手动重建 canvas item
                    
                    # 重新生成 PhotoImage
                    if pil_img.width != current_size or pil_img.height != current_size:
                         display_img = pil_img.resize((current_size, current_size), Image.Resampling.LANCZOS)
                    else:
                         display_img = pil_img
                         
                    photo = ImageTk.PhotoImage(display_img)
                    
                    # 必须保存引用到 canvas_widget
                    self.canvas_widget.sticker_photo_refs.append(photo)
                    
                    sticker_id = self.canvas_widget.canvas.create_image(
                        sticker_data['x'], sticker_data['y'],
                        image=photo,
                        anchor='center', # 贴纸默认居中
                        tags='sticker',
                        state='normal' if visible else 'hidden'
                    )
                    
                    self.canvas_widget.stickers.append({
                        'id': sticker_id,
                        'text': '',
                        'x': sticker_data['x'],
                        'y': sticker_data['y'],
                        'size': sticker_data['size'],
                        'is_image': True,
                        'image': pil_img, # 保持原始图片引用
                        'visible': visible,
                        'category': sticker_data.get('category'),
                        'image_path': sticker_data.get('image_path')
                    })
                    
                else:
                    # 恢复文本贴纸 (Emoji)
                    sticker_id = self.canvas_widget.canvas.create_text(
                        sticker_data['x'], sticker_data['y'],
                        text=sticker_data['text'],
                        font=('Arial', sticker_data['size']),
                        fill='black',
                        tags='sticker',
                        state='normal' if visible else 'hidden'
                    )
                    self.canvas_widget.stickers.append({
                        'id': sticker_id,
                        'text': sticker_data['text'],
                        'x': sticker_data['x'],
                        'y': sticker_data['y'],
                        'size': sticker_data['size'],
                        'is_image': False,
                        'visible': visible
                    })
        
        # 刷新画布
        self.refresh_canvas()
        
        # 恢复文字配置
        if 'text_config' in state:
            tc = state['text_config']
            
            # 恢复UI变量
            if hasattr(self, 'text_content_entry'):
                self.text_content_entry.delete('1.0', tk.END)
                self.text_content_entry.insert('1.0', tc.get('content', ''))
                
            if hasattr(self, 'text_color_var'): self.text_color_var.set(tc.get('color', '#333333'))
            if hasattr(self, 'font_family_var'): self.font_family_var.set(tc.get('font_family', ''))
            if hasattr(self, 'font_size_scale'): self.font_size_scale.set(tc.get('font_size', 48))
            if hasattr(self, 'text_align_var'): self.text_align_var.set(tc.get('align', 'center'))
            if hasattr(self, 'text_position_var'): self.text_position_var.set(tc.get('position', 'bottom'))
            if hasattr(self, 'text_margin_var'): self.text_margin_var.set(tc.get('margin', 20))
            if hasattr(self, 'text_bold_var'): self.text_bold_var.set(tc.get('bold', False))
            if hasattr(self, 'text_italic_var'): self.text_italic_var.set(tc.get('italic', False))
            if hasattr(self, 'text_underline_var'): self.text_underline_var.set(tc.get('underline', False))
            if hasattr(self, 'text_shadow_var'): self.text_shadow_var.set(tc.get('shadow_enabled', False))
            if hasattr(self, 'text_stroke_var'): self.text_stroke_var.set(tc.get('stroke_enabled', False))
            if hasattr(self, 'stroke_width_var'): self.stroke_width_var.set(tc.get('stroke_width', 2))
            if hasattr(self, 'stroke_color_var'): self.stroke_color_var.set(tc.get('stroke_color', '#000000'))
            if hasattr(self, 'highlight_enabled_var'): self.highlight_enabled_var.set(tc.get('highlight_enabled', True))
            
            # 触发重新渲染文字
            self._auto_apply_text()
    
    def restore_to_history(self, index):
        """恢复到指定历史记录"""
        if 0 <= index < len(self.history_stack):
            self.history_index = index
            self.restore_state(self.history_stack[index])
            self.update_history_display()
    
    def update_history_display(self):
        """更新历史记录列表显示"""
        if not hasattr(self, 'history_listbox'):
            return
        
        self.history_listbox.delete(0, tk.END)
        for i, state in enumerate(self.history_stack):
            prefix = "▶ " if i == self.history_index else "  "
            self.history_listbox.insert(tk.END, f"{prefix}{state['timestamp']} - {state['action']}")
    
    def create_history_tab(self, parent):
        """历史记录标签页"""
        # 标题
        tk.Label(
            parent, text='📝 操作记录', font=('SF Pro Display', 14, 'bold'),
            bg=COLORS['panel_bg'], fg=COLORS['text_primary'], anchor='w'
        ).pack(fill=tk.X, padx=16, pady=(16, 8))
        
        # 撤销/重做按钮区
        btn_frame = tk.Frame(parent, bg=COLORS['panel_bg'])
        btn_frame.pack(fill=tk.X, padx=16, pady=(0, 12))
        
        undo_btn = tk.Label(
            btn_frame, text='↶ 撤销', font=('SF Pro Text', 10),
            bg=COLORS['bg_tertiary'], fg=COLORS['text_primary'],
            padx=12, pady=6, cursor='hand2'
        )
        undo_btn.pack(side=tk.LEFT, padx=(0, 4))
        undo_btn.bind('<Button-1>', lambda e: self.undo())
        undo_btn.bind('<Enter>', lambda e: undo_btn.config(bg=COLORS['hover']))
        undo_btn.bind('<Leave>', lambda e: undo_btn.config(bg=COLORS['bg_tertiary']))
        
        redo_btn = tk.Label(
            btn_frame, text='↷ 重做', font=('SF Pro Text', 10),
            bg=COLORS['bg_tertiary'], fg=COLORS['text_primary'],
            padx=12, pady=6, cursor='hand2'
        )
        redo_btn.pack(side=tk.LEFT)
        redo_btn.bind('<Button-1>', lambda e: self.redo())
        redo_btn.bind('<Enter>', lambda e: redo_btn.config(bg=COLORS['hover']))
        redo_btn.bind('<Leave>', lambda e: redo_btn.config(bg=COLORS['bg_tertiary']))
        
        clear_btn = tk.Label(
            btn_frame, text='清空', font=('SF Pro Text', 10),
            bg=COLORS['bg_tertiary'], fg=COLORS['text_secondary'],
            padx=12, pady=6, cursor='hand2'
        )
        clear_btn.pack(side=tk.RIGHT)
        clear_btn.bind('<Button-1>', lambda e: self.clear_history())
        clear_btn.bind('<Enter>', lambda e: clear_btn.config(bg=COLORS['hover']))
        clear_btn.bind('<Leave>', lambda e: clear_btn.config(bg=COLORS['bg_tertiary']))
        
        # 说明文字
        tk.Label(
            parent, text='点击记录可恢复到该状态', font=('SF Pro Text', 10),
            bg=COLORS['panel_bg'], fg=COLORS['text_secondary'], anchor='w'
        ).pack(fill=tk.X, padx=16, pady=(0, 8))
        
        # 历史记录列表
        list_frame = tk.Frame(parent, bg=COLORS['bg_tertiary'], relief=tk.FLAT)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 16))
        
        self.history_listbox = tk.Listbox(
            list_frame, font=('SF Pro Text', 10),
            bg=COLORS['bg_tertiary'], fg=COLORS['text_primary'],
            selectbackground=COLORS['accent'], selectforeground='white',
            relief=tk.FLAT, borderwidth=0, highlightthickness=0,
            activestyle='none'
        )
        self.history_listbox.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        
        # 绑定点击事件
        self.history_listbox.bind('<ButtonRelease-1>', self.on_history_select)
        
        # 滚动条
        scrollbar = tk.Scrollbar(list_frame, command=self.history_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.history_listbox.config(yscrollcommand=scrollbar.set)
        
        # 初始化显示
        self.update_history_display()
    
    def on_history_select(self, event):
        """历史记录选择事件"""
        selection = self.history_listbox.curselection()
        if selection:
            index = selection[0]
            self.restore_to_history(index)
    
    def clear_history(self):
        """清空历史记录"""
        if messagebox.askyesno('确认', '确定要清空所有历史记录吗？'):
            self.history_stack = []
            self.history_index = -1
            self.update_history_display()
            
    def create_layer_tab(self, parent):
        """图层标签页"""
        # 标题栏
        header = tk.Frame(parent, bg=COLORS['panel_bg'])
        header.pack(fill=tk.X, padx=16, pady=(16, 8))
        
        tk.Label(
            header, text='📚 图层管理', font=('SF Pro Display', 14, 'bold'),
            bg=COLORS['panel_bg'], fg=COLORS['text_primary'], anchor='w'
        ).pack(side=tk.LEFT)
        
        # 刷新按钮
        refresh_btn = tk.Label(
            header, text='⟳', font=('SF Pro Text', 14),
            bg=COLORS['panel_bg'], fg=COLORS['text_secondary'],
            cursor='hand2'
        )
        refresh_btn.pack(side=tk.RIGHT)
        refresh_btn.bind('<Button-1>', lambda e: self.update_layer_list())
        
        # 图层列表容器
        list_frame = tk.Frame(parent, bg=COLORS['bg_tertiary'], relief=tk.FLAT)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 16))
        
        # 自定义列表显示
        self.layer_list_frame = tk.Frame(list_frame, bg=COLORS['bg_tertiary'])
        self.layer_list_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # 初始化右键菜单 (增强版)
        self.layer_context_menu = tk.Menu(self, tearoff=0)
        self.layer_context_menu.add_command(label="⬆️ 上移一层", command=self.move_layer_up)
        self.layer_context_menu.add_command(label="⬇️ 下移一层", command=self.move_layer_down)
        self.layer_context_menu.add_command(label="⏫ 置顶", command=self.move_layer_to_top)
        self.layer_context_menu.add_command(label="⏬ 置底", command=self.move_layer_to_bottom)
        self.layer_context_menu.add_separator()
        self.layer_context_menu.add_command(label="👁️ 显示/隐藏", command=self.toggle_layer_visibility)
        self.layer_context_menu.add_separator()
        self.layer_context_menu.add_command(label="🗑️ 删除", command=self.delete_layer_item)
        
        # 添加键盘 Delete/BackSpace 绑定
        self.bind('<Delete>', self._on_delete_key)
        self.bind('<BackSpace>', self._on_delete_key)
        
        # 初始加载
        self.update_layer_list()

    def update_layer_list(self):
        """更新图层列表显示"""
        if not hasattr(self, 'layer_list_frame'):
            return
            
        # 清空现有列表和缩略图引用
        if hasattr(self, '_layer_thumb_refs'):
            self._layer_thumb_refs.clear()
        for widget in self.layer_list_frame.winfo_children():
            widget.destroy()
            
        # 获取所有图层项 (从上到下: 边框 -> 贴纸(反序) -> 文字 -> 主图 -> 背景图案)
        layers = []
        
        # 1. 边框 (如果存在或隐藏中)
        if self.border_config.get('width', 0) > 0 or getattr(self, '_temp_hidden_border_width', None):
            is_visible = not getattr(self, '_temp_hidden_border_width', None)
            layers.append({'type': 'border', 'name': '🖼️ 边框', 'id': 'border', 'visible': is_visible})
            
        # 2. 贴纸 (反序)
        if hasattr(self.canvas_widget, 'stickers'):
            for i, sticker in enumerate(reversed(self.canvas_widget.stickers)):
                # 获取贴纸显示名称
                sticker_text = sticker.get('text', '')
                if sticker_text:
                    # Emoji 贴纸 - 只显示 emoji 字符作为名称
                    layer_name = f'✨ {sticker_text[:3]}'  # 最多3个emoji
                elif sticker.get('is_image'):
                    # PNG 图片贴纸 - 统一显示
                    layer_name = '🎨 贴纸'
                else:
                    layer_name = '✨ 贴纸'
                    
                is_visible = sticker.get('visible', True)
                layers.append({
                    'type': 'sticker', 
                    'name': layer_name, 
                    'id': sticker['id'],
                    'index': len(self.canvas_widget.stickers) - 1 - i,
                    'visible': is_visible,
                    'sticker_data': sticker  # 保存贴纸数据引用用于预览
                })
        
        # 3. 文字层 (如果存在)
        if self.text_layers and len(self.text_layers) > 0:
            for idx, text_layer in enumerate(self.text_layers):
                content = text_layer.content[:10] + ('...' if len(text_layer.content) > 10 else '')
                # 文字层没有简单的可见性控制，默认显示
                layers.append({
                    'type': 'text',
                    'name': f'🔤 文字: {content}' if content else '🔤 文字',
                    'id': f'text_{idx}',
                    'index': idx,
                    'visible': True
                })
                
        # 4. 主图片
        if self.image_processor.current_image:
            try:
                is_visible = self.canvas_widget.canvas.itemcget('main_image', 'state') != 'hidden'
            except:
                is_visible = True
            layers.append({'type': 'image', 'name': '📷 主图片', 'id': 'main_image', 'visible': is_visible})
            
        # [REMOVED] 5. 背景图案 (用户请求不显示在图层列表中)
        # if hasattr(self, 'background_pattern') and self.background_pattern and self.background_pattern != 'none':
        #     try:
        #         is_visible = self.canvas_widget.canvas.itemcget('background_pattern', 'state') != 'hidden'
        #     except:
        #         is_visible = True
        #     layers.append({'type': 'background_pattern', 'name': '✦ 背景图案', 'id': 'background_pattern', 'visible': is_visible})
        
        # 渲染列表
        for idx, layer in enumerate(layers):
            item_frame = tk.Frame(self.layer_list_frame, bg=COLORS['bg_tertiary'])
            item_frame.pack(fill=tk.X, pady=1)
            
            # 序号
            seq_label = tk.Label(
                item_frame, text=f'{idx + 1}', font=('SF Pro Text', 9),
                bg=COLORS['bg_tertiary'], fg=COLORS['text_tertiary'],
                width=2
            )
            seq_label.pack(side=tk.LEFT)
            
            # 可见性按钮 (眼睛图标)
            eye_icon = "👁️" if layer['visible'] else "⭕" # 使用圈圈代表闭眼/隐藏，或可用 🔒
            eye_label = tk.Label(
                item_frame, text=eye_icon, font=('SF Pro Text', 10),
                bg=COLORS['bg_tertiary'], fg=COLORS['text_secondary'] if layer['visible'] else COLORS['text_tertiary'],
                width=3, cursor='hand2'
            )
            eye_label.pack(side=tk.LEFT, fill=tk.Y)
            
            # 缩略图预览 (仅贴纸/图片)
            thumb_label = None
            if layer['type'] == 'sticker' and layer.get('sticker_data'):
                sticker_data = layer['sticker_data']
                # 尝试生成缩略图
                try:
                    if sticker_data.get('is_image') and sticker_data.get('image'):
                        # PNG 图片贴纸 - 缩放到24x24
                        from PIL import Image
                        thumb_size = (24, 24)
                        original = sticker_data['image']
                        thumb_img = original.copy()
                        thumb_img.thumbnail(thumb_size, Image.Resampling.LANCZOS)
                        # 创建带透明背景的方形缩略图
                        canvas_thumb = Image.new('RGBA', thumb_size, (0,0,0,0))
                        paste_x = (thumb_size[0] - thumb_img.width) // 2
                        paste_y = (thumb_size[1] - thumb_img.height) // 2
                        canvas_thumb.paste(thumb_img, (paste_x, paste_y))
                        thumb_photo = ImageTk.PhotoImage(canvas_thumb)
                        # 保持引用避免被GC
                        if not hasattr(self, '_layer_thumb_refs'):
                            self._layer_thumb_refs = []
                        self._layer_thumb_refs.append(thumb_photo)
                        thumb_label = tk.Label(item_frame, image=thumb_photo, bg=COLORS['bg_tertiary'])
                        thumb_label.pack(side=tk.LEFT, padx=2)
                except Exception as e:
                    pass  # 缩略图生成失败时不显示
            
            name_label = tk.Label(
                item_frame, text=layer['name'], font=('SF Pro Text', 10),
                bg=COLORS['bg_tertiary'], fg=COLORS['text_primary'],
                anchor='w', padx=8, pady=6
            )
            name_label.pack(fill=tk.X, side=tk.LEFT, expand=True)
            
            # 拖放手柄 (仅贴纸)
            drag_handle = None
            if layer['type'] == 'sticker':
                drag_handle = tk.Label(
                    item_frame, text='≡', font=('SF Pro Text', 14),
                    bg=COLORS['bg_tertiary'], fg=COLORS['text_tertiary'],
                    width=2, cursor='fleur'  # fleur = 移动光标
                )
                drag_handle.pack(side=tk.RIGHT)
            
            # 绑定可见性切换
            # 更新toggle_layer_visibility以接受上下文参数，或者我们在点击时设置context_layer
            def on_eye_click(e, l=layer):
                self.context_layer = l
                self.toggle_layer_visibility()
                
            eye_label.bind('<Button-1>', on_eye_click)
            
            # 事件绑定
            handler = lambda e, l=layer, f=item_frame: self.on_layer_select(l, f)
            name_label.bind('<Button-1>', handler)
            item_frame.bind('<Button-1>', handler)
            
            # 右键菜单
            ctx_handler = lambda e, l=layer: self.show_layer_context_menu(e, l)
            name_label.bind('<Button-2>', ctx_handler)
            name_label.bind('<Button-3>', ctx_handler)
            name_label.bind('<Control-Button-1>', ctx_handler)
            item_frame.bind('<Button-2>', ctx_handler)
            item_frame.bind('<Button-3>', ctx_handler)
            item_frame.bind('<Control-Button-1>', ctx_handler)
            # 缩略图也绑定右键菜单
            if thumb_label:
                thumb_label.bind('<Button-1>', handler)
                thumb_label.bind('<Button-2>', ctx_handler)
                thumb_label.bind('<Button-3>', ctx_handler)
                thumb_label.bind('<Control-Button-1>', ctx_handler)

            # Hover
            def on_enter(e, f=item_frame, l=name_label, el=eye_label, lid=layer.get('id')):
                if getattr(self, 'selected_layer_id', None) != lid:
                    col = COLORS['hover']
                    f.config(bg=col)
                    l.config(bg=col)
                    el.config(bg=col)
            
            def on_leave(e, f=item_frame, l=name_label, el=eye_label, lid=layer.get('id')):
                if getattr(self, 'selected_layer_id', None) != lid:
                    col = COLORS['bg_tertiary']
                    f.config(bg=col)
                    l.config(bg=col)
                    el.config(bg=col)
            
            name_label.bind('<Enter>', on_enter)
            name_label.bind('<Leave>', on_leave)
            eye_label.bind('<Enter>', on_enter)
            eye_label.bind('<Leave>', on_leave)
            item_frame.bind('<Enter>', on_enter)
            item_frame.bind('<Leave>', on_leave)
            
            # 拖放功能 (仅贴纸支持)
            if layer['type'] == 'sticker':
                def on_drag_start(e, l=layer, f=item_frame, dh=drag_handle, nl=name_label):
                    self._drag_layer = l
                    self._drag_start_y = e.y_root
                    self._drag_start_x = e.x_root
                    self._drag_source_frame = f
                    self._drag_valid_drop = False
                    
                    # 创建幽灵窗口 (跟随鼠标)
                    self._drag_ghost = tk.Toplevel(self)
                    self._drag_ghost.overrideredirect(True)  # 无边框
                    self._drag_ghost.attributes('-alpha', 0.8)  # 半透明
                    self._drag_ghost.config(bg=COLORS['warning'])
                    
                    ghost_label = tk.Label(
                        self._drag_ghost, text=nl.cget('text'),
                        font=('SF Pro Text', 10), bg=COLORS['warning'],
                        fg='white', padx=10, pady=5
                    )
                    ghost_label.pack()
                    
                    # 放置在鼠标位置
                    self._drag_ghost.geometry(f'+{e.x_root + 10}+{e.y_root - 10}')
                    
                    # 高亮源图层
                    f.config(bg=COLORS['text_tertiary'])
                    for child in f.winfo_children():
                        try:
                            child.config(bg=COLORS['text_tertiary'])
                        except:
                            pass
                
                def on_drag_motion(e, f=item_frame):
                    if not hasattr(self, '_drag_layer') or not self._drag_layer:
                        return
                    
                    # 移动幽灵窗口
                    if hasattr(self, '_drag_ghost') and self._drag_ghost:
                        self._drag_ghost.geometry(f'+{e.x_root + 10}+{e.y_root - 10}')
                    
                    drop_y = e.y_root
                    found_valid = False
                    
                    # 清除之前的drop target高亮
                    for widget in self.layer_list_frame.winfo_children():
                        if widget != getattr(self, '_drag_source_frame', None):
                            widget.config(bg=COLORS['bg_tertiary'])
                            for child in widget.winfo_children():
                                try:
                                    child.config(bg=COLORS['bg_tertiary'])
                                except:
                                    pass
                    
                    # 检查drop target
                    for widget in self.layer_list_frame.winfo_children():
                        if widget == getattr(self, '_drag_source_frame', None):
                            continue
                        widget_y = widget.winfo_rooty()
                        widget_h = widget.winfo_height()
                        if widget_y <= drop_y <= widget_y + widget_h:
                            # 检查是否是有效目标 (贴纸)
                            is_valid = False
                            for child in widget.winfo_children():
                                try:
                                    text = child.cget('text')
                                    if '贴纸' in text:
                                        is_valid = True
                                        break
                                except:
                                    pass
                            
                            if is_valid:
                                # 有效目标：蓝色
                                widget.config(bg=COLORS['accent'])
                                for child in widget.winfo_children():
                                    try:
                                        child.config(bg=COLORS['accent'])
                                    except:
                                        pass
                                found_valid = True
                            else:
                                # 无效目标：红色
                                widget.config(bg=COLORS['danger'])
                                for child in widget.winfo_children():
                                    try:
                                        child.config(bg=COLORS['danger'])
                                    except:
                                        pass
                            break
                    
                    self._drag_valid_drop = found_valid
                
                def on_drag_end(e, l=layer):
                    # 销毁幽灵窗口
                    if hasattr(self, '_drag_ghost') and self._drag_ghost:
                        self._drag_ghost.destroy()
                        self._drag_ghost = None
                    
                    if not hasattr(self, '_drag_layer') or not self._drag_layer:
                        return
                    
                    # 计算放置位置
                    drop_y = e.y_root
                    drop_index = None
                    is_valid_target = False
                    
                    for widget in self.layer_list_frame.winfo_children():
                        widget_y = widget.winfo_rooty()
                        widget_h = widget.winfo_height()
                        if widget_y <= drop_y <= widget_y + widget_h:
                            for child in widget.winfo_children():
                                try:
                                    text = child.cget('text')
                                    if '贴纸' in text:
                                        drop_index = list(self.layer_list_frame.winfo_children()).index(widget)
                                        is_valid_target = True
                                        break
                                except:
                                    pass
                            break
                    
                    if is_valid_target and drop_index is not None:
                        src_idx = self._drag_layer.get('index')
                        if src_idx is not None:
                            self._reorder_stickers_by_drop(src_idx, drop_index)
                    else:
                        # 无效放置：显示提示
                        self.show_toast('只能在贴纸之间拖放')
                    
                    self._drag_layer = None
                    self._drag_source_frame = None
                    self._drag_valid_drop = False
                    self.update_layer_list()
                
                # 绑定拖放事件到拖放手柄
                if drag_handle:
                    drag_handle.bind('<Button-1>', on_drag_start)
                    drag_handle.bind('<B1-Motion>', on_drag_motion)
                    drag_handle.bind('<ButtonRelease-1>', on_drag_end)

    def on_layer_select(self, layer, item_frame):
        """图层选中处理"""
        self.selected_layer = layer
        self.selected_layer_id = layer.get('id')
        
        for widget in self.layer_list_frame.winfo_children():
            widget.config(bg=COLORS['bg_tertiary'])
            for child in widget.winfo_children():
                child.config(bg=COLORS['bg_tertiary'])
        
        item_frame.config(bg=COLORS['accent'])
        for child in item_frame.winfo_children():
            child.config(bg=COLORS['accent'])
            
        if layer['type'] == 'sticker':
            # 选中贴纸并显示缩放手柄
            self.canvas_widget.selected_item = layer['id']
            self.canvas_widget._create_scaling_handles(layer['id'])
        else:
            self.canvas_widget.selected_item = None
            self.canvas_widget.canvas.delete('handle')
            
    def show_layer_context_menu(self, event, layer):
        """显示图层右键菜单"""
        self.on_layer_select(layer, event.widget.master)
        self.context_layer = layer
        
        # 根据图层类型启用/禁用菜单项
        ltype = layer['type']
        can_reorder = ltype == 'sticker'  # 只有贴纸支持排序
        can_delete = ltype in ['sticker', 'image']
        
        self.layer_context_menu.entryconfig("⬆️ 上移一层", state=tk.NORMAL if can_reorder else tk.DISABLED)
        self.layer_context_menu.entryconfig("⬇️ 下移一层", state=tk.NORMAL if can_reorder else tk.DISABLED)
        self.layer_context_menu.entryconfig("⏫ 置顶", state=tk.NORMAL if can_reorder else tk.DISABLED)
        self.layer_context_menu.entryconfig("⏬ 置底", state=tk.NORMAL if can_reorder else tk.DISABLED)
        self.layer_context_menu.entryconfig("🗑️ 删除", state=tk.NORMAL if can_delete else tk.DISABLED)
        
        # 确保菜单可以重复显示
        try:
            self.layer_context_menu.unpost()  # 先关闭旧菜单
        except:
            pass
        self.layer_context_menu.post(event.x_root, event.y_root)
        # 设置焦点以便点击其他地方可以关闭菜单
        self.layer_context_menu.focus_set()
        
    def toggle_layer_visibility(self):
        """切换图层可见性"""
        if not hasattr(self, 'context_layer'): return
        ltype = self.context_layer['type']
        
        if ltype == 'sticker':
            iid = self.context_layer['id']
            curr = self.canvas_widget.canvas.itemcget(iid, 'state')
            new_state = 'hidden' if curr!='hidden' else 'normal'
            self.canvas_widget.canvas.itemconfigure(iid, state=new_state)
            
            # 更新数据中的可见性状态
            for sticker in self.canvas_widget.stickers:
                if sticker['id'] == iid:
                    sticker['visible'] = (new_state == 'normal')
                    break
            self.save_history("切换图层可见性")
            
        elif ltype == 'image':
            try:
                iid = 'main_image'
                curr = self.canvas_widget.canvas.itemcget(iid, 'state')
                new_state = 'hidden' if curr!='hidden' else 'normal'
                self.canvas_widget.canvas.itemconfigure(iid, state=new_state)
            except:
                self.show_toast('无法切换：没有主图片')
            
        elif ltype == 'border':
            # 简单切换边框宽度
            if self.border_config.get('width', 0) > 0:
                self._temp_hidden_border_width = self.border_config.get('width')
                self.border_config['width'] = 0
            elif getattr(self, '_temp_hidden_border_width', None):
                self.border_config['width'] = self._temp_hidden_border_width
                self._temp_hidden_border_width = None
            self.refresh_canvas()
        
        elif ltype == 'text':
            # 文字层暂不支持单独隐藏，提示用户
            self.show_toast('文字层暂不支持隐藏，请清除文字')
            
        elif ltype == 'background_pattern':
            try:
                # 切换背景图案的可见性
                items = self.canvas_widget.canvas.find_withtag('background_pattern')
                if items:
                    curr = self.canvas_widget.canvas.itemcget(items[0], 'state')
                    new_state = 'hidden' if curr != 'hidden' else 'normal'
                    for item in items:
                        self.canvas_widget.canvas.itemconfigure(item, state=new_state)
            except Exception as e:
                print(f"[DEBUG] Toggle background pattern error: {e}")
            
        # 刷新列表显示状态
        self.update_layer_list()
            
    def delete_layer_item(self):
        """删除图层项"""
        if not hasattr(self, 'context_layer'): return
        ltype = self.context_layer['type']
        
        if ltype == 'sticker':
            # 需要在 canvas_widget 中实现根据 ID 删除
            # 目前只有 delete_selected_sticker (删除选中的)
            # 既然我们已经选宏了它 (on_layer_select), delete_selected_sticker 应该有效
            self.canvas_widget.delete_selected_sticker()
            self.update_layer_list()
            self.save_history("删除贴纸")
        elif ltype == 'image':
            if messagebox.askyesno("确认", "确定要清除主图片吗？"):
                self.image_processor.current_image = None
                self.refresh_canvas()
                self.update_layer_list()
                self.save_history("删除图片")
    
    def _on_delete_key(self, event=None):
        """处理键盘 Delete/BackSpace 键删除选中图层"""
        # 如果焦点在文本输入框中，不处理删除键
        focused = self.focus_get()
        if focused and (isinstance(focused, tk.Entry) or isinstance(focused, tk.Text)):
            return  # 让输入框正常处理删除键
        
        # 先检查画布上选中的项目
        if hasattr(self.canvas_widget, 'selected_item') and self.canvas_widget.selected_item:
            tags = self.canvas_widget.canvas.gettags(self.canvas_widget.selected_item)
            if 'sticker' in tags:
                self.canvas_widget.delete_selected_sticker()
                self.update_layer_list()
                self.save_history("删除贴纸")
                return
        
        # 再检查图层列表选中的项目
        if hasattr(self, 'selected_layer_id') and self.selected_layer_id:
            # 找到对应的图层
            for layer in self.get_layer_list():
                if layer.get('id') == self.selected_layer_id:
                    self.context_layer = layer
                    self.delete_layer_item()
                    return
    
    def move_layer_up(self):
        """将图层上移一层"""
        if not hasattr(self, 'context_layer'): return
        ltype = self.context_layer['type']
        
        if ltype == 'sticker':
            idx = self.context_layer.get('index')
            stickers = self.canvas_widget.stickers
            if idx is not None and idx < len(stickers) - 1:
                stickers[idx], stickers[idx + 1] = stickers[idx + 1], stickers[idx]
                self._rebuild_sticker_order()
                self.update_layer_list()
                self.save_history("上移图层")
        else:
            self.show_toast(f'{ltype} 图层顺序固定')
    
    def move_layer_down(self):
        """将图层下移一层"""
        if not hasattr(self, 'context_layer'): return
        ltype = self.context_layer['type']
        
        if ltype == 'sticker':
            idx = self.context_layer.get('index')
            stickers = self.canvas_widget.stickers
            if idx is not None and idx > 0:
                stickers[idx], stickers[idx - 1] = stickers[idx - 1], stickers[idx]
                self._rebuild_sticker_order()
                self.update_layer_list()
                self.save_history("下移图层")
        else:
            self.show_toast(f'{ltype} 图层顺序固定')
    
    def move_layer_to_top(self):
        """将图层置顶"""
        if not hasattr(self, 'context_layer'): return
        ltype = self.context_layer['type']
        
        if ltype == 'sticker':
            idx = self.context_layer.get('index')
            stickers = self.canvas_widget.stickers
            if idx is not None and idx < len(stickers) - 1:
                sticker = stickers.pop(idx)
                stickers.append(sticker)
                self._rebuild_sticker_order()
                self.update_layer_list()
                self.save_history("图层置顶")
        else:
            self.show_toast(f'{ltype} 图层顺序固定')
    
    def move_layer_to_bottom(self):
        """将图层置底"""
        if not hasattr(self, 'context_layer'): return
        ltype = self.context_layer['type']
        
        if ltype == 'sticker':
            idx = self.context_layer.get('index')
            stickers = self.canvas_widget.stickers
            if idx is not None and idx > 0:
                sticker = stickers.pop(idx)
                stickers.insert(0, sticker)
                self._rebuild_sticker_order()
                self.update_layer_list()
                self.save_history("图层置底")
        else:
            self.show_toast(f'{ltype} 图层顺序固定')
    
    def _rebuild_sticker_order(self):
        """重新排序画布上的贴纸图层 (根据 stickers 数组顺序)"""
        for sticker in self.canvas_widget.stickers:
            self.canvas_widget.canvas.tag_raise(sticker['id'])
        self.canvas_widget._ensure_layer_order()
    
    def _reorder_stickers_by_drop(self, src_sticker_idx, drop_widget_idx):
        """通过拖放重新排序贴纸"""
        stickers = self.canvas_widget.stickers
        
        # 计算目标贴纸索引 (drop_widget_idx 是列表中的位置，需要转换)
        # 图层列表中贴纸是反序显示的，所以需要调整
        num_stickers = len(stickers)
        
        # 边框占1个位置 (如果存在)
        border_offset = 1 if (self.border_config.get('width', 0) > 0 or getattr(self, '_temp_hidden_border_width', None)) else 0
        
        # 目标索引 = num_stickers - 1 - (drop_widget_idx - border_offset)
        target_idx = num_stickers - 1 - (drop_widget_idx - border_offset)
        target_idx = max(0, min(num_stickers - 1, target_idx))
        
        if src_sticker_idx == target_idx or src_sticker_idx < 0 or src_sticker_idx >= num_stickers:
            return
        
        # 移动贴纸
        sticker = stickers.pop(src_sticker_idx)
        stickers.insert(target_idx, sticker)
        
        self._rebuild_sticker_order()
        self.save_history("拖放排序图层")
    
    def create_background_tab(self, parent):
        """背景/主题标签页"""
        # 创建滚动区域
        scroll_canvas = tk.Canvas(parent, bg=COLORS['panel_bg'], highlightthickness=0)
        scrollbar = tk.Scrollbar(parent, orient='vertical', command=scroll_canvas.yview)
        scroll_frame = tk.Frame(scroll_canvas, bg=COLORS['panel_bg'])
        
        scroll_frame.bind('<Configure>', lambda e: scroll_canvas.configure(scrollregion=scroll_canvas.bbox('all')))
        scroll_canvas.create_window((0, 0), window=scroll_frame, anchor='nw')
        scroll_canvas.configure(yscrollcommand=scrollbar.set)
        
        # 自定义颜色标题(预设主题已移到左侧面板)
        tk.Label(
            scroll_frame, text='🌈 自定义颜色', font=('SF Pro Display', 14, 'bold'),
            bg=COLORS['panel_bg'], fg=COLORS['text_primary'], anchor='w'
        ).pack(fill=tk.X, padx=16, pady=(0, 12))
        
        # 自定义颜色区域 - 新布局
        custom_color_container = tk.Frame(scroll_frame, bg=COLORS['panel_bg'])
        custom_color_container.pack(fill=tk.X, padx=16, pady=(0, 16))
        
        # 1. 预览
        self.bg_color_preview = tk.Canvas(
            custom_color_container, width=60, height=60,
            bg=self.background_color, highlightthickness=2,
            highlightbackground=COLORS['separator']
        )
        self.bg_color_preview.pack(side=tk.LEFT, padx=(0, 12))
        self.bg_color_preview.bind('<Button-1>', lambda e: self.choose_background_color())
        self.bg_color_preview.config(cursor='hand2')
        
        # 2. 信息
        info_frame = tk.Frame(custom_color_container, bg=COLORS['panel_bg'])
        info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.bg_color_hex_label = tk.Label(
            info_frame, text=self.background_color, font=('SF Mono', 14, 'bold'),
            bg=COLORS['panel_bg'], fg=COLORS['text_primary']
        )
        self.bg_color_hex_label.pack(anchor='w')
        
        tk.Label(
            info_frame, text='点击预览或按钮选择', font=('SF Pro Text', 10),
            bg=COLORS['panel_bg'], fg=COLORS['text_secondary']
        ).pack(anchor='w', pady=(2, 0))
        
        # 3. 按钮 (放在右侧，小一点)
        bg_choose_btn = tk.Label(
            custom_color_container, text='🎯 选择',
            bg=COLORS['accent'], fg='white', font=('SF Pro Text', 11),
            padx=10, pady=6, cursor='hand2'
        )
        bg_choose_btn.pack(side=tk.RIGHT, padx=(8, 0))
        bg_choose_btn.bind('<Button-1>', lambda e: self.choose_background_color())
        def make_hover(b):
            b.bind('<Enter>', lambda e: b.config(bg=COLORS['accent_hover']))
            b.bind('<Leave>', lambda e: b.config(bg=COLORS['accent']))
        make_hover(bg_choose_btn)
        
        # 快速颜色选择
        quick_color_frame = tk.Frame(scroll_frame, bg=COLORS['panel_bg'])
        quick_color_frame.pack(fill=tk.X, padx=16, pady=(0, 16))
        
        # 使用Grid布局显示大量颜色
        for idx, color in enumerate(QUICK_COLORS):
            row = idx // 10  # 每行10个
            col = idx % 10
            
            color_btn = tk.Canvas(
                quick_color_frame, width=24, height=24,
                bg=color, highlightthickness=1,
                highlightbackground=COLORS['separator'], cursor='hand2'
            )
            color_btn.grid(row=row, column=col, padx=2, pady=2)
            color_btn.bind('<Button-1>', lambda e, c=color: self.set_background_color(c))
        
        # 分隔线
        tk.Frame(scroll_frame, height=1, bg=COLORS['separator']).pack(fill=tk.X, padx=16, pady=8)
        
        # 背景图案
        tk.Label(
            scroll_frame, text='✦ 背景图案', font=('SF Pro Display', 14, 'bold'),
            bg=COLORS['panel_bg'], fg=COLORS['text_primary'], anchor='w'
        ).pack(fill=tk.X, padx=16, pady=(12, 12))
        
        bg_pattern_grid = tk.Frame(scroll_frame, bg=COLORS['panel_bg'])
        bg_pattern_grid.pack(fill=tk.X, padx=16, pady=(0, 16))
        
        self.bg_pattern_buttons = {}
        for idx, pattern in enumerate(BACKGROUND_PATTERNS):
            is_selected = pattern['id'] == self.background_pattern
            btn = tk.Label(
                bg_pattern_grid, text=f"{pattern['icon']}\n{pattern['name']}",
                bg=COLORS['accent'] if is_selected else COLORS['bg_tertiary'],
                fg=COLORS['text_bright'] if is_selected else COLORS['text_primary'],
                font=('SF Pro Text', 10, 'bold') if is_selected else ('SF Pro Text', 10),
                width=6, pady=6, cursor='hand2'
            )
            btn.grid(row=idx // 3, column=idx % 3, padx=4, pady=4)
            btn.bind('<Button-1>', lambda e, p=pattern['id']: self.set_bg_pattern(p))
            self.bg_pattern_buttons[pattern['id']] = btn
        
        # 图案颜色和大小
        pattern_config_frame = tk.Frame(scroll_frame, bg=COLORS['panel_bg'])
        pattern_config_frame.pack(fill=tk.X, padx=16, pady=(0, 16))
        
        # 图案颜色
        tk.Label(
            pattern_config_frame, text='图案颜色',
            font=('SF Pro Text', 11), bg=COLORS['panel_bg'], fg=COLORS['text_secondary']
        ).pack(anchor='w')
        
        pattern_color_row = tk.Frame(pattern_config_frame, bg=COLORS['panel_bg'])
        pattern_color_row.pack(fill=tk.X, pady=(4, 8))
        
        self.bg_pattern_color_canvas = tk.Canvas(
            pattern_color_row, width=40, height=40,
            bg=self.background_pattern_color, highlightthickness=1,
            highlightbackground=COLORS['separator'], cursor='hand2'
        )
        self.bg_pattern_color_canvas.pack(side=tk.LEFT, padx=(0, 8))
        self.bg_pattern_color_canvas.bind('<Button-1>', lambda e: self.choose_bg_pattern_color())
        
        # 图案大小滑块
        tk.Label(
            pattern_config_frame, text='图案大小',
            font=('SF Pro Text', 11), bg=COLORS['panel_bg'], fg=COLORS['text_secondary']
        ).pack(anchor='w')
        
        size_frame = tk.Frame(pattern_config_frame, bg=COLORS['panel_bg'])
        size_frame.pack(fill=tk.X, pady=(4, 0))
        
        self.bg_pattern_size_scale = tk.Scale(
            size_frame, from_=5, to=30, orient=tk.HORIZONTAL,
            command=self.on_bg_pattern_size_change, bg=COLORS['panel_bg'],
            highlightthickness=0, troughcolor=COLORS['separator'],
            activebackground=COLORS['accent'], length=150
        )
        self.bg_pattern_size_scale.set(self.background_pattern_size)
        self.bg_pattern_size_scale.pack(side=tk.LEFT)
        
        self.bg_pattern_size_label = tk.Label(
            size_frame, text=f'{self.background_pattern_size}px',
            font=('SF Mono', 10), bg=COLORS['panel_bg'], fg=COLORS['accent']
        )
        self.bg_pattern_size_label.pack(side=tk.LEFT, padx=(8, 0))
        
        # 绑定滚动 - 所有子控件创建完成后再绑定
        self.bind_mousewheel(scroll_canvas)
        self.bind_mousewheel(scroll_frame, scroll_canvas)
        
        scroll_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def create_border_tab(self, parent):
        """边框标签页 - 美观版"""
        # 创建滚动区域
        scroll_canvas = tk.Canvas(parent, bg=COLORS['panel_bg'], highlightthickness=0)
        scrollbar = tk.Scrollbar(parent, orient='vertical', command=scroll_canvas.yview)
        scroll_frame = tk.Frame(scroll_canvas, bg=COLORS['panel_bg'])
        
        scroll_frame.bind('<Configure>', lambda e: scroll_canvas.configure(scrollregion=scroll_canvas.bbox('all')))
        scroll_canvas.create_window((0, 0), window=scroll_frame, anchor='nw')
        scroll_canvas.configure(yscrollcommand=scrollbar.set)
        
        scroll_canvas.configure(yscrollcommand=scrollbar.set)
        
        # 1. 边框大小
        tk.Label(
            scroll_frame, text='📏 大小与圆角', font=('SF Pro Display', 14, 'bold'),
            bg=COLORS['panel_bg'], fg=COLORS['text_primary'], anchor='w'
        ).pack(fill=tk.X, padx=16, pady=(12, 12))
        
        size_frame = tk.Frame(scroll_frame, bg=COLORS['panel_bg'])
        size_frame.pack(fill=tk.X, padx=16, pady=(0, 16))
        
        # 宽度
        tk.Label(
            size_frame, text='宽度', font=('SF Pro Text', 11),
            bg=COLORS['panel_bg'], fg=COLORS['text_secondary']
        ).grid(row=0, column=0, sticky='w', pady=4)
        
        self.border_width_scale = tk.Scale(
            size_frame, from_=0, to=100, orient=tk.HORIZONTAL,
            command=self.on_border_width_change, bg=COLORS['panel_bg'],
            highlightthickness=0, troughcolor=COLORS['separator'],
            activebackground=COLORS['accent'], length=180
        )
        self.border_width_scale.set(self.border_config['width'])
        self.border_width_scale.grid(row=0, column=1, padx=8, sticky='ew')
        
        # 圆角
        tk.Label(
            size_frame, text='圆角', font=('SF Pro Text', 11),
            bg=COLORS['panel_bg'], fg=COLORS['text_secondary']
        ).grid(row=1, column=0, sticky='w', pady=12)
        
        self.border_radius_scale = tk.Scale(
            size_frame, from_=0, to=100, orient=tk.HORIZONTAL,
            command=self.on_border_radius_change, bg=COLORS['panel_bg'],
            highlightthickness=0, troughcolor=COLORS['separator'],
            activebackground=COLORS['accent'], length=180
        )
        self.border_radius_scale.set(self.border_config['radius'])
        self.border_radius_scale.grid(row=1, column=1, padx=8, sticky='ew')
        
        # 分隔线
        tk.Frame(scroll_frame, height=1, bg=COLORS['separator']).pack(fill=tk.X, padx=16, pady=8)
        
        # 3. 颜色
        tk.Label(
            scroll_frame, text='🎨 颜色', font=('SF Pro Display', 14, 'bold'),
            bg=COLORS['panel_bg'], fg=COLORS['text_primary'], anchor='w'
        ).pack(fill=tk.X, padx=16, pady=(12, 8))
        
        color_container = tk.Frame(scroll_frame, bg=COLORS['panel_bg'])
        color_container.pack(fill=tk.X, padx=16, pady=(0, 16))
        
        # 预览
        self.border_color_canvas = tk.Canvas(
            color_container, width=60, height=60,
            bg=self.border_config['color'], highlightthickness=2,
            highlightbackground=COLORS['separator'], cursor='hand2'
        )
        self.border_color_canvas.pack(side=tk.LEFT, padx=(0, 12))
        self.border_color_canvas.bind('<Button-1>', lambda e: self.choose_border_color())
        
        # 信息
        info_frame = tk.Frame(color_container, bg=COLORS['panel_bg'])
        info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.border_color_hex_label = tk.Label(
            info_frame, text=self.border_config['color'], 
            font=('SF Mono', 14, 'bold'),
            bg=COLORS['panel_bg'], fg=COLORS['accent']
        )
        self.border_color_hex_label.pack(anchor='w')
        
        tk.Label(
            info_frame, text='点击预览或按钮选择', font=('SF Pro Text', 10),
            bg=COLORS['panel_bg'], fg=COLORS['text_secondary']
        ).pack(anchor='w', pady=(2, 0))
        
        # 按钮
        border_color_btn = tk.Label(
            color_container, text='🎯 选择',
            bg=COLORS['bg_tertiary'], fg=COLORS['text_primary'], font=('SF Pro Text', 11),
            padx=10, pady=6, cursor='hand2'
        )
        border_color_btn.pack(side=tk.RIGHT, padx=(8,0))
        border_color_btn.bind('<Button-1>', lambda e: self.choose_border_color())
        def make_hover(b):
            b.bind('<Enter>', lambda e: b.config(bg=COLORS['hover']))
            b.bind('<Leave>', lambda e: b.config(bg=COLORS['bg_tertiary']))
        make_hover(border_color_btn)
        
        # 快速颜色选择
        quick_color_frame = tk.Frame(scroll_frame, bg=COLORS['panel_bg'])
        quick_color_frame.pack(fill=tk.X, padx=16, pady=(0, 16))
        
        quick_colors = QUICK_COLORS
        
        for idx, color in enumerate(quick_colors):
            row = idx // 10
            col = idx % 10
            
            color_btn = tk.Canvas(
                quick_color_frame, width=24, height=24,
                bg=color, highlightthickness=1,
                highlightbackground=COLORS['separator'], cursor='hand2'
            )
            color_btn.grid(row=row, column=col, padx=2, pady=2)
            color_btn.bind('<Button-1>', lambda e, c=color: self.set_border_color_quick(c))
        
        # 分隔线
        tk.Frame(scroll_frame, height=1, bg=COLORS['separator']).pack(fill=tk.X, padx=16, pady=8)
        
        # 5. 线条样式
        tk.Label(
            scroll_frame, text='〰 线条样式', font=('SF Pro Display', 13, 'bold'),
            bg=COLORS['panel_bg'], fg=COLORS['text_primary'], anchor='w'
        ).pack(fill=tk.X, padx=16, pady=(12, 8))
        
        line_style_grid = tk.Frame(scroll_frame, bg=COLORS['panel_bg'])
        line_style_grid.pack(fill=tk.X, padx=16, pady=(0, 16))
        
        self.line_style_buttons = {}
        for idx, style in enumerate(BORDER_LINE_STYLES):
            is_selected = style['id'] == self.border_config.get('line_style', 'solid')
            btn = tk.Label(
                line_style_grid, text=f"{style['icon']}\n{style['name']}",
                bg=COLORS['accent'] if is_selected else COLORS['bg_tertiary'],
                fg=COLORS['text_bright'] if is_selected else COLORS['text_primary'],
                font=('SF Pro Text', 10, 'bold') if is_selected else ('SF Pro Text', 10),
                width=6, pady=6, cursor='hand2'
            )
            btn.grid(row=0, column=idx, padx=4)
            btn.bind('<Button-1>', lambda e, s=style['id']: self.set_border_line_style(s))
            self.line_style_buttons[style['id']] = btn
        
        # 分隔线
        tk.Frame(scroll_frame, height=1, bg=COLORS['separator']).pack(fill=tk.X, padx=16, pady=8)
        
        # 6. 边框图案
        tk.Label(
            scroll_frame, text='✦ 边框图案', font=('SF Pro Display', 13, 'bold'),
            bg=COLORS['panel_bg'], fg=COLORS['text_primary'], anchor='w'
        ).pack(fill=tk.X, padx=16, pady=(12, 8))
        
        pattern_grid = tk.Frame(scroll_frame, bg=COLORS['panel_bg'])
        pattern_grid.pack(fill=tk.X, padx=16, pady=(0, 16))
        
        self.border_pattern_buttons = {}
        for idx, pattern in enumerate(BORDER_PATTERNS):
            is_selected = pattern['id'] == self.border_config.get('pattern', 'none')
            btn = tk.Label(
                pattern_grid, text=f"{pattern['icon']}\n{pattern['name']}",
                bg=COLORS['accent'] if is_selected else COLORS['bg_tertiary'],
                fg=COLORS['text_bright'] if is_selected else COLORS['text_primary'],
                font=('SF Pro Text', 10, 'bold') if is_selected else ('SF Pro Text', 10),
                width=6, pady=6, cursor='hand2'
            )
            
            # 两排布局 (每排5个)
            row = idx // 5
            col = idx % 5
            btn.grid(row=row, column=col, padx=4, pady=4)
            
            btn.bind('<Button-1>', lambda e, p=pattern['id']: self.set_border_pattern(p))
            self.border_pattern_buttons[pattern['id']] = btn
        
        # 分隔线
        tk.Frame(scroll_frame, height=1, bg=COLORS['separator']).pack(fill=tk.X, padx=16, pady=8)
        
        # 7. 操作按钮
        btn_frame = tk.Frame(scroll_frame, bg=COLORS['panel_bg'])
        btn_frame.pack(fill=tk.X, padx=16, pady=(12, 20))
        
        apply_btn = tk.Label(
            btn_frame, text='✓ 应用边框',
            bg=COLORS['accent'], fg='white', font=('SF Pro Text', 12, 'bold'),
            pady=10, cursor='hand2'
        )
        apply_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        apply_btn.bind('<Button-1>', lambda e: self.apply_custom_border())
        apply_btn.bind('<Enter>', lambda e: apply_btn.config(bg=COLORS['accent_hover']))
        apply_btn.bind('<Leave>', lambda e: apply_btn.config(bg=COLORS['accent']))
        
        clear_btn = tk.Label(
            btn_frame, text='✕ 清除边框',
            bg=COLORS['danger'], fg='white', font=('SF Pro Text', 12, 'bold'),
            pady=10, cursor='hand2'
        )
        clear_btn.pack(side=tk.LEFT, fill=tk.X, expand=True)
        clear_btn.bind('<Button-1>', lambda e: self.clear_border())
        clear_btn.bind('<Enter>', lambda e: clear_btn.config(bg='#FF6B6B'))
        clear_btn.bind('<Leave>', lambda e: clear_btn.config(bg=COLORS['danger']))
        
        # 绑定滚动 - 所有子控件创建完成后再绑定
        self.bind_mousewheel(scroll_canvas)
        self.bind_mousewheel(scroll_frame, scroll_canvas)
        
        scroll_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def update_border_preview(self):
        """更新边框预览"""
        if not hasattr(self, 'border_preview_canvas'):
            return
        
        canvas = self.border_preview_canvas
        canvas.delete('all')
        
        w, h = 200, 120
        shape = self.border_config['shape']
        width = min(self.border_config['width'], 10)  # 预览中限制粗细
        radius = min(self.border_config['radius'], 25)
        color = self.border_config['color']
        
        if width <= 0:
            return
        
        # 绘制边框预览
        if shape == 'rectangle':
            for i in range(width):
                canvas.create_rectangle(
                    10 + i, 10 + i, w - 10 - i, h - 10 - i,
                    outline=color
                )
        elif shape == 'rounded_rect':
            # 圆角矩形预览
            self.draw_preview_rounded_rect(canvas, 10, 10, w - 10, h - 10, radius, width, color)
        elif shape in ('circle', 'ellipse'):
            for i in range(width):
                canvas.create_oval(
                    10 + i, 10 + i, w - 10 - i, h - 10 - i,
                    outline=color
                )
    
    def draw_preview_rounded_rect(self, canvas, x1, y1, x2, y2, radius, width, color):
        """在预览画布上绘制圆角矩形"""
        r = min(radius, min(x2-x1, y2-y1) // 4)
        
        for i in range(width):
            cx1, cy1 = x1 + i, y1 + i
            cx2, cy2 = x2 - i, y2 - i
            
            if r <= 0:
                canvas.create_rectangle(cx1, cy1, cx2, cy2, outline=color)
                continue
            
            # 四条直线
            canvas.create_line(cx1 + r, cy1, cx2 - r, cy1, fill=color)
            canvas.create_line(cx1 + r, cy2, cx2 - r, cy2, fill=color)
            canvas.create_line(cx1, cy1 + r, cx1, cy2 - r, fill=color)
            canvas.create_line(cx2, cy1 + r, cx2, cy2 - r, fill=color)
            
            # 四个圆角
            canvas.create_arc(cx1, cy1, cx1 + 2*r, cy1 + 2*r, 
                            start=90, extent=90, style='arc', outline=color)
            canvas.create_arc(cx2 - 2*r, cy1, cx2, cy1 + 2*r, 
                            start=0, extent=90, style='arc', outline=color)
            canvas.create_arc(cx1, cy2 - 2*r, cx1 + 2*r, cy2, 
                            start=180, extent=90, style='arc', outline=color)
            canvas.create_arc(cx2 - 2*r, cy2 - 2*r, cx2, cy2, 
                            start=270, extent=90, style='arc', outline=color)
    
    def set_border_line_style(self, style_id):
        """设置边框线条样式"""
        self.border_config['line_style'] = style_id
        # 更新按钮选中状态
        if hasattr(self, 'line_style_buttons'):
            for sid, btn in self.line_style_buttons.items():
                if sid == style_id:
                    btn.config(bg=COLORS['accent'], fg=COLORS['text_bright'], font=('SF Pro Text', 10, 'bold'))
                else:
                    btn.config(bg=COLORS['bg_tertiary'], fg=COLORS['text_primary'], font=('SF Pro Text', 10))
        self.update_border_preview()
        self.apply_border_realtime()
    
    def set_border_pattern(self, pattern_id):
        """设置边框图案"""
        self.border_config['pattern'] = pattern_id
        # 切换图案时也确保尺寸正确
        current_width = self.border_config.get('width', 10)
        self.border_config['pattern_size'] = max(4, int(current_width * 0.6))
        # 更新按钮选中状态
        if hasattr(self, 'border_pattern_buttons'):
            for pid, btn in self.border_pattern_buttons.items():
                if pid == pattern_id:
                    btn.config(bg=COLORS['accent'], fg=COLORS['text_bright'], font=('SF Pro Text', 10, 'bold'))
                else:
                    btn.config(bg=COLORS['bg_tertiary'], fg=COLORS['text_primary'], font=('SF Pro Text', 10))
        self.update_border_preview()
        self.apply_border_realtime()
    
    def set_bg_pattern(self, pattern_id):
        """设置背景图案"""
        self.background_pattern = pattern_id
        # 更新按钮选中状态
        if hasattr(self, 'bg_pattern_buttons'):
            for pid, btn in self.bg_pattern_buttons.items():
                if pid == pattern_id:
                    btn.config(bg=COLORS['accent'], fg=COLORS['text_bright'], font=('SF Pro Text', 10, 'bold'))
                else:
                    btn.config(bg=COLORS['bg_tertiary'], fg=COLORS['text_primary'], font=('SF Pro Text', 10))
        # 应用背景图案
        self.canvas_widget.set_background_pattern(
            self.background_pattern,
            self.background_color,
            self.background_pattern_color,
            self.background_pattern_size
        )
    
    def choose_bg_pattern_color(self):
        """选择背景图案颜色"""
        def on_color_selected(color):
            self.background_pattern_color = color
            if hasattr(self, 'bg_pattern_color_canvas'):
                self.bg_pattern_color_canvas.config(bg=color)
            # 应用背景图案
            self.canvas_widget.set_background_pattern(
                self.background_pattern,
                self.background_color,
                self.background_pattern_color,
                self.background_pattern_size
            )
        
        def on_realtime_preview(color):
            """实时预览图案颜色"""
            if hasattr(self, 'bg_pattern_color_canvas'):
                self.bg_pattern_color_canvas.config(bg=color)
            # 实时应用背景图案
            self.canvas_widget.set_background_pattern(
                self.background_pattern,
                self.background_color,
                color,
                self.background_pattern_size
            )
        
        ColorWheelPicker(self, self.background_pattern_color, on_color_selected, on_realtime_preview)
    
    def on_bg_pattern_size_change(self, value):
        """背景图案大小改变"""
        self.background_pattern_size = int(float(value))
        if hasattr(self, 'bg_pattern_size_label'):
            self.bg_pattern_size_label.config(text=f'{self.background_pattern_size}px')
        # 应用背景图案
        self.canvas_widget.set_background_pattern(
            self.background_pattern,
            self.background_color,
            self.background_pattern_color,
            self.background_pattern_size
        )
    
    def clear_border(self):
        """清除边框"""
        self.canvas_widget.canvas.delete('border')
        self.canvas_widget.canvas.delete('border_image')
        # 重置边框配置为默认值（但不设为0，以便重新设置）
        self.border_config['width'] = 10
        self.border_config['radius'] = 0
        self.border_config['shape'] = 'rectangle'
        self.border_config['color'] = '#007AFF'
        
        # 更新滑块和按钮状态
        if hasattr(self, 'border_width_scale'):
            self.border_width_scale.set(10)
        if hasattr(self, 'border_radius_scale'):
            self.border_radius_scale.set(0)
        if hasattr(self, 'border_width_value'):
            self.border_width_value.config(text="10px")
        if hasattr(self, 'border_radius_value'):
            self.border_radius_value.config(text="0px")
        if hasattr(self, 'border_color_canvas'):
            self.border_color_canvas.config(bg='#007AFF')
        if hasattr(self, 'border_color_hex_label'):
            self.border_color_hex_label.config(text='#007AFF')
        
        # 更新形状按钮
        if hasattr(self, 'border_shape_buttons'):
            for sid, btn in self.border_shape_buttons.items():
                if sid == 'rectangle':
                    btn.config(
                        bg=COLORS['accent'], fg=COLORS['selected_text'],
                        font=('SF Pro Text', 10, 'bold'),
                        highlightthickness=2, highlightbackground=COLORS['accent']
                    )
                else:
                    btn.config(
                        bg=COLORS['panel_bg'], fg=COLORS['text_secondary'],
                        font=('SF Pro Text', 10),
                        highlightthickness=1, highlightbackground=COLORS['separator']
                    )
        
        # 更新预览
        self.update_border_preview()
        print("✓ 边框已清除，可重新设置")
    
    def set_border_shape(self, shape_id):
        """设置边框形状"""
        self.border_config['shape'] = shape_id
        for sid, btn in self.border_shape_buttons.items():
            if sid == shape_id:
                btn.config(
                    bg=COLORS['accent'], fg=COLORS['text_bright'],
                    font=('SF Pro Text', 10, 'bold')
                )
            else:
                btn.config(
                    bg=COLORS['bg_tertiary'], fg=COLORS['text_primary'],
                    font=('SF Pro Text', 10)
                )
        self.update_border_preview()
        self.apply_border_realtime()  # 实时应用
    
    def on_border_width_change(self, value):
        """边框粗细改变"""
        width = int(float(value))
        self.border_config['width'] = width
        if hasattr(self, 'border_width_value'):
            self.border_width_value.config(text=f"{width}px")
        self.update_border_preview()
        self.apply_border_realtime()  # 实时应用
    
    def on_border_radius_change(self, value):
        """圆角改变"""
        radius = int(float(value))
        self.border_config['radius'] = radius
        if hasattr(self, 'border_radius_value'):
            self.border_radius_value.config(text=f"{radius}px")
        self.update_border_preview()
        self.apply_border_realtime()  # 实时应用
    
    def choose_border_color(self):
        """选择边框颜色 - 使用颜色圆盘"""
        def on_color_selected(color):
            self.border_config['color'] = color
            if hasattr(self, 'border_color_canvas'):
                self.border_color_canvas.config(bg=color)
            if hasattr(self, 'border_color_hex_label'):
                self.border_color_hex_label.config(text=color)
            self.update_border_preview()
        
        def on_realtime_preview(color):
            """实时预览边框颜色"""
            self.border_config['color'] = color
            if hasattr(self, 'border_color_canvas'):
                self.border_color_canvas.config(bg=color)
            if hasattr(self, 'border_color_hex_label'):
                self.border_color_hex_label.config(text=color)
            self.update_border_preview()
            self.apply_border_realtime()
        
        ColorWheelPicker(self, self.border_config['color'], on_color_selected, on_realtime_preview)
    
    def set_border_color_quick(self, color):
        """快速设置边框颜色"""
        self.border_config['color'] = color
        if hasattr(self, 'border_color_canvas'):
            self.border_color_canvas.config(bg=color)
        if hasattr(self, 'border_color_hex_label'):
            self.border_color_hex_label.config(text=color)
        self.update_border_preview()
        self.apply_border_realtime()  # 实时应用
    
    def apply_border_realtime(self):
        """实时应用边框到画布"""
        if self.border_config['width'] > 0:
            self.canvas_widget.apply_custom_border(self.border_config)
            self.save_history("修改边框")
    
    def apply_custom_border(self):
        """应用自定义边框"""
        print(f"✓ 应用边框: {self.border_config}")
        self.canvas_widget.apply_custom_border(self.border_config)

    def create_sticker_tab(self, parent):
        """贴纸标签页 - 支持两个分类（fluent_3d和google_emoji）"""
        sticker_label = tk.Label(
            parent, text='点击添加贴纸', font=('SF Pro Display', 13, 'bold'),
            bg=COLORS['panel_bg'], fg=COLORS['text_primary'], anchor='w'
        )
        sticker_label.pack(fill=tk.X, padx=16, pady=(16, 8))
        
        # 存储当前打开的分类和所有分类的状态
        if not hasattr(self, 'active_sticker_category'):
            self.active_sticker_category = None
        if not hasattr(self, 'sticker_category_states'):
            self.sticker_category_states = {}
        
        # 扫描两个目录的PNG文件
        assets_dir = os.path.join(os.path.dirname(__file__), 'assets', 'stickers')
        fluent_3d_dir = os.path.join(assets_dir, 'fluent_3d')
        google_emoji_dir = os.path.join(assets_dir, 'google_emoji')
        
        # 获取文件列表
        fluent_3d_files = []
        if os.path.exists(fluent_3d_dir):
            fluent_3d_files = sorted([f for f in os.listdir(fluent_3d_dir) if f.endswith('.png')])
        
        google_emoji_files = []
        if os.path.exists(google_emoji_dir):
            google_emoji_files = sorted([f for f in os.listdir(google_emoji_dir) if f.endswith('.png')])
        
        # 创建分类容器
        categories_container = tk.Frame(parent, bg=COLORS['panel_bg'])
        categories_container.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 16))
        
        # 存储容器引用，用于手风琴效果
        self.sticker_categories_container = categories_container
        
        # Fluent 3D 分类
        fluent_category_state = self._create_sticker_category(
            categories_container, 
            '3D 贴纸', 
            fluent_3d_files, 
            'fluent_3d',
            is_open=True
        )
        self.sticker_category_states['fluent_3d'] = fluent_category_state
        
        # Google Emoji 分类
        google_category_state = self._create_sticker_category(
            categories_container,
            '2D 贴纸',
            google_emoji_files,
            'google_emoji',
            is_open=False
        )
        self.sticker_category_states['google_emoji'] = google_category_state
    
    def _create_sticker_category(self, parent, title, file_list, category_type, is_open=False):
        """创建可折叠的贴纸分类"""
        # 分类容器 [FIX] 使用 BOTH/Expand 允许垂直扩展，但默认受 pack 顺序影响
        category_frame = tk.Frame(parent, bg=COLORS['panel_bg'])
        # 初始只横向填充，展开时才 expand
        category_frame.pack(fill=tk.X, pady=(0, 8))
        
        # 标题栏（可点击折叠/展开）
        header_frame = tk.Frame(category_frame, bg=COLORS['bg_tertiary'], cursor='hand2')
        header_frame.pack(fill=tk.X)
        
        # 折叠/展开图标
        collapse_label = tk.Label(
            header_frame, 
            text='▼' if is_open else '▶',
            font=('SF Pro Display', 10),
            bg=COLORS['bg_tertiary'],
            fg=COLORS['text_primary']
        )
        collapse_label.pack(side=tk.LEFT, padx=(8, 8), pady=8)
        
        # 标题
        title_label = tk.Label(
            header_frame,
            text=f'{title} ({len(file_list)})',
            font=('SF Pro Display', 12, 'bold'),
            bg=COLORS['bg_tertiary'],
            fg=COLORS['text_primary'],
            anchor='w'
        )
        title_label.pack(side=tk.LEFT, fill=tk.X, expand=True, pady=8)
        
        # 创建滚动容器（Canvas + Scrollbar）
        # [FIX] 设置最小高度或让其能够扩展
        scroll_container = tk.Frame(category_frame, bg=COLORS['panel_bg'])
        
        # Canvas用于滚动 [FIX] 设置 height 以增加默认可视高度 (如 500)
        scroll_canvas = tk.Canvas(
            scroll_container,
            bg=COLORS['panel_bg'],
            highlightthickness=0,
            bd=0,
            height=500  # [FIX] 增加高度
        )
        
        # 滚动条
        scrollbar = tk.Scrollbar(
            scroll_container,
            orient='vertical',
            command=scroll_canvas.yview
        )
        
        # 网格容器（内容区域）
        grid_frame = tk.Frame(scroll_canvas, bg=COLORS['panel_bg'])
        
        # 将grid_frame添加到Canvas
        scroll_canvas.create_window((0, 0), window=grid_frame, anchor='nw')
        
        # 配置滚动区域
        def configure_scroll_region(e=None):
            scroll_canvas.configure(scrollregion=scroll_canvas.bbox('all'))
            # [FIX] 同时设置 canvas 宽度跟随容器，防止水平滚动
            scroll_canvas.itemconfig(scroll_canvas.find_withtag('all')[0], width=scroll_canvas.winfo_width())
        
        grid_frame.bind('<Configure>', configure_scroll_region)
        scroll_canvas.bind('<Configure>', lambda e: scroll_canvas.itemconfig(scroll_canvas.find_withtag('all')[0], width=e.width))

        # 布局Canvas和Scrollbar
        scroll_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # [FIX] 绑定鼠标滚轮
        self.bind_mousewheel(grid_frame, scroll_canvas)
        
        # 存储状态
        state = {
            'is_open': is_open,
            'grid_frame': grid_frame,
            'scroll_container': scroll_container,
            'collapse_label': collapse_label,
            'category_type': category_type,
            'category_frame': category_frame # [FIX] 存储 frame 引用以便修改 pack 属性
        }
        
        # 切换折叠/展开的函数
        def toggle_category(e=None):
            # was_open = state['is_open'] # Unused
            state['is_open'] = not state['is_open']
            
            if state['is_open']:
                # 打开当前分类
                state['collapse_label'].config(text='▼')
                
                # [FIX] 展开时，让 category_frame 填充并扩展剩余空间
                state['category_frame'].pack_configure(fill=tk.BOTH, expand=True)
                state['scroll_container'].pack(fill=tk.BOTH, expand=True, padx=8, pady=(4, 0))
                
                self.active_sticker_category = category_type
                # 关闭其他分类
                self._close_other_sticker_categories(category_type)
            else:
                # 关闭当前分类
                state['collapse_label'].config(text='▶')
                state['scroll_container'].pack_forget()
                # [FIX] 恢复为仅横向填充
                state['category_frame'].pack_configure(fill=tk.X, expand=False)
                
                if self.active_sticker_category == category_type:
                    self.active_sticker_category = None
        
        # 返回状态字典
        state['toggle_category'] = toggle_category
        
        # 绑定点击事件
        header_frame.bind('<Button-1>', toggle_category)
        collapse_label.bind('<Button-1>', toggle_category)
        title_label.bind('<Button-1>', toggle_category)
        
        # 初始状态
        if is_open:
            # [FIX] 初始打开时也应用 expand
            category_frame.pack_configure(fill=tk.BOTH, expand=True)
            state['scroll_container'].pack(fill=tk.BOTH, expand=True, padx=8, pady=(4, 0))
            if not hasattr(self, 'active_sticker_category') or self.active_sticker_category is None:
                self.active_sticker_category = category_type
        
        # 创建贴纸网格 - 异步加载
        # 先创建占位符，然后逐步加载
        placeholder_image = None
        try:
            # 创建一个小的占位符图片（48x48，与显示尺寸一致）
            placeholder = Image.new('RGBA', (48, 48), (200, 200, 200, 100))
            placeholder_image = ImageTk.PhotoImage(placeholder)
        except:
            pass
        
        # 存储按钮和文件信息的映射
        button_map = {}
        
        for idx, filename in enumerate(file_list):
            row = idx // 6
            col = idx % 6
            
            file_path = os.path.join(
                os.path.dirname(__file__), 
                'assets', 'stickers', 
                category_type, 
                filename
            )
            
            # 创建按钮（先用占位符或emoji）
            # 不使用width/height限制，让图片自然显示
            btn = tk.Label(
                grid_frame,
                text='🎨',
                font=(get_emoji_font_name(), 28),
                bg=COLORS['bg_tertiary'],
                cursor='hand2'
            )
            
            # 如果有占位符图片，使用它
            if placeholder_image:
                btn.config(image=placeholder_image, text='')
            
            btn.grid(row=row, column=col, padx=4, pady=4)
            
            # 绑定点击事件 - 传递分类类型
            btn.bind('<Button-1>', lambda e, cat=category_type, f=filename: self.add_sticker_from_file(cat, f))
            # [FIX] 增加滚轮绑定到按钮上，确保鼠标在按钮上时也能滚动
            self.bind_mousewheel(btn, scroll_canvas)
            
            btn.bind('<Enter>', lambda e, b=btn: b.config(bg=COLORS['hover']))
            btn.bind('<Leave>', lambda e, b=btn: b.config(bg=COLORS['bg_tertiary']))
            
            # 存储按钮和文件路径的映射，用于异步加载
            button_map[btn] = (file_path, filename)
        
        # 异步加载图片
        self._load_sticker_images_async(button_map, category_type)
        
        return state
    
    def _close_other_sticker_categories(self, current_category):
        """关闭其他贴纸分类（手风琴效果）"""
        if not hasattr(self, 'sticker_category_states'):
            return
        
        for cat_type, state in self.sticker_category_states.items():
            if cat_type != current_category and state['is_open']:
                # 关闭其他分类
                state['is_open'] = False
                state['collapse_label'].config(text='▶')
                state['scroll_container'].pack_forget()
                # [FIX] 恢复 frame 为仅横向填充，不暂用垂直空间
                if 'category_frame' in state:
                    state['category_frame'].pack_configure(fill=tk.X, expand=False)
    
    def _load_sticker_images_async(self, button_map, category_type):
        """异步加载贴纸图片"""
        def load_worker():
            """工作线程：加载图片"""
            batch_size = 10  # 每批加载10个
            loaded_count = 0
            
            for btn, (file_path, filename) in button_map.items():
                # 检查缓存
                cache_key = f"{category_type}/{filename}"
                if cache_key in self.sticker_image_cache:
                    # 从缓存获取
                    cached_img = self.sticker_image_cache[cache_key]
                    # 创建UI显示用的缩略图
                    thumb_img = cached_img.copy()
                    thumb_img = thumb_img.resize((48, 48), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(thumb_img)
                    self.sticker_photo_refs.append(photo)
                    
                    # 在主线程中更新UI
                    self.after(0, lambda b=btn, p=photo: self._update_sticker_button(b, p))
                else:
                    # 加载新图片
                    if os.path.exists(file_path):
                        try:
                            img = Image.open(file_path).convert('RGBA')
                            # 缓存原始图片（用于画布显示，保持高分辨率）
                            self.sticker_image_cache[cache_key] = img.copy()
                            
                            # 创建UI显示用的缩略图
                            thumb_img = img.copy()
                            thumb_img = thumb_img.resize((48, 48), Image.Resampling.LANCZOS)
                            photo = ImageTk.PhotoImage(thumb_img)
                            self.sticker_photo_refs.append(photo)
                            
                            # 在主线程中更新UI
                            self.after(0, lambda b=btn, p=photo: self._update_sticker_button(b, p))
                        except Exception as e:
                            print(f"加载贴纸图片失败 {filename}: {e}")
                
                loaded_count += 1
                
                # 每批加载后稍作延迟，避免阻塞
                if loaded_count % batch_size == 0:
                    threading.Event().wait(0.01)  # 10ms延迟
        
        # 启动加载线程
        thread = threading.Thread(target=load_worker, daemon=True)
        thread.start()
    
    def _update_sticker_button(self, btn, photo):
        """更新贴纸按钮的图片（在主线程中调用）"""
        try:
            btn.config(image=photo, text='')
        except:
            pass
    
    def set_background_color(self, color):
        """设置背景颜色"""
        self.background_color = color
        self.canvas_widget.set_background_color(color)
        # 更新预览Canvas
        if hasattr(self, 'bg_color_preview'):
            self.bg_color_preview.config(bg=color)
        # 更新颜色值标签
        if hasattr(self, 'bg_color_hex_label'):
            self.bg_color_hex_label.config(text=color)
        # 更新选中效果 - 高亮当前选中的颜色
        if hasattr(self, 'bg_color_canvases'):
            for bg_id, canvas in self.bg_color_canvases.items():
                # 找到匹配的预设颜色
                is_selected = False
                for bg_preset in DEFAULT_BACKGROUNDS:
                    if bg_preset['id'] == bg_id and bg_preset['color'] == color:
                        is_selected = True
                        break
                # 设置高亮边框
                if is_selected:
                    canvas.config(highlightbackground='#007AFF', highlightthickness=3)
                else:
                    canvas.config(highlightbackground='#E5E5EA', highlightthickness=2)
        print(f"✓ 背景颜色: {color}")
        self.save_history("修改背景")
    
    def choose_background_color(self):
        """选择背景颜色 - 使用颜色圆盘"""
        def on_color_selected(color):
            self.set_background_color(color)
        
        def on_realtime_preview(color):
            """实时预览背景颜色"""
            self.set_background_color(color)
        
        ColorWheelPicker(self, self.background_color, on_color_selected, on_realtime_preview)
    
    def upload_background_image(self):
        """上传背景图片"""
        file_path = filedialog.askopenfilename(
            title='选择背景图片',
            filetypes=[('图片文件', '*.jpg *.jpeg *.png *.bmp'), ('所有文件', '*.*')]
        )
        if file_path:
            try:
                img = Image.open(file_path)
                self.background_image = img
                self.canvas_widget.set_background_image(img)
                print(f"✓ 背景图片已设置")
            except Exception as e:
                messagebox.showerror('错误', f'加载图片失败: {e}')
    
    def clear_background_image(self):
        """清除背景图片"""
        self.background_image = None
        self.canvas_widget.set_background_color(self.background_color)
        print("✓ 背景图片已清除")
    
    def generate_theme_thumbnail(self, theme, size=50):
        """生成主题缩略图"""
        from PIL import Image, ImageDraw, ImageTk
        
        # 创建缩略图画布
        img = Image.new('RGB', (size, size), theme.get('background_color', '#FFFFFF'))
        draw = ImageDraw.Draw(img)
        
        # 绘制背景图案（简化版）
        pattern = theme.get('background_pattern', 'none')
        pattern_color = theme.get('background_pattern_color', '#E0E0E0')
        if pattern == 'grid':
            spacing = 10
            for x in range(0, size, spacing):
                draw.line([(x, 0), (x, size)], fill=pattern_color, width=1)
            for y in range(0, size, spacing):
                draw.line([(0, y), (size, y)], fill=pattern_color, width=1)
        elif pattern == 'dots':
            spacing = 8
            for x in range(spacing//2, size, spacing):
                for y in range(spacing//2, size, spacing):
                    draw.ellipse([x-1, y-1, x+1, y+1], fill=pattern_color)
        elif pattern == 'stripe':
            spacing = 6
            for i in range(-size, size, spacing):
                draw.line([(i, 0), (i + size, size)], fill=pattern_color, width=1)
        
        # 绘制边框
        border_config = theme.get('border_config', {})
        border_width = min(border_config.get('width', 0) // 3, 5)  # 缩小边框
        if border_width > 0:
            border_color = border_config.get('color', '#000000')
            radius = min(border_config.get('radius', 0) // 4, 8)
            if radius > 0:
                draw.rounded_rectangle([0, 0, size-1, size-1], radius=radius, outline=border_color, width=border_width)
            else:
                for i in range(border_width):
                    draw.rectangle([i, i, size-1-i, size-1-i], outline=border_color)
        
        # 转换为 PhotoImage
        return ImageTk.PhotoImage(img)
        
    def get_current_theme_state(self):
        """获取当前主题状态"""
        # 序列化贴纸数据（去除 Image 对象）
        serializable_stickers = []
        for s in self.canvas_widget.get_stickers():
            s_copy = s.copy()
            if 'image' in s_copy:
                del s_copy['image'] # 删除 PIL 对象，它是不可序列化的
            serializable_stickers.append(s_copy)

        return {
            'background_color': self.background_color,
            'background_pattern': self.background_pattern,
            'background_pattern_color': self.background_pattern_color,
            'background_pattern_size': self.background_pattern_size,
            'border_config': self.border_config.copy(),
            'stickers': serializable_stickers
        }

    def apply_theme_state(self, state):
        """应用主题状态"""
        # 应用背景
        self.set_background_color(state['background_color'])
        self.set_bg_pattern(state['background_pattern'])
        self.background_pattern_color = state['background_pattern_color']
        self.background_pattern_size = state['background_pattern_size']
        self.canvas_widget.set_background_pattern(
            self.background_pattern, 
            self.background_color, 
            self.background_pattern_color, 
            self.background_pattern_size
        )
        if hasattr(self, 'bg_pattern_color_canvas'):
            self.bg_pattern_color_canvas.config(bg=self.background_pattern_color)
        if hasattr(self, 'bg_pattern_size_scale'):
            self.bg_pattern_size_scale.set(self.background_pattern_size)
            self.bg_pattern_size_label.config(text=f'{self.background_pattern_size}px')
        
        # 应用边框
        self.border_config = state['border_config'].copy()
        self.canvas_widget.apply_custom_border(self.border_config)
        # 更新边框UI状态
        self.selected_border_color = self.border_config['color']
        if hasattr(self, 'border_width_scale'):
            self.border_width_scale.set(self.border_config['width'])
        if hasattr(self, 'border_radius_scale'):
            self.border_radius_scale.set(self.border_config['radius'])
        if hasattr(self, 'border_color_canvas'):
            self.border_color_canvas.config(bg=self.border_config['color'])
        if hasattr(self, 'border_color_hex_label'):
            self.border_color_hex_label.config(text=self.border_config['color'])
        if hasattr(self, 'update_border_preview'):
            self.update_border_preview()
        
        # 应用贴纸
        self.canvas_widget.delete_selected_sticker()
        for sticker in self.canvas_widget.stickers:
            self.canvas_widget.canvas.delete(sticker['id'])
        self.canvas_widget.stickers = []
        
        for sticker_data in state['stickers']:
            # 恢复图片贴纸
            if sticker_data.get('is_image') and sticker_data.get('image_path'):
                try:
                    image_path = sticker_data['image_path']
                    if os.path.exists(image_path):
                        img = Image.open(image_path).convert('RGBA')
                        # 调整大小
                        size = sticker_data.get('size', 96)
                        img = img.resize((size, size), Image.Resampling.LANCZOS)
                        
                        self.canvas_widget.add_sticker_image(
                            img,
                            size=size,
                            category=sticker_data.get('category'),
                            image_path=image_path,
                            x=sticker_data.get('x'),
                            y=sticker_data.get('y')
                        )
                        continue
                except Exception as e:
                    print(f"Failed to restore sticker image: {e}")
            
            # 恢复文字/Emoji贴纸
            s_id = self.canvas_widget.canvas.create_text(
                sticker_data['x'], sticker_data['y'],
                text=sticker_data['text'],
                font=('Arial', sticker_data['size']),
                fill='black',
                tags='sticker'
            )
            new_s = sticker_data.copy()
            new_s['id'] = s_id
            self.canvas_widget.stickers.append(new_s)
            
    def save_preset_theme(self, index=None, silent=False):
        """保存当前为预设主题
        
        Args:
            index: 保存到的索引位置（目前未使用）
            silent: 如果为True，则不显示成功提示
        """
        state = self.get_current_theme_state()
        
        if len(self.preset_themes) >= 8:
            if not messagebox.askyesno("提示", "预设已满(8个)，保存新预设将覆盖最早的预设，是否继续？"):
                return
            self.preset_themes.pop(0)
            self.preset_themes.append(state)
        else:
            self.preset_themes.append(state)
            
        self.save_settings() # 保存设置 (包含预设)
        self.update_preset_theme_display()
        self.update_left_preset_display()
        
        if not silent:
            messagebox.showinfo("成功", "主题已保存！")

    def apply_preset_theme(self, index):
        """应用预设主题"""
        if 0 <= index < len(self.preset_themes):
            self.apply_theme_state(self.preset_themes[index])
            
    def update_preset_theme_display(self):
        """更新预设主题显示区域"""
        if hasattr(self, 'preset_grid_frame'):
            for widget in self.preset_grid_frame.winfo_children():
                widget.destroy()
            
            # 清理旧的缩略图引用
            if not hasattr(self, 'preset_thumbnails'):
                self.preset_thumbnails = []
            self.preset_thumbnails.clear()
            
            for i in range(8):
                row = i // 4
                col = i % 4
                
                container = tk.Frame(self.preset_grid_frame, bg=COLORS['panel_bg'])
                container.grid(row=row, column=col, padx=4, pady=4)
                
                if i < len(self.preset_themes):
                    # 生成缩略图
                    theme = self.preset_themes[i]
                    thumbnail = self.generate_theme_thumbnail(theme, size=50)
                    self.preset_thumbnails.append(thumbnail)
                    
                    btn = tk.Label(
                        container,
                        image=thumbnail,
                        bg=COLORS['bg_tertiary'],
                        cursor='hand2',
                        relief=tk.FLAT,
                        bd=2
                    )
                    btn.pack()
                    btn.bind('<Button-1>', lambda e, idx=i: self.apply_preset_theme(idx))
                    # Hover effect
                    def make_hover(b):
                        b.bind('<Enter>', lambda e: b.config(bg=COLORS['hover']))
                        b.bind('<Leave>', lambda e: b.config(bg=COLORS['bg_tertiary']))
                    make_hover(btn)
                else:
                    btn = tk.Label(
                        container,
                        text="＋",
                        bg=COLORS['bg_secondary'],
                        fg=COLORS['text_secondary'],
                        font=('SF Pro Text', 14),
                        width=5, height=2,
                        cursor='hand2'
                    )
                    btn.pack()
                    btn.bind('<Button-1>', lambda e: self.save_preset_theme())
                    # Hover effect
                    def make_hover(b):
                        b.bind('<Enter>', lambda e: b.config(bg=COLORS['hover']))
                        b.bind('<Leave>', lambda e: b.config(bg=COLORS['bg_secondary']))
                    make_hover(btn)

    def update_left_preset_display(self):
        """更新左侧面板的预设主题显示"""
        if not hasattr(self, 'left_preset_grid'):
            return
            
        # 清空现有按钮
        for widget in self.left_preset_grid.winfo_children():
            widget.destroy()
        
        # 清理旧的缩略图引用
        if not hasattr(self, 'left_preset_thumbnails'):
            self.left_preset_thumbnails = []
        self.left_preset_thumbnails.clear()
        
        # 创建2列4行的按钮网格
        for i in range(8):
            row = i // 2
            col = i % 2
            
            if i < len(self.preset_themes):
                # 生成缩略图
                theme = self.preset_themes[i]
                thumbnail = self.generate_theme_thumbnail(theme, size=40)
                self.left_preset_thumbnails.append(thumbnail)
                
                # 已保存的预设 - 使用缩略图
                btn = tk.Label(
                    self.left_preset_grid,
                    image=thumbnail,
                    bg=COLORS['bg_tertiary'],
                    cursor='hand2',
                    relief=tk.FLAT,
                    bd=1
                )
                btn.grid(row=row, column=col, padx=2, pady=2, sticky='ew')
                btn.bind('<Button-1>', lambda e, idx=i: self.apply_preset_theme(idx))
                
                def make_hover(b):
                    b.bind('<Enter>', lambda e: b.config(bg=COLORS['hover']))
                    b.bind('<Leave>', lambda e: b.config(bg=COLORS['bg_tertiary']))
                make_hover(btn)
            else:
                # 空槽位 - 点击保存新预设
                btn = tk.Label(
                    self.left_preset_grid,
                    text="＋",
                    bg=COLORS['bg_secondary'],
                    fg=COLORS['text_secondary'],
                    font=('SF Pro Text', 12),
                    width=4, height=2,
                    cursor='hand2'
                )
                btn.grid(row=row, column=col, padx=2, pady=2, sticky='ew')
                btn.bind('<Button-1>', lambda e: self.save_preset_theme())
                
                def make_hover(b):
                    b.bind('<Enter>', lambda e: b.config(bg=COLORS['hover']))
                    b.bind('<Leave>', lambda e: b.config(bg=COLORS['bg_secondary']))
                make_hover(btn)
        
        # 配置列权重使按钮均匀分布
        self.left_preset_grid.columnconfigure(0, weight=1)
        self.left_preset_grid.columnconfigure(1, weight=1)
