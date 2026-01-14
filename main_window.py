"""
主窗口模块
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image
import os
from datetime import datetime

from canvas_widget import CanvasWidget
from image_processor import ImageProcessor, CompositeImage
from constants import (SIZE_PRESETS, BORDER_STYLES, STICKER_LIST, COLORS, 
                      BORDER_STYLES_WITH_PREVIEW, BORDER_CATEGORIES, 
                      BORDER_COLORS, BORDER_STYLE_NAMES,
                      BORDER_SHAPES, BORDER_LINE_STYLES, DEFAULT_BACKGROUNDS,
                      BORDER_PATTERNS, BACKGROUND_PATTERNS, DEFAULT_BORDER_CONFIG,
                      QUICK_COLORS)
from color_picker import ColorPicker
from color_wheel_picker import ColorWheelPicker
from PIL import Image, ImageTk, ImageDraw, ImageFont


class MainWindow(tk.Tk):
    """主窗口类"""
    
    def __init__(self):
        super().__init__()
        
        self.title('图片套版工具')
        
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
        
        # 初始化变量
        self.image_processor = ImageProcessor()
        self.current_size_preset = SIZE_PRESETS[3]  # 默认小红书3:4
        self.current_border = BORDER_STYLES[0]  # 默认无边框
        self.batch_images = []  # 批量图片列表
        self.sticker_images = {}  # 缓存贴纸图片
        self.border_preview_images = {}  # 缓存边框预览图
        self.sticker_photo_refs = []  # 保持图片引用，防止被垃圾回收
        self.border_photo_refs = []  # 保持边框图片引用
        
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
        
        # 创建UI
        self.create_widgets()
        
        # 绑定快捷键
        self.bind('<Command-z>', lambda e: self.undo())
        self.bind('<Command-Shift-Z>', lambda e: self.redo())
        self.bind('<Command-s>', lambda e: self.export_image())
        self.bind('<Configure>', self.on_window_resize)
    
    def on_window_resize(self, event):
        """窗口大小改变时调整画布"""
        if event.widget == self:
            # 延迟调整，避免频繁触发
            if hasattr(self, 'resize_timer'):
                self.after_cancel(self.resize_timer)
            self.resize_timer = self.after(100, self.adjust_canvas_display)
    
    def adjust_canvas_display(self):
        """自适应调整画布显示"""
        try:
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
        
    def create_widgets(self):
        """创建界面组件 - 毛玻璃风格"""
        # 主容器
        main_container = tk.Frame(self, bg=COLORS['bg'])
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # 左侧可折叠面板容器
        self.left_container = tk.Frame(main_container, bg=COLORS['bg'])
        self.left_container.pack(side=tk.LEFT, fill=tk.Y)
        
        # 左侧面板框架
        self.left_panel_frame = tk.Frame(self.left_container, bg=COLORS['bg'])
        self.left_panel_frame.pack(side=tk.LEFT, fill=tk.Y)
        
        self.left_panel = self.create_left_panel(self.left_panel_frame)
        self.left_panel.pack(fill=tk.BOTH, expand=True, padx=(8, 0), pady=8)
        
        # 折叠按钮 - 使用Label
        self.collapse_btn = tk.Label(
            self.left_container,
            text='◀',
            font=('SF Pro Text', 10),
            bg=COLORS['bg_secondary'],
            fg=COLORS['text_primary'],
            width=2,
            cursor='hand2'
        )
        self.collapse_btn.pack(side=tk.RIGHT, fill=tk.Y, padx=0)
        self.collapse_btn.bind('<Button-1>', lambda e: self.toggle_left_panel())
        self.collapse_btn.bind('<Enter>', lambda e: self.collapse_btn.config(bg=COLORS['hover']))
        self.collapse_btn.bind('<Leave>', lambda e: self.collapse_btn.config(bg=COLORS['bg_secondary']))
        
        self.left_panel_visible = True
        
        # 中间画布区域
        self.center_panel = self.create_center_panel(main_container)
        self.center_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=8, pady=8)
        
        # 右侧面板
        self.right_panel = self.create_right_panel(main_container)
        self.right_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 8), pady=8)
        
        # 延迟应用默认边框（等待画布初始化完成）
        self.after(200, self.apply_default_border)
    
    def apply_default_border(self):
        """应用默认边框"""
        self.canvas_widget.apply_custom_border(self.border_config)
        print("✓ 默认边框已应用")
    
    def toggle_left_panel(self):
        """切换左侧面板显示/隐藏"""
        if self.left_panel_visible:
            # 隐藏
            self.left_panel_frame.pack_forget()
            self.collapse_btn.config(text='▶')
            self.left_panel_visible = False
        else:
            # 显示
            self.left_panel_frame.pack(side=tk.LEFT, fill=tk.Y, before=self.collapse_btn)
            self.collapse_btn.config(text='◀')
            self.left_panel_visible = True
    
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
        
        btn_delete = tk.Label(
            left_buttons,
            text='🗑️ 删除',
            font=('SF Pro Text', 10),
            bg=COLORS['bg_tertiary'],
            fg=COLORS['danger'],
            padx=12,
            pady=6,
            cursor='hand2'
        )
        btn_delete.pack(side=tk.LEFT)
        btn_delete.bind('<Button-1>', lambda e: self.delete_selected_sticker())
        btn_delete.bind('<Enter>', lambda e: btn_delete.config(bg=COLORS['hover']))
        btn_delete.bind('<Leave>', lambda e: btn_delete.config(bg=COLORS['bg_tertiary']))
        
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
            width=280,
            relief=tk.FLAT,
            bd=0,
            highlightthickness=0
        )
        
        # 配置 ttk 标签页样式
        style = ttk.Style()
        style.theme_use('default')
        
        # 配置标签页样式 - 深色主题
        style.configure(
            'TNotebook',
            background=COLORS['panel_bg'],
            borderwidth=0,
            relief='flat',
            tabmargins=[0, 0, 0, 0]  # 移除标签页边距
        )
        style.configure(
            'TNotebook.Tab',
            background=COLORS['bg_tertiary'],
            foreground=COLORS['text_secondary'],
            padding=[8, 6],  # 减小 padding 避免区域重叠
            font=('SF Pro Text', 9),  # 稍小字体
            borderwidth=0,
            focuscolor='',  # 移除焦点颜色
        )
        style.map(
            'TNotebook.Tab',
            background=[('selected', COLORS['panel_bg'])],
            foreground=[('selected', COLORS['accent'])]
            # 移除 expand 效果，避免点击区域偏移
        )
        
        # 创建标签页
        notebook = ttk.Notebook(panel, style='TNotebook')
        notebook.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
        
        # 标签页1: 背景
        background_tab = tk.Frame(notebook, bg=COLORS['panel_bg'])
        notebook.add(background_tab, text='🎨 背景')
        self.create_background_tab(background_tab)
        
        # 标签页2: 边框
        border_tab = tk.Frame(notebook, bg=COLORS['panel_bg'])
        notebook.add(border_tab, text='🖼️ 边框')
        self.create_border_tab(border_tab)
        
        # 标签页3: 贴纸
        sticker_tab = tk.Frame(notebook, bg=COLORS['panel_bg'])
        notebook.add(sticker_tab, text='✨ 贴纸')
        self.create_sticker_tab(sticker_tab)
        
        # 标签页4: 基础编辑
        basic_tab = tk.Frame(notebook, bg=COLORS['panel_bg'])
        notebook.add(basic_tab, text='📐 编辑')
        self.create_basic_tools_tab(basic_tab)
        
        # 标签页5: 批量
        batch_tab = tk.Frame(notebook, bg=COLORS['panel_bg'])
        notebook.add(batch_tab, text='⚡ 批量')
        self.create_batch_tab(batch_tab)
        
        # 标签页6: 图层
        layer_tab = tk.Frame(notebook, bg=COLORS['panel_bg'])
        notebook.add(layer_tab, text='📚 图层')
        self.create_layer_tab(layer_tab)
        
        # 标签页7: 记录
        history_tab = tk.Frame(notebook, bg=COLORS['panel_bg'])
        notebook.add(history_tab, text='📝 记录')
        self.create_history_tab(history_tab)
        
        return panel
    
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
                    font=('Apple Color Emoji', 28),
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
    
    def create_batch_tab(self, parent):
        """批量处理标签页 - 现代风格"""
        batch_frame = tk.Frame(parent, bg=COLORS['panel_bg'])
        batch_frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=16)
        
        # 说明文字
        desc_label = tk.Label(
            batch_frame,
            text='批量处理可将当前设置的贴纸和边框\n应用到多张图片上',
            font=('SF Pro Text', 11),
            bg=COLORS['panel_bg'],
            fg=COLORS['text_secondary'],
            justify=tk.LEFT
        )
        desc_label.pack(pady=(0, 24))
        
        batch_upload_btn = tk.Label(
            batch_frame,
            text='📁 批量上传图片',
            bg=COLORS['warning'],
            fg='white',
            font=('SF Pro Text', 12, 'bold'),
            pady=14,
            cursor='hand2'
        )
        batch_upload_btn.pack(fill=tk.X, pady=6)
        batch_upload_btn.bind('<Button-1>', lambda e: self.batch_upload())
        batch_upload_btn.bind('<Enter>', lambda e: batch_upload_btn.config(bg='#E68A00'))
        batch_upload_btn.bind('<Leave>', lambda e: batch_upload_btn.config(bg=COLORS['warning']))
        
        self.batch_count_label = tk.Label(
            batch_frame,
            text='已选择: 0 张图片',
            bg=COLORS['panel_bg'],
            fg=COLORS['text_primary'],
            font=('SF Pro Display', 12, 'bold')
        )
        self.batch_count_label.pack(pady=12)
        
        batch_export_btn = tk.Label(
            batch_frame,
            text='⚡ 批量生成并导出',
            bg=COLORS['success'],
            fg='white',
            font=('SF Pro Text', 12, 'bold'),
            pady=14,
            cursor='hand2'
        )
        batch_export_btn.pack(fill=tk.X, pady=6)
        batch_export_btn.bind('<Button-1>', lambda e: self.batch_export())
        batch_export_btn.bind('<Enter>', lambda e: batch_export_btn.config(bg='#28A745'))
        batch_export_btn.bind('<Leave>', lambda e: batch_export_btn.config(bg=COLORS['success']))
        
        # 批量处理提示
        tip_text = """
