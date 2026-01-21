import tkinter as tk
from tkinter import ttk
from constants import COLORS

class ModernStyles:
    @staticmethod
    def apply_theme(root):
        """应用全局 TTK 主题样式"""
        style = ttk.Style(root)
        
        # 尝试使用 'clam' 主题作为基础，因为它更容易自定义颜色且去除了大部分原生3D效果
        try:
            style.theme_use('clam')
        except:
            pass
            
        # 配置 TCombobox (下拉框)
        style.configure('TCombobox',
                        fieldbackground=COLORS['input_bg'],
                        background=COLORS['bg_secondary'],
                        foreground=COLORS['text_primary'],
                        arrowcolor=COLORS['text_secondary'],
                        borderwidth=0,
                        relief='flat',
                        padding=5)
        
        style.map('TCombobox',
                  fieldbackground=[('readonly', COLORS['input_bg'])],
                  selectbackground=[('readonly', COLORS['input_bg'])],
                  selectforeground=[('readonly', COLORS['text_primary'])],
                  background=[('active', COLORS['hover'])])
                  
        # 配置 TButton (虽然主要用 tk.Button, 但以防万一)
        style.configure('TButton',
                        background=COLORS['btn_primary'],
                        foreground='#FFFFFF',
                        borderwidth=0,
                        focusthickness=0,
                        padding=(10, 5))
                        
        style.map('TButton',
                  background=[('active', COLORS['accent_hover']), ('disabled', COLORS['btn_secondary'])])

    @staticmethod
    def create_entry(parent, **kwargs):
        """创建现代风格输入框 (Flat, 1px Border)"""
        font = kwargs.pop('font', ('SF Pro Text', 10))
        bg = kwargs.pop('bg', COLORS['input_bg'])
        fg = kwargs.pop('fg', COLORS['text_primary'])
        width = kwargs.pop('width', 20)
        
        # 移除默认 3D 边框，使用 highlight 模拟 1px 边框
        entry = tk.Entry(parent,
                        font=font,
                        bg=bg,
                        fg=fg,
                        width=width,
                        relief='flat',
                        highlightthickness=1,
                        highlightbackground=COLORS['input_border'],
                        highlightcolor=COLORS['accent'],  # 聚焦时的边框色
                        insertbackground=COLORS['text_primary'], # 光标颜色
                        **kwargs)
        return entry
    
    @staticmethod
    def create_combobox(parent, variable, values, **kwargs):
        """创建现代风格下拉框"""
        font = kwargs.pop('font', ('SF Pro Text', 10))
        width = kwargs.pop('width', 15)
        state = kwargs.pop('state', 'readonly')
        
        # TTK Combobox 样式已经在 apply_theme 中全局配置
        # 但我们需要确保 parent 的背景色正确，避免边缘杂色
        cb = ttk.Combobox(parent, 
                         textvariable=variable, 
                         values=values,
                         state=state,
                         width=width,
                         font=font,
                         **kwargs)
        return cb

    @staticmethod
    def create_button(parent, text, command, variant='primary', **kwargs):
        """创建现代风格按钮 (Label 模拟，解决 macOS 背景色问题)"""
        bg_color = COLORS['accent'] if variant == 'primary' else COLORS['bg_tertiary']
        fg_color = '#FFFFFF' if variant == 'primary' else COLORS['text_secondary']
        active_bg = COLORS['accent_hover'] if variant == 'primary' else COLORS['hover']
        
        # 提取字体和其他参数
        font = kwargs.pop('font', ('SF Pro Text', 10, 'bold'))
        padx = kwargs.pop('padx', 12)
        pady = kwargs.pop('pady', 8)
        
        btn = tk.Label(parent,
                       text=text,
                       font=font,
                       bg=bg_color,
                       fg=fg_color,
                       cursor='hand2',
                       padx=padx,
                       pady=pady,
                       **kwargs)
        
        # 绑定点击事件
        def on_click(e):
            if command:
                command()
                
        def on_enter(e):
            if btn['state'] != 'disabled':
                btn.config(bg=active_bg)
                
        def on_leave(e):
            if btn['state'] != 'disabled':
                btn.config(bg=bg_color)
                
        btn.bind('<Button-1>', on_click)
        btn.bind('<Enter>', on_enter)
        btn.bind('<Leave>', on_leave)
        
        return btn

    @staticmethod
    def create_text_area(parent, **kwargs):
        """创建现代风格多行文本框"""
        font = kwargs.pop('font', ('SF Pro Text', 10))
        bg = kwargs.pop('bg', COLORS['bg_secondary'])
        fg = kwargs.pop('fg', COLORS['text_primary'])
        height = kwargs.pop('height', 4)
        width = kwargs.pop('width', 24)
        
        text = tk.Text(parent,
                      font=font,
                      bg=bg,
                      fg=fg,
                      height=height,
                      width=width,
                      relief='flat',
                      highlightthickness=1,
                      highlightbackground=COLORS['input_border'],
                      highlightcolor=COLORS['accent'],
                      insertbackground=COLORS['text_primary'],
                      **kwargs)
        return text
