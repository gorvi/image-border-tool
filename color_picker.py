"""
颜色选择器组件
"""

import tkinter as tk
from tkinter import ttk

class ColorPicker(tk.Toplevel):
    """颜色选择器弹窗"""
    
    def __init__(self, parent, initial_color='#000000', callback=None):
        super().__init__(parent)
        
        self.title('选择颜色')
        self.geometry('320x420')
        self.resizable(False, False)
        
        self.selected_color = initial_color
        self.callback = callback
        
        # 设置窗口居中
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (320 // 2)
        y = (self.winfo_screenheight() // 2) - (420 // 2)
        self.geometry(f'+{x}+{y}')
        
        self.create_widgets()
    
    def create_widgets(self):
        """创建UI组件"""
        # 预设颜色
        preset_frame = tk.LabelFrame(self, text='预设颜色', font=('SF Pro', 11, 'bold'))
        preset_frame.pack(fill=tk.X, padx=10, pady=10)
        
        preset_colors = [
            '#000000', '#FFFFFF', '#FF0000', '#00FF00', '#0000FF',
            '#FFFF00', '#FF00FF', '#00FFFF', '#FFA500', '#800080',
            '#FFC0CB', '#A52A2A', '#808080', '#FFD700', '#C0C0C0',
            '#00CED1', '#FF1493', '#7FFF00', '#DC143C', '#4B0082',
        ]
        
        color_grid = tk.Frame(preset_frame)
        color_grid.pack(padx=10, pady=10)
        
        for idx, color in enumerate(preset_colors):
            row = idx // 5
            col = idx % 5
            btn = tk.Button(
                color_grid,
                bg=color,
                width=4,
                height=2,
                relief=tk.FLAT,
                bd=1,
                command=lambda c=color: self.select_color(c)
            )
            btn.grid(row=row, column=col, padx=2, pady=2)
        
        # RGB 滑块
        rgb_frame = tk.LabelFrame(self, text='RGB 调节', font=('SF Pro', 11, 'bold'))
        rgb_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # 解析初始颜色
        initial_rgb = self.hex_to_rgb(self.selected_color)
        
        # R
        r_frame = tk.Frame(rgb_frame)
        r_frame.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(r_frame, text='R:', width=3).pack(side=tk.LEFT)
        self.r_scale = tk.Scale(
            r_frame, from_=0, to=255, orient=tk.HORIZONTAL,
            command=self.on_rgb_change
        )
        self.r_scale.set(initial_rgb[0])
        self.r_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.r_value = tk.Label(r_frame, text=str(initial_rgb[0]), width=3)
        self.r_value.pack(side=tk.LEFT)
        
        # G
        g_frame = tk.Frame(rgb_frame)
        g_frame.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(g_frame, text='G:', width=3).pack(side=tk.LEFT)
        self.g_scale = tk.Scale(
            g_frame, from_=0, to=255, orient=tk.HORIZONTAL,
            command=self.on_rgb_change
        )
        self.g_scale.set(initial_rgb[1])
        self.g_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.g_value = tk.Label(g_frame, text=str(initial_rgb[1]), width=3)
        self.g_value.pack(side=tk.LEFT)
        
        # B
        b_frame = tk.Frame(rgb_frame)
        b_frame.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(b_frame, text='B:', width=3).pack(side=tk.LEFT)
        self.b_scale = tk.Scale(
            b_frame, from_=0, to=255, orient=tk.HORIZONTAL,
            command=self.on_rgb_change
        )
        self.b_scale.set(initial_rgb[2])
        self.b_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.b_value = tk.Label(b_frame, text=str(initial_rgb[2]), width=3)
        self.b_value.pack(side=tk.LEFT)
        
        # 颜色预览
        preview_frame = tk.Frame(self)
        preview_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(preview_frame, text='预览:', font=('SF Pro', 11)).pack(side=tk.LEFT, padx=5)
        
        self.preview = tk.Frame(
            preview_frame,
            bg=self.selected_color,
            width=100,
            height=40,
            relief=tk.SUNKEN,
            bd=2
        )
        self.preview.pack(side=tk.LEFT, padx=10)
        
        self.hex_label = tk.Label(
            preview_frame,
            text=self.selected_color,
            font=('Courier', 12, 'bold')
        )
        self.hex_label.pack(side=tk.LEFT, padx=10)
        
        # 按钮 - 使用Label替代Button (macOS上Button的fg不生效)
        btn_frame = tk.Frame(self, bg='#252526')
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ok_btn = tk.Label(
            btn_frame,
            text='确定',
            bg='#0A84FF',
            fg='#FFFFFF',
            font=('SF Pro', 11, 'bold'),
            padx=20,
            pady=8,
            cursor='hand2'
        )
        ok_btn.pack(side=tk.RIGHT, padx=5)
        ok_btn.bind('<Button-1>', lambda e: self.on_ok())
        ok_btn.bind('<Enter>', lambda e: ok_btn.config(bg='#409CFF'))
        ok_btn.bind('<Leave>', lambda e: ok_btn.config(bg='#0A84FF'))
        
        cancel_btn = tk.Label(
            btn_frame,
            text='取消',
            bg='#404040',
            fg='#E8E8E8',
            font=('SF Pro', 11),
            padx=20,
            pady=8,
            cursor='hand2'
        )
        cancel_btn.pack(side=tk.RIGHT, padx=5)
        cancel_btn.bind('<Button-1>', lambda e: self.destroy())
        cancel_btn.bind('<Enter>', lambda e: cancel_btn.config(bg='#505050'))
        cancel_btn.bind('<Leave>', lambda e: cancel_btn.config(bg='#404040'))
    
    def hex_to_rgb(self, hex_color):
        """HEX转RGB"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def rgb_to_hex(self, r, g, b):
        """RGB转HEX"""
        return f'#{r:02x}{g:02x}{b:02x}'
    
    def on_rgb_change(self, value):
        """RGB值改变"""
        r = self.r_scale.get()
        g = self.g_scale.get()
        b = self.b_scale.get()
        
        self.r_value.config(text=str(r))
        self.g_value.config(text=str(g))
        self.b_value.config(text=str(b))
        
        self.selected_color = self.rgb_to_hex(r, g, b)
        self.preview.config(bg=self.selected_color)
        self.hex_label.config(text=self.selected_color)
    
    def select_color(self, color):
        """选择预设颜色"""
        self.selected_color = color
        rgb = self.hex_to_rgb(color)
        
        self.r_scale.set(rgb[0])
        self.g_scale.set(rgb[1])
        self.b_scale.set(rgb[2])
        
        self.preview.config(bg=color)
        self.hex_label.config(text=color)
    
    def on_ok(self):
        """确定"""
        if self.callback:
            self.callback(self.selected_color)
        self.destroy()