使用步骤：
1. 先上传一张样例图片
2. 添加贴纸和边框
3. 点击"批量上传图片"
4. 点击"批量生成"即可

注意：批量处理会将当前画布
上的贴纸和边框应用到所有图片
        """
        tip_label = tk.Label(
            batch_frame,
            text=tip_text,
            font=('Arial', 9),
            bg=COLORS['bg'],
            fg='#666',
            justify=tk.LEFT,
            padx=10,
            pady=10
        )
        tip_label.pack(fill=tk.X, pady=20)
    
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
        if self.image_processor.current_image:
            self.refresh_canvas()
        
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
        """添加贴纸"""
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
            # 使用 border_config 而非 current_border，确保边框配置一致
            self.canvas_widget.apply_custom_border(self.border_config)
            
        # 确保顺序生效后再强制定序一次 (处理异步渲染)
        self.after(50, lambda: self.canvas_widget._ensure_layer_order())
        
        # 更新图层列表 (如果已创建)
        if hasattr(self, 'update_layer_list'):
            self.update_layer_list()
    
    def export_image(self):
        """导出图片"""
        if not self.image_processor.current_image:
            messagebox.showwarning('提示', '请先上传图片！')
            return
        
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
            # 获取导出参数
            preset_width = self.current_size_preset['width']
            preset_height = self.current_size_preset['height']
            display_width = self.canvas_widget.width
            display_height = self.canvas_widget.height
            scale = max(preset_width / display_width, preset_height / display_height)
            
            # 1. 创建背景图层
            final_img = Image.new('RGB', (preset_width, preset_height), self.background_color)
            draw = ImageDraw.Draw(final_img)
            
            # 2. 绘制背景图案
            if self.background_pattern and self.background_pattern != 'none':
                # 这里简单重构图案绘制逻辑，或调用专门的 helper
                scaled_pattern_size = int(self.background_pattern_size * scale)
                # 使用临时处理器来绘制图案以免影响主状态
                temp_proc = ImageProcessor()
                temp_proc.current_image = final_img
                temp_proc.draw_background_pattern(
                    self.background_pattern,
                    self.background_pattern_color,
                    scaled_pattern_size
                )
                final_img = temp_proc.current_image
            
            # 3. 绘制主图片
            if self.image_processor.current_image:
                # 首先获取图片在画布上的实际位置
                main_img_id = self.canvas_widget.main_image_id
                if main_img_id:
                    coords = self.canvas_widget.canvas.coords(main_img_id)
                    if coords:
                        cx, cy = coords
                        # 获取图片渲染大小
                        # 注意：Tkinter 里的图片坐标是中心点
                        main_pil = self.image_processor.current_image
                        
                        # 按比例缩放并粘贴
                        scaled_main_w = int(main_pil.width * scale)
                        scaled_main_h = int(main_pil.height * scale)
                        scaled_main_pil = main_pil.resize((scaled_main_w, scaled_main_h), Image.Resampling.LANCZOS)
                        
                        # 计算粘贴位置
                        paste_x = int(cx * scale - scaled_main_w / 2)
                        paste_y = int(cy * scale - scaled_main_h / 2)
                        final_img.paste(scaled_main_pil, (paste_x, paste_y), scaled_main_pil if scaled_main_pil.mode == 'RGBA' else None)
            
            # 4. 绘制贴纸
            sticker_draw = ImageDraw.Draw(final_img)
            for sticker in self.canvas_widget.get_stickers():
                scaled_x = int(sticker['x'] * scale)
                scaled_y = int(sticker['y'] * scale)
                scaled_size = int(sticker['size'] * scale)
                
                try:
                    # 尝试加载中文字体，如果失败回退
                    font = ImageFont.truetype("/System/Library/Fonts/STHeiti Light.ttc", scaled_size)
                except:
                    font = ImageFont.load_default()
                
                sticker_draw.text((scaled_x, scaled_y), sticker['text'], fill='black', font=font, anchor="mm")
            
            # 5. 绘制边框 (在最上层)
            from image_processor import CompositeImage
            
            # 使用 border_config 而非 current_border
            border_config = self.border_config.copy()
            print(f"[DEBUG] Exporting with border config: {border_config}")  # 调试
            
            # 只检查 width > 0 即可应用边框（移除对 id 的检查）
            if border_config.get('width', 0) > 0:
                # 缩放边框宽度和圆角
                border_config['width'] = int(border_config.get('width', 10) * scale)
                if 'radius' in border_config:
                    border_config['radius'] = int(border_config['radius'] * scale)
                
                composite = CompositeImage(preset_width, preset_height)
                composite.canvas = final_img.copy()
                composite.draw = ImageDraw.Draw(composite.canvas)
                
                if border_config.get('radius', 0) > 0:
                    composite.add_rounded_border(border_config)
                else:
                    composite.add_border(border_config)
                final_img = composite.canvas
                print(f"[DEBUG] Border applied successfully")
            else:
                print(f"[DEBUG] Skipping border - width={border_config.get('width')}")
            
            # 6. 保存
            try:
                final_img.save(file_path)
                messagebox.showinfo('成功', f'图片已保存到:\n{file_path}')
                
                # 根据勾选框状态决定是否自动保存预设
                if hasattr(self, 'auto_save_preset_var') and self.auto_save_preset_var.get():
                    self.save_preset_theme()
            except Exception as e:
                messagebox.showerror('错误', f'保存失败: {e}')
    
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
    
    def batch_export(self):
        """批量导出图片"""
        if not self.batch_images:
            messagebox.showwarning('提示', '请先批量上传图片！')
            return
        
        # 选择输出目录
        output_dir = filedialog.askdirectory(title='选择输出目录')
        if not output_dir:
            return
        
        success_count = 0
        preset_width = self.current_size_preset['width']
        preset_height = self.current_size_preset['height']
        
        for idx, img_path in enumerate(self.batch_images):
            try:
                # 加载图片
                processor = ImageProcessor()
                processor.load_image(img_path)
                processor.set_canvas_size(preset_width, preset_height)
                processor.resize_to_canvas(maintain_ratio=True)
                
                # 生成复合图片
                composite = CompositeImage(
                    preset_width,
                    preset_height,
                    bg_color=self.background_color
                )
                
                # 绘制背景图案
                composite.draw_background_pattern(
                    self.background_pattern,
                    self.background_pattern_color,
                    self.background_pattern_size
                )
                composite.add_main_image(processor.current_image, fit_mode='contain')
                
                # 添加贴纸（使用当前画布的贴纸）
                for sticker in self.canvas_widget.get_stickers():
                    composite.add_sticker(sticker['text'], sticker['x'], sticker['y'], sticker['size'])
                
                # 添加边框 - 使用 border_config（当前自定义设置）
                border_config = self.border_config.copy()
                if border_config.get('width', 0) > 0:
                    # 根据画布和导出尺寸缩放边框
                    display_width = self.canvas_widget.width
                    display_height = self.canvas_widget.height
                    scale = max(preset_width / display_width, preset_height / display_height)
                    border_config['width'] = int(border_config['width'] * scale)
                    if 'radius' in border_config:
                        border_config['radius'] = int(border_config['radius'] * scale)
                    
                    if border_config.get('radius', 0) > 0:
                        composite.add_rounded_border(border_config)
                    else:
                        composite.add_border(border_config)
                
                # 保存
                filename = os.path.basename(img_path)
                save_path = os.path.join(output_dir, f"processed_{filename}")
                if composite.save(save_path):
                    success_count += 1
                    
            except Exception as e:
                print(f"处理图片 {img_path} 失败: {e}")
        
        
        messagebox.showinfo('完成', f'批量处理完成！\n成功: {success_count}/{len(self.batch_images)}')
    
    def save_history(self, action_name="操作"):
        """保存历史记录"""
        import copy
        from datetime import datetime
        
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
            'stickers': copy.deepcopy(self.canvas_widget.stickers) if hasattr(self.canvas_widget, 'stickers') else []
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
                    'visible': visible
                })
        
        # 刷新画布
        self.refresh_canvas()
    
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
        self.history_listbox.bind('<ButtonRelease-1>', lambda e: self.restore_history_from_list())
        
        # 滚动条
        scrollbar = tk.Scrollbar(list_frame, command=self.history_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.history_listbox.config(yscrollcommand=scrollbar.set)
    
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
        
        # 初始化右键菜单
        self.layer_context_menu = tk.Menu(self, tearoff=0)
        self.layer_context_menu.add_command(label="👁️ 显示/隐藏", command=self.toggle_layer_visibility)
        self.layer_context_menu.add_separator()
        self.layer_context_menu.add_command(label="🗑️ 删除", command=self.delete_layer_item)
        
        # 初始加载
        self.update_layer_list()

    def update_layer_list(self):
        """更新图层列表显示"""
        if not hasattr(self, 'layer_list_frame'):
            return
            
        # 清空现有列表
        for widget in self.layer_list_frame.winfo_children():
            widget.destroy()
            
        # 获取所有图层项 (从上到下: 边框 -> 贴纸(反序) -> 主图 -> 背景)
        layers = []
        
        # 1. 边框 (如果存在或隐藏中)
        if self.border_config.get('width', 0) > 0 or getattr(self, '_temp_hidden_border_width', None):
            is_visible = not getattr(self, '_temp_hidden_border_width', None)
            layers.append({'type': 'border', 'name': '🖼️ 边框', 'id': 'border', 'visible': is_visible})
            
        # 2. 贴纸 (反序)
        if hasattr(self.canvas_widget, 'stickers'):
            for i, sticker in enumerate(reversed(self.canvas_widget.stickers)):
                text = sticker['text'][:10] + ('...' if len(sticker['text']) > 10 else '')
                is_visible = sticker.get('visible', True)
                layers.append({
                    'type': 'sticker', 
                    'name': f'✨ 贴纸: {text}', 
                    'id': sticker['id'],
                    'index': len(self.canvas_widget.stickers) - 1 - i,
                    'visible': is_visible
                })
                
        # 3. 主图片
        if self.image_processor.current_image:
            is_visible = self.canvas_widget.canvas.itemcget('main_image', 'state') != 'hidden'
            layers.append({'type': 'image', 'name': '📷 主图片', 'id': 'main_image', 'visible': is_visible})
            
        # 4. 背景
        is_visible = self.canvas_widget.canvas.itemcget('background_image', 'state') != 'hidden'
        layers.append({'type': 'background', 'name': '🎨 背景', 'id': 'background', 'visible': is_visible})
        
        # 渲染列表
        for idx, layer in enumerate(layers):
            item_frame = tk.Frame(self.layer_list_frame, bg=COLORS['bg_tertiary'])
            item_frame.pack(fill=tk.X, pady=1)
            
            # 可见性按钮 (眼睛图标)
            eye_icon = "👁️" if layer['visible'] else "⭕" # 使用圈圈代表闭眼/隐藏，或可用 🔒
            eye_label = tk.Label(
                item_frame, text=eye_icon, font=('SF Pro Text', 10),
                bg=COLORS['bg_tertiary'], fg=COLORS['text_secondary'] if layer['visible'] else COLORS['text_tertiary'],
                width=3, cursor='hand2'
            )
            eye_label.pack(side=tk.LEFT, fill=tk.Y)
            
            name_label = tk.Label(
                item_frame, text=layer['name'], font=('SF Pro Text', 10),
                bg=COLORS['bg_tertiary'], fg=COLORS['text_primary'],
                anchor='w', padx=8, pady=6
            )
            name_label.pack(fill=tk.X, side=tk.LEFT, expand=True)
            
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
            self.canvas_widget.select_item(layer['id'])
        else:
            self.canvas_widget.selected_item = None
            self.canvas_widget.canvas.delete('handle')
            
    def show_layer_context_menu(self, event, layer):
        """显示图层右键菜单"""
        self.on_layer_select(layer, event.widget.master)
        self.context_layer = layer
        self.layer_context_menu.entryconfig("🗑️ 删除", state=tk.NORMAL if layer['type'] in ['sticker', 'image'] else tk.DISABLED)
        self.layer_context_menu.post(event.x_root, event.y_root)
        
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
            iid = 'main_image'
            curr = self.canvas_widget.canvas.itemcget(iid, 'state')
            new_state = 'hidden' if curr!='hidden' else 'normal'
            self.canvas_widget.canvas.itemconfigure(iid, state=new_state)
            
        elif ltype == 'border':
             # 简单切换边框宽度
            if self.border_config.get('width', 0) > 0:
                self._temp_hidden_border_width = self.border_config.get('width')
                self.border_config['width'] = 0
            elif getattr(self, '_temp_hidden_border_width', None):
                self.border_config['width'] = self._temp_hidden_border_width
                self._temp_hidden_border_width = None
            self.refresh_canvas()
        
        elif ltype == 'background':
            iid = 'background_image'
            curr = self.canvas_widget.canvas.itemcget(iid, 'state')
            new_state = 'hidden' if curr!='hidden' else 'normal'
            self.canvas_widget.canvas.itemconfigure(iid, state=new_state)
            
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
            btn.grid(row=0, column=idx, padx=4)
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
        """贴纸标签页"""
        sticker_label = tk.Label(
            parent, text='点击添加贴纸', font=('SF Pro Display', 13, 'bold'),
            bg=COLORS['panel_bg'], fg=COLORS['text_primary'], anchor='w'
        )
        sticker_label.pack(fill=tk.X, padx=16, pady=(16, 8))
        
        sticker_grid = tk.Frame(parent, bg=COLORS['panel_bg'])
        sticker_grid.pack(fill=tk.X, padx=12, pady=(0, 16))
        
        for idx, sticker in enumerate(STICKER_LIST):
            row = idx // 4
            col = idx % 4
            
            # 使用Label替代Button
            if sticker['id'] in self.sticker_images:
                btn = tk.Label(
                    sticker_grid, image=self.sticker_images[sticker['id']],
                    bg=COLORS['bg_tertiary'], cursor='hand2'
                )
            else:
                btn = tk.Label(
                    sticker_grid, text=sticker['emoji'], font=('Apple Color Emoji', 28),
                    bg=COLORS['bg_tertiary'], width=2, height=1, cursor='hand2'
                )
            btn.grid(row=row, column=col, padx=4, pady=4)
            btn.bind('<Button-1>', lambda e, s=sticker: self.add_sticker(s))
            btn.bind('<Enter>', lambda e, b=btn: b.config(bg=COLORS['hover']))
            btn.bind('<Leave>', lambda e, b=btn: b.config(bg=COLORS['bg_tertiary']))
    
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
        
    def get_current_theme_state(self):
        """获取当前主题状态"""
        return {
            'background_color': self.background_color,
            'background_pattern': self.background_pattern,
            'background_pattern_color': self.background_pattern_color,
            'background_pattern_size': self.background_pattern_size,
            'border_config': self.border_config.copy(),
            'stickers': self.canvas_widget.get_stickers()
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
            
    def save_preset_theme(self, index=None):
        """保存当前为预设主题"""
        state = self.get_current_theme_state()
        
        if len(self.preset_themes) >= 8:
            if not messagebox.askyesno("提示", "预设已满(8个)，保存新预设将覆盖最早的预设，是否继续？"):
                return
            self.preset_themes.pop(0)
            self.preset_themes.append(state)
        else:
            self.preset_themes.append(state)
        
        self.update_preset_theme_display()
        self.update_left_preset_display()
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
             
             for i in range(8):
                row = i // 3
                col = i % 3
                
                container = tk.Frame(self.preset_grid_frame, bg=COLORS['panel_bg'])
                container.grid(row=row, column=col, padx=6, pady=6)
                
                if i < len(self.preset_themes):
                    btn = tk.Label(
                        container,
                        text=f"预设 {i+1}",
                        bg=COLORS['bg_tertiary'],
                        fg=COLORS['text_primary'],
                        font=('SF Pro Text', 11),
                        width=8, height=3,
                        cursor='hand2'
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
                        font=('SF Pro Text', 16),
                        width=8, height=3,
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
        
        # 创建2列4行的按钮网格
        for i in range(8):
            row = i // 2
            col = i % 2
            
            if i < len(self.preset_themes):
                # 已保存的预设
                btn = tk.Label(
                    self.left_preset_grid,
                    text=f"主题{i+1}",
                    bg=COLORS['bg_tertiary'],
                    fg=COLORS['text_primary'],
                    font=('SF Pro Text', 9),
                    width=6, height=2,
                    cursor='hand2'
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
                    width=6, height=2,
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
