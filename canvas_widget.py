"""
画布组件模块
"""

import tkinter as tk
from tkinter import Canvas
from PIL import Image, ImageTk


class CanvasWidget(tk.Frame):
    """画布组件"""
    
    def __init__(self, parent, width=800, height=600):
        super().__init__(parent)
        self.width = width
        self.height = height
        
        # 创建画布 - 无边距，边框靠边
        self.canvas = Canvas(
            self, 
            width=width, 
            height=height,
            bg='white',
            relief=tk.FLAT,
            borderwidth=0,
            highlightthickness=0
        )
        self.canvas.pack(padx=0, pady=0)
        
        # 存储画布对象
        self.canvas_items = []
        self.main_image_id = None
        self.stickers = []  # 贴纸列表 [{id, x, y, text, size}]
        self.selected_sticker = None
        
        self.dragging_item = None
        self.drag_start_x = 0
        self.drag_start_y = 0
        
        # 缩放和选择状态
        self.selected_item = None  # 当前选中的 Canvas ID
        self.handle_type = None    # 当前拖拽的缩放柄类型 ('nw', 'ne', etc.)
        self.handles = {}          # 存储句柄 ID -> 类型
        
        # 绑定鼠标事件
        self.canvas.bind('<Button-1>', self.on_canvas_click)
        self.canvas.bind('<B1-Motion>', self.on_canvas_drag)
        self.canvas.bind('<ButtonRelease-1>', self.on_canvas_release)
        
        # 绑定右键点击 (兼容 Mac 和 Win/Linux)
        # Mac 触控板双指点击 = Button-2, 鼠标右键 = Button-2 或 Button-3
        self.canvas.bind('<Button-2>', self.show_context_menu)
        self.canvas.bind('<Button-3>', self.show_context_menu)
        self.canvas.bind('<Control-Button-1>', self.show_context_menu)
            
        # 创建右键上下文菜单
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="置于顶层", command=self.move_to_front)
        self.context_menu.add_command(label="置于底层", command=self.move_to_back)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="上移一层", command=self.move_up)
        self.context_menu.add_command(label="下移一层", command=self.move_down)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="删除", command=self.delete_selected_sticker)

    def move_to_front(self):
        """置于顶层 (在图片/贴纸层内，边框之下)"""
        if self.selected_item:
            # 将选中项提升到所有内容层之上
            # 先将其提升到边框之下的最高位置
            all_items = self.canvas.find_all()
            for item in reversed(all_items):
                tags = self.canvas.gettags(item)
                # 找到第一个边框元素，将选中项放在它下面
                if 'border' in tags or 'border_image' in tags:
                    self.canvas.tag_lower(self.selected_item, item)
                    break
            else:
                # 如果没有边框，直接提升到最顶层
                self.canvas.tag_raise(self.selected_item)
            self._ensure_layer_order()

    def move_to_back(self):
        """置于底层 (在图片/贴纸层内)"""
        if self.selected_item:
            self.canvas.tag_lower(self.selected_item, 'main_image')
            self.canvas.tag_lower(self.selected_item, 'sticker')
            self._ensure_layer_order()

    def move_up(self):
        """上移一层"""
        if self.selected_item:
            above = self.canvas.find_above(self.selected_item)
            if above:
                tags = self.canvas.gettags(above)
                # 只能在图片和贴纸之间移动，不能穿透边框
                if 'sticker' in tags or 'main_image' in tags:
                    self.canvas.tag_raise(self.selected_item, above)
            self._ensure_layer_order()

    def move_down(self):
        """下移一层"""
        if self.selected_item:
            below = self.canvas.find_below(self.selected_item)
            if below:
                tags = self.canvas.gettags(below)
                if 'sticker' in tags or 'main_image' in tags:
                    self.canvas.tag_lower(self.selected_item, below)
            self._ensure_layer_order()
    
    def clear_canvas(self):
        """清空画布"""
        self.canvas.delete('all')
        self.canvas_items = []
        self.main_image_id = None
    def _ensure_layer_order(self):
        """统一管理画布图层顺序：背景 < 图案 < 图片 < 贴纸 < 边框 < 手柄"""
        # 按从底到顶的顺序设置
        # 1. 背景最底层
        self.canvas.tag_lower('background_image')
        # 2. 背景图案
        self.canvas.tag_raise('background_pattern', 'background_image')
        # 3. 主图片
        self.canvas.tag_raise('main_image', 'background_pattern')
        # 4. 贴纸
        self.canvas.tag_raise('sticker', 'main_image')
        # 5. 边框 (必须在贴纸之上)
        self.canvas.tag_raise('border', 'sticker')
        self.canvas.tag_raise('border_image', 'border')
        # 6. 手柄 (必须在边框之上才能点击)
        self.canvas.tag_raise('handle')

    def display_image(self, pil_image):
        """显示PIL图片"""
        if not pil_image:
            return
        
        # 保存原始图片引用以便缩放
        self.original_pil_image = pil_image.copy()
        
        # 调整图片大小以适应画布，留出边框空间
        img_width, img_height = pil_image.size
        canvas_ratio = self.width / self.height
        img_ratio = img_width / img_height
        
        # 留出更多边距确保边框可见 (原来是40，改为80)
        margin = 80
        if img_ratio > canvas_ratio:
            new_width = self.width - margin
            new_height = int(new_width / img_ratio)
        else:
            new_height = self.height - margin
            new_width = int(new_height * img_ratio)
        
        # 保存当前显示尺寸
        self.current_display_size = (new_width, new_height)
            
        display_img = pil_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        self.photo = ImageTk.PhotoImage(display_img)
        
        # 删除所有标记为 main_image 的旧对象，确保不叠加
        self.canvas.delete('main_image')
            
        self.main_image_id = self.canvas.create_image(
            self.width // 2, self.height // 2, 
            image=self.photo, 
            anchor=tk.CENTER,
            tags='main_image'
        )
        self.canvas.image = self.photo
        
        # 强制重排图层
        self._ensure_layer_order()
    
    def add_sticker(self, emoji_text, font_size=48):
        """添加贴纸"""
        # 在画布中心添加贴纸
        x = self.width // 2
        y = self.height // 2
        
        sticker_id = self.canvas.create_text(
            x, y,
            text=emoji_text,
            font=('Arial', font_size),
            fill='black',
            tags='sticker'
        )
        
        # 添加到贴纸列表
        sticker_data = {
            'id': sticker_id,
            'x': x,
            'y': y,
            'text': emoji_text,
            'size': font_size
        }
        self.stickers.append(sticker_data)
        
        return sticker_id
    
    def add_border(self, border_style):
        """添加边框 - 统一使用 apply_custom_border"""
        self.apply_custom_border(border_style)
    
    def apply_border_image(self, border_img):
        """应用边框图片 - 直接显示"""
        # 清除旧边框
        self.canvas.delete('border')
        self.canvas.delete('border_image')
        
        try:
            # 调整边框图片大小以适应画布
            border_resized = border_img.resize((self.width, self.height), Image.Resampling.LANCZOS)
            self.border_photo = ImageTk.PhotoImage(border_resized)
            
            # 在画布上绘制边框（在最上层）
            self.canvas.create_image(
                0, 0,
                anchor=tk.NW,
                image=self.border_photo,
                tags='border_image'
            )
            
            # 确保边框在最上层
            self.canvas.tag_raise('border_image')
        except Exception as e:
            print(f"应用边框图片失败: {e}")
    
    def apply_custom_border(self, config):
        """应用自定义边框配置"""
        self.canvas.delete('border')
        self.canvas.delete('border_image')
        
        # shape = config.get('shape', 'rectangle') # 不再需要shape，完全由radius决定
        # shape = config.get('shape', 'rectangle') # 不再需要shape，完全由radius决定
        border_width = config.get('width', 0)
        radius = config.get('radius', 0)
        color = config.get('color', '#000000')
        line_style = config.get('line_style', 'solid')
        pattern = config.get('pattern', 'none')
        
        if border_width <= 0:
            return
        
        # 获取画布实际尺寸
        self.canvas.update_idletasks()
        canvas_w = self.canvas.winfo_width()
        canvas_h = self.canvas.winfo_height()
        
        # 如果获取失败，使用保存的尺寸
        if canvas_w <= 1:
            canvas_w = self.width
        if canvas_h <= 1:
            canvas_h = self.height
        
        # 设置线条样式
        dash_pattern = None
        if line_style == 'dashed':
            dash_pattern = (10, 5)
        elif line_style == 'dotted':
            dash_pattern = (3, 3)
        
        # 统一使用圆角矩形逻辑（支持radius=0即直角，也支持双线）
        if line_style == 'double':
            # 双线边框 (支持圆角)
            outer_width = max(1, border_width // 3)
            inner_width = max(1, border_width // 3)
            gap = border_width - outer_width - inner_width
            
            # 外线
            self.draw_rounded_rectangle(outer_width, radius, color, canvas_w, canvas_h, dash_pattern)
            
            # 内线
            # 内线需要缩小绘制区域，并调整圆角半径
            offset = outer_width + gap
            inner_w = canvas_w - 2 * offset
            inner_h = canvas_h - 2 * offset
            inner_radius = max(0, radius - offset)
            
            # 由于draw_rounded_rectangle默认全画布，这里我们需要临时调整逻辑或传递offset?
            # draw_rounded_rectangle目前没有offset参数。
            # 我们可以直接在该方法外部手动计算坐标调用 self.draw_rounded_rect_at(...) 
            # 或者简单地，为了避免改动太大，我们再次调用 draw_rounded_rectangle 但需要先实现一个带偏移的版本?
            # 实际上 draw_rounded_rectangle 内部是 0,0 到 w,h。
            # 如果我们想画内线，我们最好手动调用绘制逻辑，或者改进 draw_rounded_rectangle。
            
            # 简单起见，既然 draw_rounded_rectangle 比较复杂（画了4条线+4个弧），
            # 不如直接用 offset 绘制内层。
            # 但为了复用代码，我们可以给 draw_rounded_rectangle 增加 offset 参数！
            
            self.draw_rounded_rectangle(inner_width, inner_radius, color, canvas_w, canvas_h, dash_pattern, offset=offset)
            
        else:
            # 普通/虚线/点线边框
            self.draw_rounded_rectangle(border_width, radius, color, canvas_w, canvas_h, dash_pattern)
        
        if pattern and pattern != 'none':
            self.draw_border_pattern(pattern, border_width, canvas_w, canvas_h, config.get('pattern_color', '#FFFFFF'))
            
        self._ensure_layer_order()
    
    def draw_rounded_rectangle(self, border_width, radius, color, canvas_w=None, canvas_h=None, dash_pattern=None, offset=0):
        """绘制圆角矩形边框"""
        # 使用传入的尺寸或默认尺寸
        w = canvas_w if canvas_w else self.width
        h = canvas_h if canvas_h else self.height
        
        # 确保圆角不会太大
        max_radius = min(w, h) // 4
        r = min(radius, max_radius)
        
        # 基础坐标 (应用偏移)
        # x1,y1 是左上角, x2,y2 是右下角
        base_x1, base_y1 = offset, offset
        base_x2, base_y2 = w - 1 - offset, h - 1 - offset
        
        for i in range(border_width):
            x1, y1 = base_x1 + i, base_y1 + i
            x2, y2 = base_x2 - i, base_y2 - i
            
            # 如果圆角为0，直接画矩形
            if r <= 0:
                self.canvas.create_rectangle(x1, y1, x2, y2, outline=color, dash=dash_pattern, tags='border')
                continue
            
            # 绘制四条直线
            # 上边
            self.canvas.create_line(x1 + r, y1, x2 - r, y1, fill=color, dash=dash_pattern, tags='border')
            # 下边
            self.canvas.create_line(x1 + r, y2, x2 - r, y2, fill=color, dash=dash_pattern, tags='border')
            # 左边
            self.canvas.create_line(x1, y1 + r, x1, y2 - r, fill=color, dash=dash_pattern, tags='border')
            # 右边
            self.canvas.create_line(x2, y1 + r, x2, y2 - r, fill=color, dash=dash_pattern, tags='border')
            
            # 绘制四个圆角
            # 左上角
            self.canvas.create_arc(x1, y1, x1 + 2*r, y1 + 2*r, 
                                  start=90, extent=90, style='arc', 
                                  outline=color, tags='border')
            # 右上角
            self.canvas.create_arc(x2 - 2*r, y1, x2, y1 + 2*r, 
                                  start=0, extent=90, style='arc', 
                                  outline=color, tags='border')
            # 左下角
            self.canvas.create_arc(x1, y2 - 2*r, x1 + 2*r, y2, 
                                  start=180, extent=90, style='arc', 
                                  outline=color, tags='border')
            # 右下角
            self.canvas.create_arc(x2 - 2*r, y2 - 2*r, x2, y2, 
                                  start=270, extent=90, style='arc', 
                                  outline=color, tags='border')
    
    def draw_border_pattern(self, pattern, border_width, canvas_w, canvas_h, pattern_color):
        """在边框区域内绘制图案"""
        if not pattern or pattern == 'none' or border_width <= 2:
            return
        
        # 只在边框区域内绘制图案
        bw = border_width
        
        if pattern == 'stripe':
            # 斜纹图案 - 在边框区域内
            spacing = 6
            # 上边框
            for i in range(0, canvas_w, spacing):
                self.canvas.create_line(i, 0, i + bw, bw, fill=pattern_color, tags='border')
            # 下边框
            for i in range(0, canvas_w, spacing):
                self.canvas.create_line(i, canvas_h - bw, i + bw, canvas_h, fill=pattern_color, tags='border')
            # 左边框
            for i in range(bw, canvas_h - bw, spacing):
                self.canvas.create_line(0, i, bw, i + bw, fill=pattern_color, tags='border')
            # 右边框
            for i in range(bw, canvas_h - bw, spacing):
                self.canvas.create_line(canvas_w - bw, i, canvas_w, i + bw, fill=pattern_color, tags='border')
        
        elif pattern == 'dots':
            # 波点图案
            spacing = max(8, bw)
            dot_r = max(2, bw // 4)
            # 上下边框
            for x in range(spacing // 2, canvas_w, spacing):
                self.canvas.create_oval(x - dot_r, bw // 2 - dot_r, x + dot_r, bw // 2 + dot_r,
                                       fill=pattern_color, outline='', tags='border')
                self.canvas.create_oval(x - dot_r, canvas_h - bw // 2 - dot_r, x + dot_r, canvas_h - bw // 2 + dot_r,
                                       fill=pattern_color, outline='', tags='border')
            # 左右边框
            for y in range(bw + spacing // 2, canvas_h - bw, spacing):
                self.canvas.create_oval(bw // 2 - dot_r, y - dot_r, bw // 2 + dot_r, y + dot_r,
                                       fill=pattern_color, outline='', tags='border')
                self.canvas.create_oval(canvas_w - bw // 2 - dot_r, y - dot_r, canvas_w - bw // 2 + dot_r, y + dot_r,
                                       fill=pattern_color, outline='', tags='border')
        
        elif pattern == 'grid':
            # 网格图案 - 使用全局坐标以确保对齐
            spacing = max(6, bw // 2)
            
            # 绘制竖线 (遍历整个宽度)
            for x in range(0, canvas_w, spacing):
                # 只在边框区域绘制
                # 左边框区域 or 右边框区域 or 上下边框区域(不仅是上下边缘,而是整个宽度)
                # 简化逻辑: 
                # 如果x在左边框范围内(<bw) 或 x在右边框范围内(>canvas_w-bw), 则画整条竖线
                # 否则(x在中间), 只能在上下边框高度内画竖线
                
                if x < bw or x > canvas_w - bw:
                    # 左右边框区域: 画整条竖线
                    self.canvas.create_line(x, 0, x, canvas_h, fill=pattern_color, tags='border')
                else:
                    # 中间区域: 只画上下边框的竖线部分
                    self.canvas.create_line(x, 0, x, bw, fill=pattern_color, tags='border')
                    self.canvas.create_line(x, canvas_h - bw, x, canvas_h, fill=pattern_color, tags='border')
            
            # 绘制横线 (遍历整个高度)
            for y in range(0, canvas_h, spacing):
                # 逻辑同上
                if y < bw or y > canvas_h - bw:
                    # 上下边框区域: 画整条横线
                    self.canvas.create_line(0, y, canvas_w, y, fill=pattern_color, tags='border')
                else:
                    # 中间区域: 只画左右边框的横线部分
                    self.canvas.create_line(0, y, bw, y, fill=pattern_color, tags='border')
                    self.canvas.create_line(canvas_w - bw, y, canvas_w, y, fill=pattern_color, tags='border')

        elif pattern == 'wave':
            # 波浪图案
            import math
            
            amplitude = max(2, bw / 4)
            wavelength = max(10, bw * 2)
            
            # 上边框
            points = []
            for x in range(0, canvas_w, 2):
                y = bw / 2 + amplitude * math.sin(x / wavelength * 2 * math.pi)
                points.append(x)
                points.append(y)
            if len(points) >= 4:
                self.canvas.create_line(points, fill=pattern_color, smooth=True, tags='border')
            
            # 下边框
            points = []
            for x in range(0, canvas_w, 2):
                y = canvas_h - bw / 2 + amplitude * math.sin(x / wavelength * 2 * math.pi)
                points.append(x)
                points.append(y)
            if len(points) >= 4:
                self.canvas.create_line(points, fill=pattern_color, smooth=True, tags='border')
            
            # 左边框
            points = []
            for y in range(0, canvas_h, 2):
                x = bw / 2 + amplitude * math.sin(y / wavelength * 2 * math.pi)
                points.append(x)
                points.append(y)
            if len(points) >= 4:
                self.canvas.create_line(points, fill=pattern_color, smooth=True, tags='border')
            
            # 右边框
            points = []
            for y in range(0, canvas_h, 2):
                x = canvas_w - bw / 2 + amplitude * math.sin(y / wavelength * 2 * math.pi)
                points.append(x)
                points.append(y)
            if len(points) >= 4:
                self.canvas.create_line(points, fill=pattern_color, smooth=True, tags='border')
    
    def set_background_color(self, color):
        """设置画布背景色"""
        self.canvas.config(bg=color)
        # 清除背景图案
        self.canvas.delete('background_pattern')
    
    def set_background_image(self, img):
        """设置背景图片"""
        try:
            bg_resized = img.resize((self.width, self.height), Image.Resampling.LANCZOS)
            self.bg_photo = ImageTk.PhotoImage(bg_resized)
            
            # 删除旧背景
            self.canvas.delete('background_image')
            self.canvas.delete('background_pattern')
            
            # 添加新背景（在最底层）
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.bg_photo, tags='background_image')
            self.canvas.tag_lower('background_image')
        except Exception as e:
            print(f"设置背景图片失败: {e}")
    
    def set_background_pattern(self, pattern_id, bg_color, pattern_color, pattern_size=10):
        """设置背景图案"""
        # 先清除旧图案
        self.canvas.delete('background_pattern')
        self.canvas.config(bg=bg_color)
        
        canvas_w = self.canvas.winfo_width()
        canvas_h = self.canvas.winfo_height()
        if canvas_w <= 1:
            canvas_w = self.width
        if canvas_h <= 1:
            canvas_h = self.height
        
        if pattern_id == 'none' or not pattern_id:
            return
        
        if pattern_id == 'stripe':
            # 斜纹图案
            spacing = pattern_size * 2
            for i in range(-canvas_h, canvas_w + canvas_h, spacing):
                self.canvas.create_line(
                    i, 0, i + canvas_h, canvas_h,
                    fill=pattern_color, width=1, tags='background_pattern'
                )
        
        elif pattern_id == 'dots':
            # 波点图案
            spacing = pattern_size * 2
            dot_radius = pattern_size // 3
            for y in range(0, canvas_h + spacing, spacing):
                offset = (y // spacing) % 2 * (spacing // 2)
                for x in range(offset, canvas_w + spacing, spacing):
                    self.canvas.create_oval(
                        x - dot_radius, y - dot_radius,
                        x + dot_radius, y + dot_radius,
                        fill=pattern_color, outline='', tags='background_pattern'
                    )
        
        elif pattern_id == 'grid':
            # 网格图案
            spacing = pattern_size * 2
            for x in range(0, canvas_w, spacing):
                self.canvas.create_line(
                    x, 0, x, canvas_h,
                    fill=pattern_color, width=1, tags='background_pattern'
                )
            for y in range(0, canvas_h, spacing):
                self.canvas.create_line(
                    0, y, canvas_w, y,
                    fill=pattern_color, width=1, tags='background_pattern'
                )
        
        elif pattern_id == 'horizontal':
            # 横线图案
            spacing = pattern_size * 2
            for y in range(0, canvas_h, spacing):
                self.canvas.create_line(
                    0, y, canvas_w, y,
                    fill=pattern_color, width=1, tags='background_pattern'
                )
        
        elif pattern_id == 'vertical':
            # 竖线图案
            spacing = pattern_size * 2
            for x in range(0, canvas_w, spacing):
                self.canvas.create_line(
                    x, 0, x, canvas_h,
                    fill=pattern_color, width=1, tags='background_pattern'
                )
        
        # 确保图层顺序：背景 < 图案 < 图片 < 贴纸 < 边框
        self._ensure_layer_order()
    
    def _create_scaling_handles(self, item_id):
        """为指定的对象创建缩放柄"""
        self._hide_scaling_handles()
        self.selected_item = item_id
        
        # 使用 bbox() 获取边界框 (x1, y1, x2, y2)
        # 注意：coords() 对于图片只返回中心点，不能用于此处
        bbox = self.canvas.bbox(item_id)
        if not bbox:
            return
        x1, y1, x2, y2 = bbox
        
        # 定义 8 个位置
        handle_positions = {
            'nw': (x1, y1), 'n': ((x1+x2)/2, y1), 'ne': (x2, y1),
            'w': (x1, (y1+y2)/2), 'e': (x2, (y1+y2)/2),
            'sw': (x1, y2), 's': ((x1+x2)/2, y2), 'se': (x2, y2)
        }
        
        for h_type, (hx, hy) in handle_positions.items():
            h_id = self.canvas.create_rectangle(
                hx-5, hy-5, hx+5, hy+5,
                fill='#3B82F6', outline='white', width=2, tags='handle'
            )
            self.handles[h_id] = h_type
        
        # 确保手柄在最顶层
        self.canvas.tag_raise('handle')
            
    def _update_scaling_handles(self):
        """更新缩放柄位置"""
        if not self.selected_item or not self.handles:
            return
        
        bbox = self.canvas.bbox(self.selected_item)
        if not bbox:
            return
        x1, y1, x2, y2 = bbox
        
        handle_positions = {
            'nw': (x1, y1), 'n': ((x1+x2)/2, y1), 'ne': (x2, y1),
            'w': (x1, (y1+y2)/2), 'e': (x2, (y1+y2)/2),
            'sw': (x1, y2), 's': ((x1+x2)/2, y2), 'se': (x2, y2)
        }
        
        for h_id, h_type in self.handles.items():
            hx, hy = handle_positions[h_type]
            self.canvas.coords(h_id, hx-4, hy-4, hx+4, hy+4)
            self.canvas.tag_raise(h_id)

    def _hide_scaling_handles(self):
        """隐藏/删除缩放柄"""
        self.canvas.delete('handle')
        self.handles = {}
        # 注意: 这里不清除 selected_item，因为可能只是取消显示手柄但仍保留选中状态

    def show_context_menu(self, event):
        """显示右键菜单"""
        # 查找下方对象
        item = self.canvas.find_closest(event.x, event.y)[0]
        tags = self.canvas.gettags(item)
        
        if 'main_image' in tags or 'sticker' in tags:
            self.selected_item = item
            # 根据类型调整菜单项（可选）
            self.context_menu.post(event.x_root, event.y_root)

    def move_to_front(self):
        """置于顶层"""
        if self.selected_item:
            self.canvas.tag_raise(self.selected_item)
            # 维持边框始终在最前的逻辑
            self._ensure_layer_order()

    def move_to_back(self):
        """置于底层"""
        if self.selected_item:
            self.canvas.tag_lower(self.selected_item)
            # 维持背景始终在最后的逻辑
            self._ensure_layer_order()

    def on_canvas_click(self, event):
        """画布点击事件 - 增强识别逻辑"""
        # 1. 优先识别缩放手柄 (Handle)
        # 我们使用 find_closest 并限制距离，这比 find_overlapping 在大图层重叠时更可靠
        closest_items = self.canvas.find_closest(event.x, event.y, halo=3)
        if closest_items:
            item = closest_items[0]
            if item in self.handles:
                self.handle_type = self.handles[item]
                self.drag_start_x = event.x
                self.drag_start_y = event.y
                return

        # 2. 识别贴纸或图片
        # 按从上到下的顺序查找
        items = self.canvas.find_overlapping(event.x - 2, event.y - 2, event.x + 2, event.y + 2)
        for item in reversed(items):
            tags = self.canvas.gettags(item)
            if 'sticker' in tags or 'main_image' in tags:
                self.selected_item = item
                self.dragging_item = item
                self.drag_start_x = event.x
                self.drag_start_y = event.y
                
                if 'sticker' in tags:
                    self.selected_sticker = item
                else:
                    self.selected_sticker = None
                
                # 创建缩放柄并置顶
                self._create_scaling_handles(item)
                self._update_scaling_handles()
                return
        
        # 3. 点击空白处
        self._hide_scaling_handles()
        self.selected_item = None
        self.selected_sticker = None
    
    def on_canvas_drag(self, event):
        """画布拖拽事件"""
        dx = event.x - self.drag_start_x
        dy = event.y - self.drag_start_y
        
        # 1. 处理缩放
        if self.handle_type and self.selected_item:
            tags = self.canvas.gettags(self.selected_item)
            
            if 'sticker' in tags:
                # 贴纸缩放：通过调整字体大小
                for sticker in self.stickers:
                    if sticker['id'] == self.selected_item:
                        current_size = sticker['size']
                        if 's' in self.handle_type or 'e' in self.handle_type:
                            size_delta = max(dx, dy) // 3
                        else:
                            size_delta = -max(-dx, -dy) // 3
                        
                        new_size = max(12, min(200, current_size + size_delta))
                        sticker['size'] = new_size
                        self.canvas.itemconfigure(self.selected_item, font=('Arial', new_size))
                        break
            elif 'main_image' in tags:
                # 图片缩放：重新渲染图片
                if hasattr(self, 'original_pil_image') and hasattr(self, 'current_display_size'):
                    cur_w, cur_h = self.current_display_size
                    
                    # 根据拖拽方向计算新尺寸
                    if 'e' in self.handle_type or 's' in self.handle_type:
                        scale_factor = 1 + max(dx, dy) / 200
                    else:
                        scale_factor = 1 - max(-dx, -dy) / 200
                    
                    scale_factor = max(0.3, min(3.0, scale_factor))  # 限制缩放范围
                    
                    new_w = max(50, int(cur_w * scale_factor))
                    new_h = max(50, int(cur_h * scale_factor))
                    
                    # 重新渲染图片
                    display_img = self.original_pil_image.resize((new_w, new_h), Image.Resampling.LANCZOS)
                    self.photo = ImageTk.PhotoImage(display_img)
                    self.canvas.itemconfigure(self.main_image_id, image=self.photo)
                    self.canvas.image = self.photo
                    
                    # 更新当前显示尺寸
                    self.current_display_size = (new_w, new_h)
            
            self._update_scaling_handles()
            self.drag_start_x = event.x
            self.drag_start_y = event.y
            return

        # 2. 处理平移
        if self.dragging_item:
            # 移动对象
            self.canvas.move(self.dragging_item, dx, dy)
            self._update_scaling_handles()
            
            # 更新起始位置
            self.drag_start_x = event.x
            self.drag_start_y = event.y
            
            # 更新贴纸数据
            for sticker in self.stickers:
                if sticker['id'] == self.dragging_item:
                    coords = self.canvas.coords(sticker['id'])
                    if len(coords) == 2:
                        sticker['x'], sticker['y'] = coords
                    break
    
    def on_canvas_release(self, event):
        """画布释放事件"""
        self.dragging_item = None
        self.handle_type = None
    
    def delete_selected_sticker(self):
        """删除选中的贴纸"""
        if self.selected_sticker:
            self.canvas.delete(self.selected_sticker)
            self.stickers = [s for s in self.stickers if s['id'] != self.selected_sticker]
            self.selected_sticker = None
            return True
        return False
    
    def get_stickers(self):
        """获取所有贴纸信息"""
        return self.stickers.copy()
    
    def resize_canvas(self, width, height):
        """调整画布大小"""
        if self.width == 0 or self.height == 0:
            scale_x = 1
            scale_y = 1
        else:
            scale_x = width / self.width
            scale_y = height / self.height
            
        self.width = width
        self.height = height
        self.canvas.config(width=width, height=height)
        
        # 调整贴纸位置和大小
        for sticker in self.stickers:
            sticker['x'] = int(sticker['x'] * scale_x)
            sticker['y'] = int(sticker['y'] * scale_y)
            # 字体大小取平均缩放比例
            scale_avg = (scale_x + scale_y) / 2
            sticker['size'] = int(sticker['size'] * scale_avg)
            
            # 更新画布上的对象
            self.canvas.coords(sticker['id'], sticker['x'], sticker['y'])
            self.canvas.itemconfigure(sticker['id'], font=('Arial', sticker['size']))
            
        # 清除旧边框（将在重新应用时绘制新边框）
        self.canvas.delete('border')
        self.canvas.delete('border_image')
        # 强制更新
        self.canvas.update_idletasks()
