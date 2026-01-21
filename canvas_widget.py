"""
画布组件模块
"""

import tkinter as tk
from tkinter import Canvas
from PIL import Image, ImageTk, ImageDraw, ImageFont
import math
import os
import platform
from constants import COLORS, DASH_PATTERNS


class CanvasWidget(tk.Frame):
    """画布组件"""
    
    def __init__(self, parent, width=800, height=600):
        super().__init__(parent, bg=COLORS['bg'])
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
        self.canvas.pack(padx=0, pady=0, expand=True)
        
        # 存储画布对象
        self.canvas_items = []
        self.main_image_id = None
        self.stickers = []  # 贴纸列表 [{id, x, y, text, size, is_image}]
        self.selected_sticker = None
        self.sticker_photo_refs = []  # 保持图片引用，防止被垃圾回收
        
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
            self.canvas.tag_lower(self.selected_item, 'text_layer')
            # 确保在背景图案之上
            self.canvas.tag_raise(self.selected_item, 'background_pattern')
            self._ensure_layer_order()

    def move_up(self):
        """上移一层"""
        if self.selected_item:
            above = self.canvas.find_above(self.selected_item)
            if above:
                tags = self.canvas.gettags(above)
                # 只能在图片和贴纸之间移动，不能穿透边框
                if 'sticker' in tags or 'main_image' in tags or 'text_layer' in tags:
                    self.canvas.tag_raise(self.selected_item, above)
            self._ensure_layer_order()

    def move_down(self):
        """下移一层"""
        if self.selected_item:
            below = self.canvas.find_below(self.selected_item)
            if below:
                tags = self.canvas.gettags(below)
                if 'sticker' in tags or 'main_image' in tags or 'text_layer' in tags:
                    self.canvas.tag_lower(self.selected_item, below)
            self._ensure_layer_order()
    
    def clear_canvas(self):
        """清空画布"""
        self.canvas.delete('all')
        self.canvas_items = []
        self.main_image_id = None
    def _ensure_layer_order(self):
        """统一管理画布图层顺序：图案 < 背景 < 图片 < 贴纸 < 边框 < 手柄"""
        # 按从底到顶的顺序设置
        # 1. 背景图案在最底层（如果存在）
        if self.canvas.find_withtag('background_pattern'):
            self.canvas.tag_lower('background_pattern')
        
        # 2. 背景图片在图案之上
        if self.canvas.find_withtag('background_image'):
            if self.canvas.find_withtag('background_pattern'):
                self.canvas.tag_raise('background_image', 'background_pattern')
            else:
                self.canvas.tag_lower('background_image')
        
        # 3. 主图片在背景之上
        if self.canvas.find_withtag('main_image'):
            if self.canvas.find_withtag('background_image'):
                self.canvas.tag_raise('main_image', 'background_image')
            elif self.canvas.find_withtag('background_pattern'):
                self.canvas.tag_raise('main_image', 'background_pattern')
            else:
                self.canvas.tag_lower('main_image')
        
        # 4. 贴纸/文字层
        if self.canvas.find_withtag('sticker'):
            if self.canvas.find_withtag('main_image'):
                self.canvas.tag_raise('sticker', 'main_image')
            elif self.canvas.find_withtag('background_image'):
                self.canvas.tag_raise('sticker', 'background_image')
        
        if self.canvas.find_withtag('text_layer'):
            if self.canvas.find_withtag('sticker'):
                self.canvas.tag_raise('text_layer', 'sticker')
            elif self.canvas.find_withtag('main_image'):
                self.canvas.tag_raise('text_layer', 'main_image')
            elif self.canvas.find_withtag('background_image'):
                self.canvas.tag_raise('text_layer', 'background_image')
        
        # 5. 角落遮罩
        if self.canvas.find_withtag('corner_mask'):
            if self.canvas.find_withtag('text_layer'):
                self.canvas.tag_raise('corner_mask', 'text_layer')
            elif self.canvas.find_withtag('sticker'):
                self.canvas.tag_raise('corner_mask', 'sticker')
            elif self.canvas.find_withtag('main_image'):
                self.canvas.tag_raise('corner_mask', 'main_image')
        
        # 6. 边框 (必须在所有内容之上)
        if self.canvas.find_withtag('border'):
            if self.canvas.find_withtag('corner_mask'):
                self.canvas.tag_raise('border', 'corner_mask')
            elif self.canvas.find_withtag('text_layer'):
                self.canvas.tag_raise('border', 'text_layer')
            elif self.canvas.find_withtag('sticker'):
                self.canvas.tag_raise('border', 'sticker')
        
        if self.canvas.find_withtag('border_image'):
            # Pattern should be ON TOP of the border lines
            if self.canvas.find_withtag('border'):
                self.canvas.tag_raise('border_image', 'border')
            
            # But BELOW corner mask
            if self.canvas.find_withtag('corner_mask'):
                self.canvas.tag_lower('border_image', 'corner_mask')
        
        # 7. 手柄 (必须在边框之上才能点击)
        if self.canvas.find_withtag('handle'):
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
    
    def clear_main_image(self):
        """清除主图片"""
        self.canvas.delete('main_image')
        self.main_image_id = None
        self.photo = None
        self.original_pil_image = None
        self.current_display_size = None
    
    def _get_emoji_font(self, font_size):
        """获取跨平台的彩色 emoji 字体"""
        system = platform.system()
        emoji_font_paths = []
        
        if system == 'Darwin':  # macOS
            emoji_font_paths = [
                '/System/Library/Fonts/Apple Color Emoji.ttc',
                '/System/Library/Fonts/Supplemental/Apple Color Emoji.ttc',
            ]
        elif system == 'Windows':  # Windows
            emoji_font_paths = [
                'C:/Windows/Fonts/seguiemj.ttf',  # Segoe UI Emoji
            ]
        elif system == 'Linux':  # Linux
            emoji_font_paths = [
                '/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf',
            ]
        
        for font_path in emoji_font_paths:
            if os.path.exists(font_path):
                try:
                    return ImageFont.truetype(font_path, font_size)
                except:
                    continue
        return None
    
    def _render_emoji_image(self, emoji_text, size):
        """将emoji渲染为彩色图片"""
        # 尝试使用PNG文件
        assets_dir = os.path.join(os.path.dirname(__file__), 'assets', 'stickers')
        # 从emoji文本映射到文件名
        emoji_to_file = {
            '❤️': 'heart.png', '⭐': 'star.png', '😊': 'smile.png', '🔥': 'fire.png',
            '✨': 'sparkles.png', '🌸': 'flower.png', '👑': 'crown.png', '🎀': 'ribbon.png',
            '🎂': 'cake.png', '🎁': 'gift.png', '🎈': 'balloon.png', '🎵': 'music.png',
        }
        
        if emoji_text in emoji_to_file:
            png_path = os.path.join(assets_dir, emoji_to_file[emoji_text])
            if os.path.exists(png_path):
                try:
                    img = Image.open(png_path).convert('RGBA')
                    img = img.resize((size, size), Image.Resampling.LANCZOS)
                    return img
                except Exception as e:
                    print(f"[DEBUG] 加载PNG贴纸失败: {e}")
        
        # 使用字体渲染彩色emoji
        font = self._get_emoji_font(size * 2)  # 使用更大的字体以获得更好的质量
        if font:
            try:
                temp_size = size * 3
                emoji_temp = Image.new('RGBA', (temp_size, temp_size), (0, 0, 0, 0))
                emoji_draw = ImageDraw.Draw(emoji_temp)
                emoji_draw.text((temp_size // 2, temp_size // 2), emoji_text, 
                              font=font, anchor="mm", embedded_color=True)
                
                # 裁剪到实际内容
                bbox = emoji_temp.getbbox()
                if bbox:
                    emoji_cropped = emoji_temp.crop(bbox)
                    # 调整大小
                    if emoji_cropped.width != size or emoji_cropped.height != size:
                        emoji_cropped = emoji_cropped.resize((size, size), Image.Resampling.LANCZOS)
                    return emoji_cropped
            except Exception as e:
                print(f"[DEBUG] 渲染emoji失败: {e}")
        
        # 降级方案：返回None，使用文本显示
        return None
    
    def add_sticker(self, emoji_text, font_size=48, sticker_id=None):
        """添加贴纸（支持彩色显示）"""
        import random
        
        # 贴纸默认放置在四角边框内侧位置
        margin = font_size + 30  # 边框内侧留出边距
        
        # 四个角落的位置（按顺序：左下、右下、左上、右上）
        corners = [
            (margin, self.height - margin),  # 左下
            (self.width - margin, self.height - margin),  # 右下
            (margin, margin),  # 左上
            (self.width - margin, margin),  # 右上
        ]
        
        # 按贴纸数量循环选择角落
        corner_index = len(self.stickers) % 4
        base_x, base_y = corners[corner_index]
        
        # 添加小偏移避免完全重叠
        offset_x = random.randint(-15, 15)
        offset_y = random.randint(-15, 15)
        x = max(margin, min(self.width - margin, base_x + offset_x))
        y = max(margin, min(self.height - margin, base_y + offset_y))
        
        # 尝试渲染为彩色图片
        emoji_img = self._render_emoji_image(emoji_text, font_size)
        
        if emoji_img:
            # 使用图片显示（彩色）
            photo = ImageTk.PhotoImage(emoji_img)
            self.sticker_photo_refs.append(photo)  # 保持引用
            
            sticker_id = self.canvas.create_image(
                x, y,
                image=photo,
                anchor=tk.CENTER,
                tags='sticker'
            )
        else:
            # 降级方案：使用文本显示（黑白）
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
            'size': font_size,
            'is_image': emoji_img is not None
        }
        self.stickers.append(sticker_data)
        
        return sticker_id
    
    def add_sticker_image(self, img, size=96, category=None, image_path=None, x=None, y=None):
        """直接添加PNG图片作为贴纸"""
        import random
        
        # 如果未指定坐标，则计算默认位置
        if x is None or y is None:
            # 贴纸默认放置在四角边框内侧位置
            margin = size + 30  # 边框内侧留出边距
            
            # 四个角落的位置（按顺序：左下、右下、左上、右上）
            corners = [
                (margin, self.height - margin),  # 左下
                (self.width - margin, self.height - margin),  # 右下
                (margin, margin),  # 左上
                (self.width - margin, margin),  # 右上
            ]
            
            # 按贴纸数量循环选择角落
            corner_index = len(self.stickers) % 4
            base_x, base_y = corners[corner_index]
            
            # 添加小偏移避免完全重叠
            offset_x = random.randint(-15, 15)
            offset_y = random.randint(-15, 15)
            
            if x is None:
                x = max(margin, min(self.width - margin, base_x + offset_x))
            if y is None:
                y = max(margin, min(self.height - margin, base_y + offset_y))
        
        # 使用图片显示
        photo = ImageTk.PhotoImage(img)
        self.sticker_photo_refs.append(photo)  # 保持引用
        
        sticker_id = self.canvas.create_image(
            x, y,
            image=photo,
            anchor=tk.CENTER,
            tags='sticker'
        )
        
        # 添加到贴纸列表
        sticker_data = {
            'id': sticker_id,
            'x': x,
            'y': y,
            'text': '',  # PNG图片没有文本
            'size': size,
            'is_image': True,
            'image': img,  # 保存原始图片对象 (非序列化)
            'category': category,  # 保存分类信息
            'image_path': image_path # 保存文件路径 (用于序列化保存设置)
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
        self.canvas.delete('corner_mask') # 清除旧遮罩
        
        border_width = config.get('width', 0)
        radius = config.get('radius', 0)
        color = config.get('color', '#000000')
        line_style = config.get('line_style', 'solid')
        pattern = config.get('pattern', 'none')
        
        # 始终绘制遮罩以模拟画布圆角（即使没有边框宽度，只要有圆角）
        # 如果边框宽度>0，遮罩在边框下；如果不画边框但有圆角，也需要遮罩
        if radius > 0:
            # 遮罩颜色应为 APP背景色，以模拟透明
            mask_color = COLORS['bg']
            # 我们需要获取画布当前尺寸
            self.canvas.update_idletasks()
            w = self.canvas.winfo_width() 
            h = self.canvas.winfo_height()
            if w <= 1: w = self.width
            if h <= 1: h = self.height
            
            self.draw_corner_masks(radius, mask_color, w, h)
        
        if border_width <= 0:
            self._ensure_layer_order()
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
        
        # Setting line style
        dash_pattern = None
        if line_style in DASH_PATTERNS:
            dash_pattern = DASH_PATTERNS[line_style]
        
        # For non-solid line styles, use PIL-based rendering to match Export
        if line_style in ('dashed', 'dotted', 'double'):
            self._draw_pil_styled_border(border_width, radius, color, line_style, canvas_w, canvas_h)
        else:
            # Solid border - use native Tkinter for performance
            self.draw_rounded_rectangle(border_width, radius, color, canvas_w, canvas_h, dash_pattern)
        
        if pattern and pattern != 'none':
            pattern_size = config.get('pattern_size', 10)
            self.draw_border_pattern(pattern, border_width, canvas_w, canvas_h, config.get('pattern_color', '#FFFFFF'), pattern_size)
            
        self._ensure_layer_order()

    def _draw_pil_styled_border(self, border_width, radius, color, line_style, canvas_w, canvas_h):
        """使用 PIL 绘制样式化边框，以匹配导出效果"""
        from PIL import Image, ImageDraw
        
        # Create transparent image for border
        border_img = Image.new('RGBA', (canvas_w, canvas_h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(border_img)
        
        x1, y1, x2, y2 = 0, 0, canvas_w - 1, canvas_h - 1
        width = border_width
        
        if line_style == 'dashed':
            # Diagonal parallelograms (matching CompositeImage._draw_styled_rect)
            dash_w = width * 1.0
            gap_w = width * 0.5
            period = dash_w + gap_w
            
            # Top
            for x in range(int(x1+radius), int(x2-radius), int(period)):
                if x + dash_w > x2 - radius:
                    continue
                points = [
                    (x, y1+width),
                    (x + width, y1),
                    (x + width + dash_w, y1),
                    (x + dash_w, y1 + width)
                ]
                draw.polygon(points, fill=color)
            
            # Bottom
            for x in range(int(x1+radius), int(x2-radius), int(period)):
                if x + dash_w > x2 - radius:
                    continue
                points = [
                    (x, y2),
                    (x + width, y2 - width),
                    (x + width + dash_w, y2 - width),
                    (x + dash_w, y2)
                ]
                draw.polygon(points, fill=color)
            
            # Left
            for y in range(int(y1+radius), int(y2-radius), int(period)):
                if y + dash_w > y2 - radius:
                    continue
                points = [
                    (x1, y + width),
                    (x1 + width, y),
                    (x1 + width, y + dash_w),
                    (x1, y + width + dash_w)
                ]
                draw.polygon(points, fill=color)
            
            # Right
            for y in range(int(y1+radius), int(y2-radius), int(period)):
                if y + dash_w > y2 - radius:
                    continue
                points = [
                    (x2 - width, y + width),
                    (x2, y),
                    (x2, y + dash_w),
                    (x2 - width, y + width + dash_w)
                ]
                draw.polygon(points, fill=color)
            
            # Corners (solid arcs)
            if radius > 0:
                draw.arc([x1, y1, x1+2*radius, y1+2*radius], 180, 270, fill=color, width=width)
                draw.arc([x2-2*radius, y1, x2, y1+2*radius], 270, 0, fill=color, width=width)
                draw.arc([x2-2*radius, y2-2*radius, x2, y2], 0, 90, fill=color, width=width)
                draw.arc([x1, y2-2*radius, x1+2*radius, y2], 90, 180, fill=color, width=width)
        
        elif line_style == 'dotted':
            # Draw ellipses along border
            dot_radius = max(width // 2, 3)
            dot_spacing = max(width, 10)
            
            # Top edge
            for x in range(int(x1 + radius + dot_radius), int(x2 - radius - dot_radius), dot_spacing):
                draw.ellipse([x - dot_radius, y1, x + dot_radius, y1 + width], fill=color)
            # Bottom edge
            for x in range(int(x1 + radius + dot_radius), int(x2 - radius - dot_radius), dot_spacing):
                draw.ellipse([x - dot_radius, y2 - width, x + dot_radius, y2], fill=color)
            # Left edge
            for y in range(int(y1 + radius + dot_radius), int(y2 - radius - dot_radius), dot_spacing):
                draw.ellipse([x1, y - dot_radius, x1 + width, y + dot_radius], fill=color)
            # Right edge
            for y in range(int(y1 + radius + dot_radius), int(y2 - radius - dot_radius), dot_spacing):
                draw.ellipse([x2 - width, y - dot_radius, x2, y + dot_radius], fill=color)
            
            # Corners
            if radius > 0:
                draw.arc([x1, y1, x1+2*radius, y1+2*radius], 180, 270, fill=color, width=width)
                draw.arc([x2-2*radius, y1, x2, y1+2*radius], 270, 0, fill=color, width=width)
                draw.arc([x2-2*radius, y2-2*radius, x2, y2], 0, 90, fill=color, width=width)
                draw.arc([x1, y2-2*radius, x1+2*radius, y2], 90, 180, fill=color, width=width)
        
        elif line_style == 'double':
            # Two parallel rectangles
            outer_width = max(1, width // 3)
            inner_width = max(1, width // 3)
            gap = width - outer_width - inner_width
            
            # Outer line
            if radius > 0:
                draw.rounded_rectangle([x1, y1, x2, y2], radius=radius, outline=color, width=outer_width)
            else:
                draw.rectangle([x1, y1, x2, y2], outline=color, width=outer_width)
            
            # Inner line
            offset = outer_width + gap
            inner_radius = max(0, radius - offset)
            if inner_radius > 0:
                draw.rounded_rectangle([x1+offset, y1+offset, x2-offset, y2-offset], radius=inner_radius, outline=color, width=inner_width)
            else:
                draw.rectangle([x1+offset, y1+offset, x2-offset, y2-offset], outline=color, width=inner_width)
        
        # Display the PIL image on the canvas
        self.border_style_photo = ImageTk.PhotoImage(border_img)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.border_style_photo, tags='border')

    def draw_corner_masks(self, radius, color, w, h):
        """绘制角落遮罩以模拟圆角"""
        # 确保圆角不超限
        r = min(radius, min(w, h) // 2)
        if r <= 0: return

        # 定义四个角的遮罩多边形
        # 每个遮罩是一个覆盖角区域的多边形，但在圆角处是内凹的
        
        # 辅助函数：生成圆弧点
        def get_arc_points(cx, cy, r, start_angle, end_angle, steps=10):
            points = []
            for i in range(steps + 1):
                angle = math.radians(start_angle + (end_angle - start_angle) * i / steps)
                px = cx + r * math.cos(angle)
                py = cy + r * math.sin(angle)
                points.append(px)
                points.append(py)
            return points

        # 左上角
        # 路径: (0,0) -> (r,0) -> arc to (0,r) -> (0,0)
        # 注意: Canvas坐标系y向下
        # 圆心(r,r), 角度从270(上)到180(左) -> 逆时针? 
        # sin(270)=-1, cos(270)=0 -> (r, 0)
        # sin(180)=0, cos(180)=-1 -> (0, r)
        tl_points = [0, 0, r, 0] + get_arc_points(r, r, r, 270, 180) + [0, r]
        self.canvas.create_polygon(tl_points, fill=color, outline=color, tags='corner_mask')

        # 右上角
        # (w,0) -> (w,r) -> arc to (w-r,0) -> (w,0)
        # 圆心(w-r, r)
        # angles: 0(右)到270(上)?
        # cos(0)=1 -> w, sin(0)=0 -> r. -> (w,r) (Right point)
        # cos(270)=0 -> w-r, sin(270)=-1 -> 0. -> (w-r, 0) (Top point)
        tr_points = [w, 0, w, r] + get_arc_points(w-r, r, r, 0, -90) + [w-r, 0]
        self.canvas.create_polygon(tr_points, fill=color, outline=color, tags='corner_mask')
        
        # 右下角
        # (w,h) -> (w-r,h) -> arc to (w,h-r) -> (w,h)
        # 圆心(w-r, h-r)
        # angles: 90(下)到0(右)
        br_points = [w, h, w-r, h] + get_arc_points(w-r, h-r, r, 90, 0) + [w, h-r]
        self.canvas.create_polygon(br_points, fill=color, outline=color, tags='corner_mask')

        # 左下角
        # (0,h) -> (0,h-r) -> arc to (r,h) -> (0,h)
        # 圆心(r, h-r)
        # angles: 180(左)到90(下)
        bl_points = [0, h, 0, h-r] + get_arc_points(r, h-r, r, 180, 90) + [r, h]
        self.canvas.create_polygon(bl_points, fill=color, outline=color, tags='corner_mask')
    
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
    
    def draw_border_pattern(self, pattern, border_width, canvas_w, canvas_h, pattern_color, pattern_size=10):
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
                self.canvas.create_line(i, 0, i + bw, bw, fill=pattern_color, tags='border_image')
            # 下边框
            for i in range(0, canvas_w, spacing):
                self.canvas.create_line(i, canvas_h - bw, i + bw, canvas_h, fill=pattern_color, tags='border_image')
            # 左边框
            for i in range(bw, canvas_h - bw, spacing):
                self.canvas.create_line(0, i, bw, i + bw, fill=pattern_color, tags='border_image')
            # 右边框
            for i in range(bw, canvas_h - bw, spacing):
                self.canvas.create_line(canvas_w - bw, i, canvas_w, i + bw, fill=pattern_color, tags='border_image')
        
        elif pattern == 'dots':
            # 波点图案
            spacing = max(8, bw)
            dot_r = max(2, bw // 4)
            # 上下边框
            for x in range(spacing // 2, canvas_w, spacing):
                self.canvas.create_oval(x - dot_r, bw // 2 - dot_r, x + dot_r, bw // 2 + dot_r,
                                       fill=pattern_color, outline='', tags='border_image')
                self.canvas.create_oval(x - dot_r, canvas_h - bw // 2 - dot_r, x + dot_r, canvas_h - bw // 2 + dot_r,
                                       fill=pattern_color, outline='', tags='border_image')
            # 左右边框
            for y in range(bw + spacing // 2, canvas_h - bw, spacing):
                self.canvas.create_oval(bw // 2 - dot_r, y - dot_r, bw // 2 + dot_r, y + dot_r,
                                       fill=pattern_color, outline='', tags='border_image')
                self.canvas.create_oval(canvas_w - bw // 2 - dot_r, y - dot_r, canvas_w - bw // 2 + dot_r, y + dot_r,
                                       fill=pattern_color, outline='', tags='border_image')
        
        elif pattern == 'grid':
            # 网格图案 - 使用与导出相同的间距公式
            spacing = max(pattern_size, 6)
            if pattern_size > 10: spacing = pattern_size
            
            # 绘制竖线 (遍历整个宽度)
            for x in range(0, canvas_w, spacing):
                # 只在边框区域绘制
                # 左边框区域 or 右边框区域 or 上下边框区域(不仅是上下边缘,而是整个宽度)
                # 简化逻辑: 
                # 如果x在左边框范围内(<bw) 或 x在右边框范围内(>canvas_w-bw), 则画整条竖线
                # 否则(x在中间), 只能在上下边框高度内画竖线
                
                if x < bw or x > canvas_w - bw:
                    # 左右边框区域: 画整条竖线
                    self.canvas.create_line(x, 0, x, canvas_h, fill=pattern_color, tags='border_image')
                else:
                    # 中间区域: 只画上下边框的竖线部分
                    self.canvas.create_line(x, 0, x, bw, fill=pattern_color, tags='border_image')
                    self.canvas.create_line(x, canvas_h - bw, x, canvas_h, fill=pattern_color, tags='border_image')
            
            # 绘制横线 (遍历整个高度)
            for y in range(0, canvas_h, spacing):
                # 逻辑同上
                if y < bw or y > canvas_h - bw:
                    # 上下边框区域: 画整条横线
                    self.canvas.create_line(0, y, canvas_w, y, fill=pattern_color, tags='border_image')
                else:
                    # 中间区域: 只画左右边框的横线部分
                    self.canvas.create_line(0, y, bw, y, fill=pattern_color, tags='border_image')
                    self.canvas.create_line(canvas_w - bw, y, canvas_w, y, fill=pattern_color, tags='border_image')

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
                self.canvas.create_line(points, fill=pattern_color, smooth=True, tags='border_image')
            
            # 下边框
            points = []
            for x in range(0, canvas_w, 2):
                y = canvas_h - bw / 2 + amplitude * math.sin(x / wavelength * 2 * math.pi)
                points.append(x)
                points.append(y)
            if len(points) >= 4:
                self.canvas.create_line(points, fill=pattern_color, smooth=True, tags='border_image')
            
            # 左边框
            points = []
            for y in range(0, canvas_h, 2):
                x = bw / 2 + amplitude * math.sin(y / wavelength * 2 * math.pi)
                points.append(x)
                points.append(y)
            if len(points) >= 4:
                self.canvas.create_line(points, fill=pattern_color, smooth=True, tags='border_image')
            
            # 右边框
            points = []
            for y in range(0, canvas_h, 2):
                x = canvas_w - bw / 2 + amplitude * math.sin(y / wavelength * 2 * math.pi)
                points.append(x)
                points.append(y)
            if len(points) >= 4:
                self.canvas.create_line(points, fill=pattern_color, smooth=True, tags='border_image')
        
        elif pattern in ('heart', 'club', 'triangle', 'diamond'):
            # 通用几何图形图案
            spacing = max(pattern_size * 2, 10)
            icon_size = max(pattern_size, 4)
            step = spacing
            
            # 辅助函数: 在指定位置绘制图案
            def draw_shape(cx, cy):
                if pattern == 'triangle':
                    h = icon_size * 0.866
                    pts = [
                        cx, cy - h/2,
                        cx - icon_size/2, cy + h/2,
                        cx + icon_size/2, cy + h/2
                    ]
                    self.canvas.create_polygon(pts, fill=pattern_color, outline='', tags='border_image')
                
                elif pattern == 'diamond':
                    r = icon_size / 2
                    pts = [
                        cx, cy - r,
                        cx + r, cy,
                        cx, cy + r,
                        cx - r, cy
                    ]
                    self.canvas.create_polygon(pts, fill=pattern_color, outline='', tags='border_image')
                    
                elif pattern == 'club':
                    r = icon_size / 3
                    # 三个圆
                    self.canvas.create_oval(cx-r, cy-r-r, cx+r, cy-r+r, fill=pattern_color, outline='', tags='border_image')
                    # 左下/右下计算略繁琐，简化为固定偏移
                    dx = r * 0.866
                    dy = r * 0.5
                    self.canvas.create_oval(cx-dx-r, cy+dy-r, cx-dx+r, cy+dy+r, fill=pattern_color, outline='', tags='border_image')
                    self.canvas.create_oval(cx+dx-r, cy+dy-r, cx+dx+r, cy+dy+r, fill=pattern_color, outline='', tags='border_image')
                    # 茎
                    self.canvas.create_polygon(cx, cy, cx-r/3, cy+r*2, cx+r/3, cy+r*2, fill=pattern_color, outline='', tags='border_image')

                elif pattern == 'heart':
                    # 简化绘制: 两个圆 + 一个三角形? 或者贝塞尔曲线
                    # 这里使用简单的点集模拟（因为 Canvas 没有直接的心形指令）
                    import math
                    pts = []
                    # 适当减少点数以提高性能
                    for t in range(0, 360, 30): 
                        rad = math.radians(t)
                        px = cx + (icon_size/32) * (16 * math.sin(rad)**3)
                        py = cy - (icon_size/32) * (13 * math.cos(rad) - 5 * math.cos(2*rad) - 2 * math.cos(3*rad) - math.cos(4*rad))
                        pts.append(px)
                        pts.append(py)
                    self.canvas.create_polygon(pts, fill=pattern_color, outline='', tags='border_image', smooth=True)

            # 沿边框绘制
            # 上下边框
            for x in range(step//2, canvas_w, step):
                draw_shape(x, bw // 2)
                draw_shape(x, canvas_h - bw // 2)
                
            # 左右边框
            for y in range(bw + step//2, canvas_h - bw, step):
                draw_shape(bw // 2, y)
                draw_shape(canvas_w - bw // 2, y)
    
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
            # 波点图案 - 使用与导出相同的间距公式
            spacing = max(pattern_size * 2, 8)
            dot_radius = max(pattern_size // 3, 2)
            for y in range(0, canvas_h + spacing, spacing):
                offset = (y // spacing) % 2 * (spacing // 2)
                for x in range(offset, canvas_w + spacing, spacing):
                    self.canvas.create_oval(
                        x - dot_radius, y - dot_radius,
                        x + dot_radius, y + dot_radius,
                        fill=pattern_color, outline='', tags='background_pattern'
                    )
        
        elif pattern_id == 'grid':
            # 网格图案 - 使用与导出相同的间距公式
            spacing = max(pattern_size, 6)
            if pattern_size > 10: spacing = pattern_size
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
            # 横线图案 - 使用与导出相同的间距公式
            spacing = max(pattern_size, 6)
            if pattern_size > 10: spacing = pattern_size
            for y in range(0, canvas_h, spacing):
                self.canvas.create_line(
                    0, y, canvas_w, y,
                    fill=pattern_color, width=1, tags='background_pattern'
                )
        
        elif pattern_id == 'vertical':
            # 竖线图案 - 使用与导出相同的间距公式
            spacing = max(pattern_size, 6)
            if pattern_size > 10: spacing = pattern_size
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
        print(f"[DEBUG] Right click at ({event.x}, {event.y})")
        # 查找下方对象 (与点击选择逻辑一致)
        items = self.canvas.find_overlapping(event.x - 2, event.y - 2, event.x + 2, event.y + 2)
        print(f"[DEBUG] Overlapping items: {items}")
        
        target_item = None
        for item in reversed(items):
            tags = self.canvas.gettags(item)
            print(f"[DEBUG] Item {item} tags: {tags}")
            if 'sticker' in tags or 'main_image' in tags or 'text_layer' in tags:
                target_item = item
                break
        
        if target_item:
            print(f"[DEBUG] Target found: {target_item} {self.canvas.gettags(target_item)}")
            self.selected_item = target_item
            
            # 同时也更新选中状态（显示缩放手柄）
            self.dragging_item = None # Reset dragging
            
            if 'sticker' in self.canvas.gettags(target_item):
                self.selected_sticker = target_item
            else:
                self.selected_sticker = None
            
            self._create_scaling_handles(target_item)
            
            print(f"[DEBUG] Posting context menu at {event.x_root}, {event.y_root}")
            # 使用 tk_popup 替代 post，在 macOS 上更稳定
            self.context_menu.tk_popup(event.x_root, event.y_root)
        else:
            print("[DEBUG] No target found for context menu")

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

        # 2. 识别贴纸、图片或文字
        # 按从上到下的顺序查找
        items = self.canvas.find_overlapping(event.x - 2, event.y - 2, event.x + 2, event.y + 2)
        for item in reversed(items):
            tags = self.canvas.gettags(item)
            if 'sticker' in tags or 'main_image' in tags or 'text_layer' in tags:
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
        
    def add_text_layer_item(self, pil_image, x, y):
        """添加文字层作为独立对象"""
        # 检查文字层是否当前被选中，如果是，需要更新选中引用
        was_selected = False
        if self.selected_item:
            tags = self.canvas.gettags(self.selected_item)
            if 'text_layer' in tags:
                was_selected = True
        
        self.canvas.delete('text_layer')
        
        self.text_pil_image = pil_image
        self.text_photo = ImageTk.PhotoImage(pil_image)
        
        # 创建图片对象
        text_id = self.canvas.create_image(
            x, y,
            image=self.text_photo,
            anchor=tk.NW, # 文字渲染通常从左上角开始
            tags='text_layer'
        )
        # 确保在贴纸之上，边框之下
        self._ensure_layer_order()
        
        # 如果之前被选中，更新引用并重绘手柄
        if was_selected:
            self.selected_item = text_id
            self._create_scaling_handles(text_id)
            
        return text_id
    
    def clear_text_layer(self):
        """清除文字层"""
        self.canvas.delete('text_layer')
        self.text_pil_image = None
        self.text_photo = None
        
    def set_text_callback(self, callback):
        """设置文字交互回调"""
        self.on_text_interaction = callback
    
    def on_canvas_drag(self, event):
        """画布拖拽事件"""
        dx = event.x - self.drag_start_x
        dy = event.y - self.drag_start_y
        
        # 1. 处理缩放
        if self.handle_type and self.selected_item:
            tags = self.canvas.gettags(self.selected_item)
            
            if 'sticker' in tags:
                # 贴纸缩放：通过调整大小
                for sticker in self.stickers:
                    if sticker['id'] == self.selected_item:
                        current_size = sticker['size']
                        if 's' in self.handle_type or 'e' in self.handle_type:
                            size_delta = max(dx, dy) // 3
                        else:
                            size_delta = -max(-dx, -dy) // 3
                        
                        new_size = max(12, min(200, current_size + size_delta))
                        sticker['size'] = new_size
                        
                        if sticker.get('is_image', False):
                            # 图片类型：重新渲染并更新
                            emoji_img = self._render_emoji_image(sticker['text'], new_size)
                            if emoji_img:
                                photo = ImageTk.PhotoImage(emoji_img)
                                self.sticker_photo_refs.append(photo)  # 保持引用
                                self.canvas.itemconfigure(self.selected_item, image=photo)
                        else:
                            # 文本类型：调整字体大小
                            self.canvas.itemconfigure(self.selected_item, font=('Arial', new_size))
                        break
            
            elif 'text_layer' in tags:
                # 文字层缩放：通过回调通知主窗口调整字号
                if hasattr(self, 'on_text_interaction') and self.on_text_interaction:
                    # 简单的缩放因子计算
                    if 's' in self.handle_type or 'e' in self.handle_type:
                        delta = max(dx, dy)
                    else:
                        delta = -max(-dx, -dy)
                    
                    # 避免过快
                    if abs(delta) > 5:
                        factor = 1.0 + (delta / 200.0)
                        self.on_text_interaction('scale', factor=factor)
                        
                        # 重置 drag start 防止累积过快
                        self.drag_start_x = event.x
                        self.drag_start_y = event.y
                return
                
            elif 'main_image' in tags:
                # 图片缩放：重新渲染图片
                if hasattr(self, 'original_pil_image') and hasattr(self, 'current_display_size'):
                    # 使用拖动开始时的初始尺寸 (如果没有则用当前尺寸)
                    if not hasattr(self, '_scale_start_size'):
                        self._scale_start_size = self.current_display_size
                    
                    init_w, init_h = self._scale_start_size
                    
                    # 计算从拖动开始的总位移
                    total_dy = event.y - self.drag_start_y
                    total_dx = event.x - self.drag_start_x
                    
                    # 根据拖拽方向计算缩放比例
                    if 'se' in self.handle_type or self.handle_type == 's' or self.handle_type == 'e':
                        scale_delta = max(total_dx, total_dy)
                    elif 'nw' in self.handle_type or self.handle_type == 'n' or self.handle_type == 'w':
                        scale_delta = -max(-total_dx, -total_dy)
                    elif 'ne' in self.handle_type:
                        scale_delta = max(total_dx, -total_dy)
                    elif 'sw' in self.handle_type:
                        scale_delta = max(-total_dx, total_dy)
                    else:
                        scale_delta = max(total_dx, total_dy)
                    
                    # 基于初始尺寸计算新尺寸 (避免累积误差)
                    new_w = max(50, int(init_w + scale_delta))
                    new_h = max(50, int(init_h * new_w / init_w))  # 保持比例
                    
                    # 限制最大尺寸
                    new_w = min(new_w, self.width * 2)
                    new_h = min(new_h, self.height * 2)
                    
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
            
            tags = self.canvas.gettags(self.dragging_item)
            
            # 更新贴纸数据
            if 'sticker' in tags:
                for sticker in self.stickers:
                    if sticker['id'] == self.dragging_item:
                        coords = self.canvas.coords(sticker['id'])
                        if len(coords) == 2:
                            sticker['x'] = coords[0]
                            sticker['y'] = coords[1]
                        break
            
            # 更新文字位置 (通过回调)
            elif 'text_layer' in tags:
                coords = self.canvas.coords(self.dragging_item)
                # create_image returns x,y but if dragged, coords might be same.
                # anchor logic might apply. image with anchor NW, coords is x,y.
                if len(coords) == 2:
                    if hasattr(self, 'on_text_interaction') and self.on_text_interaction:
                         self.on_text_interaction('move', x=coords[0], y=coords[1])
    
    def on_canvas_release(self, event):
        """画布释放事件"""
        self.dragging_item = None
        self.handle_type = None
        # 清除缩放开始时的尺寸记录
        if hasattr(self, '_scale_start_size'):
            del self._scale_start_size
    
    def delete_selected_sticker(self):
        """删除选中项"""
        if not self.selected_item:
            return False
            
        tags = self.canvas.gettags(self.selected_item)
        
        if 'sticker' in tags:
            self.canvas.delete(self.selected_item)
            self.stickers = [s for s in self.stickers if s['id'] != self.selected_item]
            self.selected_sticker = None
            self.selected_item = None
            self._hide_scaling_handles()
            return True
            
        elif 'text_layer' in tags:
            self.clear_text_layer()
            if hasattr(self, 'on_text_interaction') and self.on_text_interaction:
                 self.on_text_interaction('delete')
            self.selected_item = None
            self._hide_scaling_handles()
            return True

        elif 'main_image' in tags:
            # [NEW] 支持删除主图片
            self.clear_main_image()
            self._hide_scaling_handles()
            self.selected_item = None
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
            
            if sticker.get('is_image', False):
                # 图片类型：重新渲染并更新
                emoji_img = self._render_emoji_image(sticker['text'], sticker['size'])
                if emoji_img:
                    photo = ImageTk.PhotoImage(emoji_img)
                    self.sticker_photo_refs.append(photo)  # 保持引用
                    self.canvas.itemconfigure(sticker['id'], image=photo)
            else:
                # 文本类型：调整字体大小
                self.canvas.itemconfigure(sticker['id'], font=('Arial', sticker['size']))
            
        # 清除旧边框（将在重新应用时绘制新边框）
        self.canvas.delete('border')
        self.canvas.delete('border_image')
        # 强制更新
        self.canvas.update_idletasks()

    def get_main_image_geometry(self):
        """获取主图片的相对几何信息 (rel_x, rel_y, rel_w, rel_h)"""
        if not self.main_image_id:
            return None
            
        bbox = self.canvas.bbox(self.main_image_id)
        if not bbox:
            return None
            
        x1, y1, x2, y2 = bbox
        
        # 获取画布实际尺寸
        canvas_w = self.canvas.winfo_width()
        canvas_h = self.canvas.winfo_height()
        
        # 避免除以零
        if canvas_w <= 0: canvas_w = self.width
        if canvas_h <= 0: canvas_h = self.height
        
        # 计算相对坐标 (0.0 - 1.0)
        rel_x = x1 / canvas_w
        rel_y = y1 / canvas_h
        rel_w = (x2 - x1) / canvas_w
        rel_h = (y2 - y1) / canvas_h
        
        return (rel_x, rel_y, rel_w, rel_h)

    def set_text_layer(self, text_layer):
        """设置文字层并渲染到画布"""
        # 清除旧的文字层
        self.clear_text_layer()
        
        if not text_layer or not text_layer.content:
            return
        
        # 渲染文字
        from image_processor import TextLayer
        rendered, x, y = text_layer.render(self.width, self.height, scale=1.0)
        
        if rendered:
            # 转换为 PhotoImage
            self._text_photo = ImageTk.PhotoImage(rendered)
            self._text_id = self.canvas.create_image(
                x, y, 
                image=self._text_photo, 
                anchor='nw',
                tags=('text_layer',)
            )
            self._ensure_layer_order()
    
    def set_text_preview(self, config):
        """设置文字预览 (实时)"""
        if not config.get('content'):
            self.clear_text_layer()
            return
        
        from image_processor import TextLayer
        
        # 创建临时文字层
        text_layer = TextLayer(
            content=config.get('content', ''),
            font_size=config.get('font_size', 48),
            color=config.get('color', '#FFFFFF'),
            font_family=config.get('font_family', 'pingfang'),
            align=config.get('align', 'center'),
            position=config.get('position', 'bottom'),
            margin=config.get('margin', 20),
            indent=config.get('indent', False),
            shadow=config.get('shadow'),
            stroke=config.get('stroke'),
            highlight=config.get('highlight'),
            bold=config.get('bold', False),
            italic=config.get('italic', False),
            underline=config.get('underline', False)
        )
        
        self.set_text_layer(text_layer)
    
    def clear_text_layer(self):
        """清除文字层"""
        self.canvas.delete('text_layer')
        self._text_photo = None
        self._text_id = None
