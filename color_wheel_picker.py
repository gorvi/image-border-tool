"""
专业颜色圆盘选择器 - 美观版
"""

import tkinter as tk
import math
from PIL import Image, ImageDraw, ImageTk
from constants import QUICK_COLORS

class ColorWheelPicker(tk.Toplevel):
    """颜色圆盘选择器"""
    
    def __init__(self, parent, initial_color='#007AFF', callback=None, realtime_callback=None):
        super().__init__(parent)
        
        self.title('选择颜色')
        self.geometry('400x560')
        self.resizable(False, False)
        self.configure(bg='#252526')
        
        self.selected_color = initial_color
        self.initial_color = initial_color  # 保存初始颜色，用于取消时恢复
        self.callback = callback
        self.realtime_callback = realtime_callback  # 实时预览回调
        self.hue = 0
        self.saturation = 1.0
        self.value = 1.0
        
        # 从初始颜色解析HSV
        self.parse_initial_color(initial_color)
        
        # 居中显示
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - 210
        y = (self.winfo_screenheight() // 2) - 270
        self.geometry(f'+{x}+{y}')
        
        # 使窗口成为模态
        self.transient(parent)
        self.grab_set()
        
        # ESC键关闭
        self.bind('<Escape>', self.on_cancel)
        self.protocol("WM_DELETE_WINDOW", self.on_cancel)
        
        self.create_widgets()
    
    def parse_initial_color(self, hex_color):
        """解析初始颜色为HSV"""
        try:
            rgb = self.hex_to_rgb(hex_color)
            h, s, v = self.rgb_to_hsv(*rgb)
            self.hue = h
            self.saturation = s
            self.value = v
        except:
            self.hue = 0.6
            self.saturation = 1.0
            self.value = 1.0
    
    def create_widgets(self):
        """创建UI - 深色主题"""
        # 标题
        title_frame = tk.Frame(self, bg='#252526')
        title_frame.pack(fill=tk.X, padx=16, pady=(16, 8))
        
        tk.Label(
            title_frame,
            text='🎨 颜色选择器',
            font=('SF Pro Text', 14, 'bold'),
            bg='#252526',
            fg='#CCCCCC'
        ).pack(side=tk.LEFT)
        
        # 颜色圆盘容器
        wheel_container = tk.Frame(self, bg='#2D2D2D', relief=tk.FLAT, bd=0)
        wheel_container.pack(pady=(0, 12), padx=16)
        
        # 创建色轮图像
        self.wheel_size = 260
        self.create_color_wheel()
        
        self.wheel_canvas = tk.Canvas(
            wheel_container,
            width=self.wheel_size,
            height=self.wheel_size,
            bg='#2D2D2D',
            highlightthickness=0
        )
        self.wheel_canvas.pack(padx=8, pady=8)
        
        # 显示色轮
        self.wheel_canvas.create_image(
            self.wheel_size//2,
            self.wheel_size//2,
            image=self.wheel_photo
        )
        
        # 绘制选择指示器
        self.update_indicator()
        
        # 绑定点击事件
        self.wheel_canvas.bind('<Button-1>', self.on_wheel_click)
        self.wheel_canvas.bind('<B1-Motion>', self.on_wheel_click)
        
        # 亮度滑块
        brightness_frame = tk.Frame(self, bg='#252526')
        brightness_frame.pack(fill=tk.X, padx=20, pady=(0, 12))
        
        tk.Label(
            brightness_frame,
            text='亮度',
            font=('SF Pro Text', 11),
            bg='#252526',
            fg='#858585'
        ).pack(side=tk.LEFT, padx=(0, 12))
        
        self.brightness_scale = tk.Scale(
            brightness_frame,
            from_=0,
            to=100,
            orient=tk.HORIZONTAL,
            command=self.on_brightness_change,
            showvalue=False,
            bg='#252526',
            highlightthickness=0,
            troughcolor='#3C3C3C',
            activebackground='#0A84FF',
            length=200
        )
        self.brightness_scale.set(int(self.value * 100))
        self.brightness_scale.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.brightness_label = tk.Label(
            brightness_frame,
            text=f'{int(self.value * 100)}%',
            font=('SF Mono', 10),
            bg='#252526',
            fg='#0A84FF',
            width=5
        )
        self.brightness_label.pack(side=tk.LEFT, padx=(8, 0))
        
        # 预览和颜色值
        preview_frame = tk.Frame(self, bg='#252526')
        preview_frame.pack(fill=tk.X, padx=20, pady=(0, 16))
        
        # 颜色预览
        preview_container = tk.Frame(preview_frame, bg='#3C3C3C', bd=0)
        preview_container.pack(side=tk.LEFT, padx=(0, 16))
        
        self.preview = tk.Canvas(
            preview_container,
            bg=self.selected_color,
            width=70,
            height=50,
            highlightthickness=0
        )
        self.preview.pack(padx=2, pady=2)
        
        # 颜色信息
        info_frame = tk.Frame(preview_frame, bg='#252526')
        info_frame.pack(side=tk.LEFT, fill=tk.BOTH)
        
        tk.Label(
            info_frame,
            text='HEX',
            font=('SF Pro Text', 9),
            bg='#252526',
            fg='#6E6E6E'
        ).pack(anchor='w')
        
        self.hex_label = tk.Label(
            info_frame,
            text=self.selected_color.upper(),
            font=('SF Mono', 16, 'bold'),
            bg='#252526',
            fg='#CCCCCC'
        )
        self.hex_label.pack(anchor='w')
        
        # RGB值
        rgb = self.hex_to_rgb(self.selected_color)
        self.rgb_label = tk.Label(
            info_frame,
            text=f'RGB({rgb[0]}, {rgb[1]}, {rgb[2]})',
            font=('SF Mono', 9),
            bg='#252526',
            fg='#6E6E6E'
        )
        self.rgb_label.pack(anchor='w', pady=(2, 0))
        
        # 快捷颜色
        quick_frame = tk.Frame(self, bg='#252526')
        quick_frame.pack(fill=tk.X, padx=20, pady=(0, 16))
        
        # 快捷颜色 - 使用马卡龙色和多巴胺色
        quick_colors = QUICK_COLORS[:16]  # 选取前16个颜色(黑白+多巴胺色+部分马卡龙色)
        
        for color in quick_colors:
            c = tk.Canvas(
                quick_frame,
                width=22, height=22,
                bg=color,
                highlightthickness=1,
                highlightbackground='#D2D2D7',
                cursor='hand2'
            )
            c.pack(side=tk.LEFT, padx=2)
            c.bind('<Button-1>', lambda e, col=color: self.set_quick_color(col))
        
        # 按钮 - 使用Label替代Button (macOS上Button的fg不生效)
        btn_frame = tk.Frame(self, bg='#252526')
        btn_frame.pack(fill=tk.X, padx=20, pady=(0, 16))
        
        cancel_btn = tk.Label(
            btn_frame,
            text='取消',
            bg='#404040',
            fg='#E8E8E8',
            font=('SF Pro Text', 11),
            padx=24,
            pady=8,
            cursor='hand2'
        )
        cancel_btn.pack(side=tk.LEFT, padx=(0, 8))
        cancel_btn.bind('<Button-1>', self.on_cancel)
        cancel_btn.bind('<Enter>', lambda e: cancel_btn.config(bg='#505050'))
        cancel_btn.bind('<Leave>', lambda e: cancel_btn.config(bg='#404040'))
        
        ok_btn = tk.Label(
            btn_frame,
            text='确定',
            bg='#0A84FF',
            fg='#FFFFFF',
            font=('SF Pro Text', 11, 'bold'),
            padx=24,
            pady=8,
            cursor='hand2'
        )
        ok_btn.pack(side=tk.RIGHT)
        ok_btn.bind('<Button-1>', lambda e: self.on_ok())
        ok_btn.bind('<Enter>', lambda e: ok_btn.config(bg='#409CFF'))
        ok_btn.bind('<Leave>', lambda e: ok_btn.config(bg='#0A84FF'))
    
    def create_color_wheel(self):
        """创建颜色圆盘图像"""
        size = self.wheel_size
        img = Image.new('RGB', (size, size), '#2D2D2D')
        draw = ImageDraw.Draw(img)
        
        center = size // 2
        radius = center - 15
        
        # 绘制色轮
        for y in range(size):
            for x in range(size):
                dx = x - center
                dy = y - center
                distance = math.sqrt(dx*dx + dy*dy)
                
                if distance <= radius:
                    # 计算角度和饱和度
                    angle = math.atan2(dy, dx)
                    hue = (math.degrees(angle) + 180) / 360.0
                    saturation = distance / radius
                    
                    # HSV to RGB
                    r, g, b = self.hsv_to_rgb(hue, saturation, 1.0)
                    img.putpixel((x, y), (r, g, b))
        
        self.wheel_photo = ImageTk.PhotoImage(img)
    
    def update_indicator(self):
        """更新选择指示器"""
        self.wheel_canvas.delete('indicator')
        
        # 计算指示器位置
        center = self.wheel_size // 2
        radius = (center - 15) * self.saturation
        angle_rad = self.hue * 2 * math.pi - math.pi
        
        x = center + radius * math.cos(angle_rad)
        y = center + radius * math.sin(angle_rad)
        
        # 绘制指示器 - 白色外圈
        self.wheel_canvas.create_oval(
            x-10, y-10, x+10, y+10,
            outline='white',
            width=3,
            tags='indicator'
        )
        # 黑色内圈
        self.wheel_canvas.create_oval(
            x-8, y-8, x+8, y+8,
            outline='#333333',
            width=2,
            tags='indicator'
        )
        # 填充当前颜色
        self.wheel_canvas.create_oval(
            x-5, y-5, x+5, y+5,
            fill=self.selected_color,
            outline='',
            tags='indicator'
        )
    
    def on_wheel_click(self, event):
        """点击色轮"""
        center = self.wheel_size // 2
        dx = event.x - center
        dy = event.y - center
        distance = math.sqrt(dx*dx + dy*dy)
        radius = center - 15
        
        if distance <= radius:
            # 计算色相和饱和度
            angle = math.atan2(dy, dx)
            self.hue = (math.degrees(angle) + 180) / 360.0
            self.saturation = min(distance / radius, 1.0)
            
            self.update_color()
    
    def on_brightness_change(self, value):
        """亮度改变"""
        self.value = float(value) / 100.0
        if hasattr(self, 'brightness_label'):
            self.brightness_label.config(text=f'{int(self.value * 100)}%')
        self.update_color()
    
    def set_quick_color(self, color):
        """设置快捷颜色"""
        self.selected_color = color
        self.parse_initial_color(color)
        self.brightness_scale.set(int(self.value * 100))
        self.update_display()
        # 实时预览回调
        if self.realtime_callback:
            self.realtime_callback(self.selected_color)
    
    def update_color(self):
        """更新颜色"""
        r, g, b = self.hsv_to_rgb(self.hue, self.saturation, self.value)
        self.selected_color = self.rgb_to_hex(r, g, b)
        self.update_display()
        # 实时预览回调
        if self.realtime_callback:
            self.realtime_callback(self.selected_color)
    
    def update_display(self):
        """更新显示"""
        self.preview.config(bg=self.selected_color)
        self.hex_label.config(text=self.selected_color.upper())
        
        rgb = self.hex_to_rgb(self.selected_color)
        self.rgb_label.config(text=f'RGB({rgb[0]}, {rgb[1]}, {rgb[2]})')
        
        self.update_indicator()
    
    def hsv_to_rgb(self, h, s, v):
        """HSV转RGB"""
        h = h % 1.0
        c = v * s
        x = c * (1 - abs((h * 6) % 2 - 1))
        m = v - c
        
        if h < 1/6:
            r, g, b = c, x, 0
        elif h < 2/6:
            r, g, b = x, c, 0
        elif h < 3/6:
            r, g, b = 0, c, x
        elif h < 4/6:
            r, g, b = 0, x, c
        elif h < 5/6:
            r, g, b = x, 0, c
        else:
            r, g, b = c, 0, x
        
        return int((r+m)*255), int((g+m)*255), int((b+m)*255)
    
    def rgb_to_hsv(self, r, g, b):
        """RGB转HSV"""
        r, g, b = r/255.0, g/255.0, b/255.0
        max_c = max(r, g, b)
        min_c = min(r, g, b)
        delta = max_c - min_c
        
        # 色相
        if delta == 0:
            h = 0
        elif max_c == r:
            h = ((g - b) / delta) % 6
        elif max_c == g:
            h = ((b - r) / delta) + 2
        else:
            h = ((r - g) / delta) + 4
        h = h / 6.0
        
        # 饱和度
        s = 0 if max_c == 0 else delta / max_c
        
        # 明度
        v = max_c
        
        return h, s, v
    
    def hex_to_rgb(self, hex_color):
        """HEX转RGB"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def rgb_to_hex(self, r, g, b):
        """RGB转HEX"""
        return f'#{r:02x}{g:02x}{b:02x}'
    
    def on_ok(self):
        """确定"""
        if self.callback:
            self.callback(self.selected_color)
        self.destroy()
    
    def on_cancel(self, event=None):
        """取消 - 恢复初始颜色"""
        # 恢复初始颜色
        if self.realtime_callback:
            self.realtime_callback(self.initial_color)
        self.destroy()
