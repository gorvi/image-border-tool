"""
复合图片生成器模块
用于合成最终图片，处理贴纸、边框、文字合成等
"""

from PIL import Image, ImageDraw, ImageFont, ImageFilter
import io
import os
import random
import math
from constants import DASH_PATTERNS, DEFAULT_CANVAS_WIDTH

def get_emoji_font(font_size=64):
    """获取跨平台的彩色 emoji 字体
    
    Returns:
        ImageFont 对象，如果找不到则返回 None
    """
    system = platform.system()
    emoji_font_paths = []
    
    if system == 'Darwin':  # macOS
        emoji_font_paths = [
            '/System/Library/Fonts/Apple Color Emoji.ttc',
            '/System/Library/Fonts/Supplemental/Apple Color Emoji.ttc',
        ]
    elif system == 'Windows':  # Windows
        # Windows 10/11 的彩色 emoji 字体
        emoji_font_paths = [
            'C:/Windows/Fonts/seguiemj.ttf',  # Segoe UI Emoji
            'C:/Windows/Fonts/segmdl2.ttf',   # Segoe MDL2 Assets (备用)
        ]
    elif system == 'Linux':  # Linux
        emoji_font_paths = [
            '/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf',
            '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
        ]
    
    # 尝试加载字体
    for font_path in emoji_font_paths:
        if os.path.exists(font_path):
            try:
                font = ImageFont.truetype(font_path, font_size)
                return font
            except Exception as e:
                print(f"[DEBUG] 无法加载字体 {font_path}: {e}")
                continue
    
    return None


class CompositeImage:
    """复合图片生成器 - 用于合成最终图片"""
    
    def __init__(self, width, height, bg_color='white'):
        self.width = width
        self.height = height
        self.canvas = Image.new('RGB', (width, height), bg_color)
        self.draw = ImageDraw.Draw(self.canvas)
        self.current_image = None # 用于 render_background_pattern 引用当前图片
        
    def add_main_image(self, image, fit_mode='contain'):
        """添加主图片"""
        if not image:
            return
        
        # 记录当前图片引用，用于后续绘制背景
        self.current_image = self.canvas 
            
        if fit_mode == 'contain':
            # 保持宽高比，完整显示
            img_ratio = image.width / image.height
            canvas_ratio = self.width / self.height
            
            if img_ratio > canvas_ratio:
                new_width = self.width
                new_height = int(self.width / img_ratio)
            else:
                new_height = self.height
                new_width = int(self.height * img_ratio)
            
            resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            x = (self.width - new_width) // 2
            y = (self.height - new_height) // 2
            self.canvas.paste(resized, (x, y))
            
        elif fit_mode == 'cover':
            # 填充整个画布，可能裁剪
            img_ratio = image.width / image.height
            canvas_ratio = self.width / self.height
            
            if img_ratio > canvas_ratio:
                new_height = self.height
                new_width = int(self.height * img_ratio)
            else:
                new_width = self.width
                new_height = int(self.width / img_ratio)
            
            resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            x = (self.width - new_width) // 2
            y = (self.height - new_height) // 2
            self.canvas.paste(resized, (x, y))
            
        elif fit_mode == 'stretch':
            # 拉伸到画布大小
            resized = image.resize((self.width, self.height), Image.Resampling.LANCZOS)
            self.canvas.paste(resized, (0, 0))

        # 更新 draw 对象
        self.draw = ImageDraw.Draw(self.canvas)
        self.current_image = self.canvas

    def add_main_image_with_geometry(self, image, x, y, w, h, anchor='center'):
        """按照指定几何位置添加图片 (Fit in Box)
        anchor: 'center', 'n' (top), 's' (bottom)
        """
        if not image or w <= 0 or h <= 0:
            return
            
        # 计算缩放 (Contain模式)
        img_ratio = image.width / image.height
        box_ratio = w / h
        
        if img_ratio > box_ratio:
            # 图片更宽，以宽为准
            new_w = int(w)
            new_h = int(w / img_ratio)
        else:
            # 图片更瘦，以高为准
            new_h = int(h)
            new_w = int(h * img_ratio)
            
        resized = image.resize((new_w, new_h), Image.Resampling.LANCZOS)
        
        # 计算粘贴位置
        # 水平始终居中
        paste_x = int(x + (w - new_w) / 2)
        
        # 垂直根据 anchor 调整
        if anchor == 'n':
            paste_y = int(y)
        elif anchor == 's':
            paste_y = int(y + (h - new_h))
        else:
            # center
            paste_y = int(y + (h - new_h) / 2)
        
        self.canvas.paste(resized, (paste_x, paste_y))
        self.draw = ImageDraw.Draw(self.canvas)
        self.current_image = self.canvas
    
    def add_text_layer(self, text_layer, scale=1.0, border_width=0):
        """添加文字层到画布
        
        Args:
            text_layer: TextLayer 实例
            scale: 缩放比例 (用于导出时按分辨率缩放)
            border_width: 边框宽度，用于计算文字安全边距
        """
        if not text_layer or not text_layer.content:
            return
        
        rendered, x, y = text_layer.render(self.width, self.height, scale, safe_margin_x=border_width, safe_margin_y=border_width)
        if rendered:
            # 确保画布是 RGBA 模式
            if self.canvas.mode != 'RGBA':
                self.canvas = self.canvas.convert('RGBA')
            self.canvas.paste(rendered, (x, y), rendered)
            # 重新创建 draw 对象
            self.draw = ImageDraw.Draw(self.canvas)
            self.current_image = self.canvas
    
    def add_sticker(self, emoji_text, x, y, font_size=64):
        """添加贴纸（表情符号）"""
        # 尝试使用跨平台的彩色 emoji 字体
        font = get_emoji_font(font_size)
        
        if font:
            try:
                # 使用临时画布渲染 emoji（支持 embedded_color）
                temp_size = font_size * 3
                emoji_temp = Image.new('RGBA', (temp_size, temp_size), (0, 0, 0, 0))
                emoji_draw = ImageDraw.Draw(emoji_temp)
                emoji_draw.text((temp_size // 2, temp_size // 2), emoji_text, 
                              font=font, anchor="mm", embedded_color=True)
                
                # 裁剪到实际内容
                bbox = emoji_temp.getbbox()
                if bbox:
                    emoji_cropped = emoji_temp.crop(bbox)
                    # 调整大小
                    if emoji_cropped.width != font_size or emoji_cropped.height != font_size:
                        emoji_cropped = emoji_cropped.resize((font_size, font_size), Image.Resampling.LANCZOS)
                    
                    # 确保画布是 RGBA 模式
                    if self.canvas.mode != 'RGBA':
                        self.canvas = self.canvas.convert('RGBA')
                    
                    # 计算粘贴位置（居中）
                    paste_x = x - emoji_cropped.width // 2
                    paste_y = y - emoji_cropped.height // 2
                    self.canvas.paste(emoji_cropped, (paste_x, paste_y), emoji_cropped)
                    self.current_image = self.canvas
                    return
            except Exception as e:
                print(f"[DEBUG] 使用彩色 emoji 字体渲染失败: {e}")
        
        # 降级方案：使用默认字体（黑白）
        try:
            self.draw.text((x, y), emoji_text, fill='black', anchor="mm")
        except:
            self.draw.text((x, y), emoji_text, fill='black')
        self.current_image = self.canvas
    
    def add_sticker_image(self, img, x, y, size):
        """添加图片贴纸"""
        if not img:
            return
            
        # 调整大小
        try:
            resized_sticker = img.resize((size, size), Image.Resampling.LANCZOS)
            
            # 确保画布是 RGBA 模式
            if self.canvas.mode != 'RGBA':
                self.canvas = self.canvas.convert('RGBA')
            
            # 计算粘贴位置（居中）
            paste_x = x - size // 2
            paste_y = y - size // 2
            
            # 如果贴纸是 RGBA，作为 mask 传入
            mask = resized_sticker if resized_sticker.mode == 'RGBA' else None
            self.canvas.paste(resized, (paste_x, paste_y), mask)
            
            # 更新 draw 对象
            self.draw = ImageDraw.Draw(self.canvas)
            self.current_image = self.canvas
        except Exception as e:
            print(f"[DEBUG] 添加图片贴纸失败: {e}")


    def add_border(self, border_style):
        """添加边框 (支持图案和线型)"""
        if border_style.get('id', '') == 'none':
            return
        
        width = border_style.get('width', 10)
        color = border_style.get('color', '#000000')
        pattern = border_style.get('pattern', 'solid')
        line_style = border_style.get('line_style', 'solid')
        
        # 创建透明图层
        border_layer = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
        border_draw = ImageDraw.Draw(border_layer)
        
        # 1. 绘制边框底线 (Base Border)
        if width > 0:
            self._draw_styled_rect(border_draw, 0, 0, self.width-1, self.height-1, 
                                 width, color, line_style, radius=0)
            
        # 2. 绘制图案 (Pattern)
        if pattern and pattern not in ('solid', 'none', '', None):
            pattern_color = border_style.get('pattern_color', '#FFFFFF')
            pattern_size = border_style.get('pattern_size', 10)
            
            # 使用周长绘制逻辑
            self._draw_border_pattern_perimeter(border_draw, pattern, pattern_color, pattern_size, self.width, self.height, width)

        # 3. 合成到画布
        if self.canvas.mode != 'RGBA':
            self.canvas = self.canvas.convert('RGBA')
        self.canvas.paste(border_layer, (0, 0), border_layer)
        self.current_image = self.canvas

    def _draw_dashed_line(self, draw, p1, p2, width, fill, dash_gap=(10, 5)):
        """绘制虚线"""
        x1, y1 = p1
        x2, y2 = p2
        dash_len, gap_len = dash_gap
        
        dx = x2 - x1
        dy = y2 - y1
        length = math.sqrt(dx*dx + dy*dy)
        if length == 0: return
        
        # 单位向量
        ux = dx / length
        uy = dy / length
        
        curr_dist = 0
        while curr_dist < length:
            # 计算这一段的终点
            segment_len = min(dash_len, length - curr_dist)
            
            sx = x1 + ux * curr_dist
            sy = y1 + uy * curr_dist
            ex = sx + ux * segment_len
            ey = sy + uy * segment_len
            
            draw.line([(sx, sy), (ex, ey)], fill=fill, width=width)
            
            curr_dist += dash_len + gap_len

    def _draw_styled_rect(self, draw, x1, y1, x2, y2, width, color, line_style, radius=0):
        """绘制带样式的矩形 (支持虚线)"""
        # Solid border handled
        if line_style == 'solid':
            if radius > 0:
                draw.rounded_rectangle([x1, y1, x2, y2], radius=radius, outline=color, width=width)
            else:
                draw.rectangle([x1, y1, x2, y2], outline=color, width=width)
            return

        if line_style == 'dashed':
             print(f"[DEBUG] Drawing dashed border. Width={width}, Color={color}")
             # macOS Preview visual compatibility: Dashed lines appear as diagonal stripes
             # We simulate this by drawing tilted parallelograms along the border path
             
             dash_w = width * 1.0 
             gap_w = width * 0.5
             period = dash_w + gap_w
             
             # Calculate scale to ensure consistent look
             current_scale = max(1.0, self.width / DEFAULT_CANVAS_WIDTH)
             dash_w = max(width, 10 * current_scale)
             gap_w = max(width // 2, 5 * current_scale)
             period = dash_w + gap_w
             
             print(f"[DEBUG] Dash params: dash_w={dash_w}, period={period}, scale={current_scale}")
             
             # Top (Horizontal)
             count = 0
             for x in range(int(x1+radius), int(x2-radius), int(period)):
                 # Parallelogram points:
                 # BL: (x, y1+width)
                 # TL: (x+width, y1) -> Offset by width gives 45 degree slope
                 # TR: (x+width+dash_w, y1)
                 # BR: (x+dash_w, y1+width)
                 
                 # Ensure we don't draw past x2-radius
                 if x + dash_w > x2 - radius:
                     continue
                     
                 points = [
                     (x, y1+width),
                     (x + width, y1),
                     (x + width + dash_w, y1),
                     (x + dash_w, y1 + width)
                 ]
                 draw.polygon(points, fill=color)

             # Bottom (Horizontal)
             for x in range(int(x1+radius), int(x2-radius), int(period)):
                 # Parallelogram /
                 # BL: (x, y2)
                 # TL: (x+width, y2-width)
                 
                 if x + dash_w > x2 - radius:
                     continue
                     
                 points = [
                     (x, y2),
                     (x + width, y2 - width),
                     (x + width + dash_w, y2 - width),
                     (x + dash_w, y2)
                 ]
                 draw.polygon(points, fill=color)

             # Left (Vertical)
             # Stripes / / /
             for y in range(int(y1+radius), int(y2-radius), int(period)):
                # BL: (x1, y+width)
                # TR: (x1+width, y)
                
                if y + dash_w > y2 - radius:
                    continue

                points = [
                    (x1, y + width),
                    (x1 + width, y),
                    (x1 + width, y + dash_w),
                    (x1, y + width + dash_w)
                ]
                draw.polygon(points, fill=color)

             # Right (Vertical)
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
                
             # Corners
             if radius > 0:
                 # Draw solid arcs at corners (simplest solution to bridge segments)
                 # Or leave them blank if user prefers gaps. Solid is safer for continuity.
                 draw.arc([x1, y1, x1+2*radius, y1+2*radius], 180, 270, fill=color, width=width)
                 draw.arc([x2-2*radius, y1, x2, y1+2*radius], 270, 0, fill=color, width=width)
                 draw.arc([x2-2*radius, y2-2*radius, x2, y2], 0, 90, fill=color, width=width)
                 draw.arc([x1, y2-2*radius, x1+2*radius, y2], 90, 180, fill=color, width=width)
             
             return # Skip default logic
             
        # Handle 'dotted' style - draw small circles along the border
        if line_style == 'dotted':
            current_scale = max(1.0, self.width / DEFAULT_CANVAS_WIDTH)
            dot_radius = max(width // 2, int(3 * current_scale))
            dot_spacing = max(width, int(10 * current_scale))
            
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
            return

        # Handle 'double' style - draw two parallel lines
        if line_style == 'double':
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
            return

        # Fallback: draw solid border for any unrecognized style
        if radius > 0:
            draw.rounded_rectangle([x1, y1, x2, y2], radius=radius, outline=color, width=width)
        else:
            draw.rectangle([x1, y1, x2, y2], outline=color, width=width)

    def add_rounded_border(self, border_style):
        """添加圆角边框 (支持图案和线型)"""
        if border_style.get('id', '') == 'none':
            return
        
        width = border_style.get('width', 10)
        color = border_style.get('color', '#000000')
        radius = border_style.get('radius', 20)
        pattern = border_style.get('pattern', 'solid')
        line_style = border_style.get('line_style', 'solid')
        
        # 1. 先应用圆角裁剪主画布 (保持不变)
        mask_size = (self.width, self.height)
        mask = Image.new('L', mask_size, 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rounded_rectangle(
            [0, 0, self.width, self.height], # 修正: 遮罩应该是全图大小，边缘裁切
            radius=radius,
            fill=255
        )
        # 注意: 原代码中的遮罩可能有点小问题，这里简单使用全图圆角遮罩
        
        # 更好的方式：创建一个新的透明层，将原图paste进去带遮罩
        # 但为了保持兼容，我们只对边缘做处理?
        # 原逻辑是 mask.rounded_rectangle([width...]) ? 那是裁切掉内容?
        # 不，add_rounded_border 应该是给图片加相框。
        # 原逻辑: 
        # mask_draw.rounded_rectangle([width, width...]) -> 这是为了保留内容区域?
        # 让我们保留原有的裁切逻辑，以免破坏布局:
        # 也就是 mask 是全白的，但是我们要模拟圆角相框的效果
        
        # 修正: 上面的 diff 中我可能误读了原代码意图。
        # 原代码: mask 默认0(黑), rounded_rectangle fill=255(白).
        # box=[width, width, self.width - width, self.height - width]
        # 这意味着它把图片裁剪到了边框 *内部* ? 
        # 是的，如果加了边框，内容应该在边框里面。
        
        # 此处我们只改边框绘制逻辑，尽量不动裁切逻辑 (除非它是错的)
        # 但为了能在 ImageProcessor 中复用，我保持原有的裁切部分 (lines 300-318)
        # 只替换 319-364 的边框绘制逻辑
        
        # --- 裁切逻辑开始 (保留) ---
        mask = Image.new('L', (self.width, self.height), 0)
        mask_draw = ImageDraw.Draw(mask)
        # 内容区域
        mask_draw.rounded_rectangle(
            [width, width, self.width - width, self.height - width],
            radius=radius,
            fill=255
        )
        
        output = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
        if self.canvas.mode != 'RGBA':
            self.canvas = self.canvas.convert('RGBA')
        output.paste(self.canvas, (0, 0), mask)
        self.canvas = output
        # --- 裁切逻辑结束 ---
        
        # 2. 绘制边框层
        border_layer = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
        border_draw = ImageDraw.Draw(border_layer)
        
        # 绘制底线 (Base Border)
        if width > 0:
            self._draw_styled_rect(border_draw, 0, 0, self.width-1, self.height-1, 
                                 width, color, line_style, radius=radius)
            
        # 3. 绘制图案 (Pattern)
        if pattern and pattern not in ('solid', 'none', '', None):
            pattern_color = border_style.get('pattern_color', '#FFFFFF')
            pattern_size = border_style.get('pattern_size', 10)
            
            # 使用周长绘制逻辑
            self._draw_border_pattern_perimeter(border_draw, pattern, pattern_color, pattern_size, self.width, self.height, width)

        # 4. 合成
        self.canvas.paste(border_layer, (0, 0), border_layer)
        self.draw = ImageDraw.Draw(self.canvas)
        self.current_image = self.canvas

    def _draw_pattern(self, draw, pattern_id, color, pattern_size, width, height):
        """绘制图案 (内部辅助方法)"""
        # 注意：此方法主要用于 render_background_pattern (全屏平铺)
        # 与 _draw_border_pattern_perimeter (边框周长) 不同
        if pattern_id == 'stripe':
            # 斜纹
            spacing = pattern_size * 2
            for i in range(-height, width + height, spacing):
                draw.line([(i, 0), (i + height, height)], fill=color, width=1)
        
        elif pattern_id == 'dots':
            # 波点
            spacing = max(pattern_size * 2, 8)
            dot_radius = max(pattern_size // 3, 2)
            for y in range(0, height + spacing, spacing):
                offset = (y // spacing) % 2 * (spacing // 2)
                for x in range(offset, width + spacing, spacing):
                    draw.ellipse(
                        [x - dot_radius, y - dot_radius, x + dot_radius, y + dot_radius],
                        fill=color
                    )
        
        elif pattern_id == 'grid':
            # 网格
            spacing = max(pattern_size, 6)
            if pattern_size > 10: spacing = pattern_size
            
            for x in range(0, width, spacing):
                draw.line([(x, 0), (x, height)], fill=color, width=1)
            for y in range(0, height, spacing):
                draw.line([(0, y), (width, y)], fill=color, width=1)

        elif pattern_id == 'horizontal':
            # 横线
            spacing = max(pattern_size, 6)
            if pattern_size > 10: spacing = pattern_size
            for y in range(0, height, spacing):
                draw.line([(0, y), (width, y)], fill=color, width=1)
                
        elif pattern_id == 'vertical':
            # 竖线
            spacing = max(pattern_size, 6)
            if pattern_size > 10: spacing = pattern_size
            for x in range(0, width, spacing):
                draw.line([(x, 0), (x, height)], fill=color, width=1)

        elif pattern_id == 'heart':
            # 心形图案
            # import math # Removed redundant import
            ideal_spacing = max(pattern_size * 2, 10)
            icon_size = max(pattern_size, 4)
            
            # 自适应间距 X
            num_x = max(1, round(width / ideal_spacing))
            step_x = width / num_x
            
            # 自适应间距 Y
            num_y = max(1, round(height / ideal_spacing))
            step_y = height / num_y
            
            for iy in range(num_y):
                cy = (iy + 0.5) * step_y
                for ix in range(num_x):
                    cx = (ix + 0.5) * step_x
                    
                    pts = []
                    for t in range(0, 360, 20):
                        rad = math.radians(t)
                        px = cx + (icon_size/32) * (16 * math.sin(rad)**3)
                        py = cy - (icon_size/32) * (13 * math.cos(rad) - 5 * math.cos(2*rad) - 2 * math.cos(3*rad) - math.cos(4*rad))
                        pts.append((px, py))
                    
                    if len(pts) > 2:
                        draw.polygon(pts, fill=color, outline=None)

        elif pattern_id == 'club':
            # 梅花图案 (三叶草)
            ideal_spacing = max(pattern_size * 2, 10)
            icon_size = max(pattern_size, 4)
            r = icon_size / 3
            
            num_x = max(1, round(width / ideal_spacing))
            step_x = width / num_x
            num_y = max(1, round(height / ideal_spacing))
            step_y = height / num_y
            
            for iy in range(num_y):
                cy = (iy + 0.5) * step_y
                for ix in range(num_x):
                    cx = (ix + 0.5) * step_x
                    
                    # 绘制三个圆
                    draw.ellipse([cx-r, cy-r-r, cx+r, cy-r+r], fill=color)
                    dx = r * math.sin(math.radians(60))
                    dy = r * math.cos(math.radians(60))
                    draw.ellipse([cx-dx-r, cy+dy-r, cx-dx+r, cy+dy+r], fill=color)
                    draw.ellipse([cx+dx-r, cy+dy-r, cx+dx+r, cy+dy+r], fill=color)
                    # 茎
                    draw.polygon([(cx, cy), (cx-r/3, cy+r*2), (cx+r/3, cy+r*2)], fill=color)

        elif pattern_id == 'triangle':
            # 三角形图案
            ideal_spacing = max(pattern_size * 2, 10)
            icon_size = max(pattern_size, 4)
            h = icon_size * 0.866
            
            num_x = max(1, round(width / ideal_spacing))
            step_x = width / num_x
            num_y = max(1, round(height / ideal_spacing))
            step_y = height / num_y
            
            for iy in range(num_y):
                cy = (iy + 0.5) * step_y
                for ix in range(num_x):
                    cx = (ix + 0.5) * step_x
                    
                    pts = [
                        (cx, cy - h/2),
                        (cx - icon_size/2, cy + h/2),
                        (cx + icon_size/2, cy + h/2)
                    ]
                    draw.polygon(pts, fill=color)

        elif pattern_id == 'diamond':
            # 菱形图案
            ideal_spacing = max(pattern_size * 2, 10)
            icon_size = max(pattern_size, 4)
            r = icon_size / 2
            
            num_x = max(1, round(width / ideal_spacing))
            step_x = width / num_x
            num_y = max(1, round(height / ideal_spacing))
            step_y = height / num_y
            
            for iy in range(num_y):
                cy = (iy + 0.5) * step_y
                for ix in range(num_x):
                    cx = (ix + 0.5) * step_x
                    
                    pts = [
                        (cx, cy - r),
                        (cx + r, cy),
                        (cx, cy + r),
                        (cx - r, cy)
                    ]
                    draw.polygon(pts, fill=color)

        elif pattern_id == 'wave':
            # 波浪 (优化逻辑)
            amplitude = max(2, pattern_size / 3)
            wavelength = max(10, pattern_size * 2)
            step_y = max(8, pattern_size)
            
            x_step = 2
            for y_base in range(0, height, int(step_y)):
                points = []
                for x in range(0, width, x_step):
                    y = y_base + amplitude * math.sin(x / wavelength * 2 * math.pi)
                    points.append((x, y))
                if len(points) > 1:
                    draw.line(points, fill=color, width=1)

    
    def render_background_pattern(self, pattern_id, pattern_color, pattern_size=10):
        """绘制背景图案"""
        if not pattern_id or pattern_id == 'none':
            return
            
        if not self.current_image:
            # 如果没有主图，可以尝试在canvas上直接画？
            # 这里的逻辑是依赖于 current_image (可能是 canvas 或 add_main_image 设置的)
            if self.canvas:
                 self.current_image = self.canvas
            else:
                 return

        width, height = self.current_image.size
        # 创建 Draw 对象
        try:
            draw = ImageDraw.Draw(self.current_image)
            self._draw_pattern(draw, pattern_id, pattern_color, pattern_size, width, height)
        except Exception as e:
            print(f"Draw pattern failed: {e}")
    
    def _draw_border_pattern_perimeter(self, draw, pattern, color, pattern_size, width, height, border_width):
        """沿边框周长绘制图案 (类似 CanvasWidget 逻辑)"""
        bw = int(border_width)
        canvas_w = width
        canvas_h = height
        pattern_color = color
        
        # 辅助函数: 在指定位置绘制图案
        def draw_shape(cx, cy):
            if pattern == 'triangle':
                icon_size = max(pattern_size, 4)
                h = icon_size * 0.866
                pts = [
                    (cx, cy - h/2),
                    (cx - icon_size/2, cy + h/2),
                    (cx + icon_size/2, cy + h/2)
                ]
                draw.polygon(pts, fill=pattern_color)
            
            elif pattern == 'diamond':
                icon_size = max(pattern_size, 4)
                r = icon_size / 2
                pts = [
                    (cx, cy - r),
                    (cx + r, cy),
                    (cx, cy + r),
                    (cx - r, cy)
                ]
                draw.polygon(pts, fill=pattern_color)
                
            elif pattern == 'club':
                icon_size = max(pattern_size, 4)
                r = icon_size / 3
                # 三个圆
                draw.ellipse([cx-r, cy-r-r, cx+r, cy-r+r], fill=pattern_color)
                dx = r * 0.866
                dy = r * 0.5
                draw.ellipse([cx-dx-r, cy+dy-r, cx-dx+r, cy+dy+r], fill=pattern_color)
                draw.ellipse([cx+dx-r, cy+dy-r, cx+dx+r, cy+dy+r], fill=pattern_color)
                # 茎
                draw.polygon([(cx, cy), (cx-r/3, cy+r*2), (cx+r/3, cy+r*2)], fill=pattern_color)

            elif pattern == 'heart':
                icon_size = max(pattern_size, 4)
                # import math # Removed redundant import
                pts = []
                for t in range(0, 360, 30): 
                    rad = math.radians(t)
                    px = cx + (icon_size/32) * (16 * math.sin(rad)**3)
                    py = cy - (icon_size/32) * (13 * math.cos(rad) - 5 * math.cos(2*rad) - 2 * math.cos(3*rad) - math.cos(4*rad))
                    pts.append((px, py))
                draw.polygon(pts, fill=pattern_color)

        if pattern in ('stripe', 'horizontal', 'vertical'):
             # 使用原来的逻辑，但限制在边框区域？
             # CanvasWidget stripe 逻辑是画线
             if pattern == 'stripe':
                 spacing = max(6, int(pattern_size * 0.6))
                 # 上边框 & 下边框
                 for i in range(0, canvas_w, spacing):
                     draw.line([(i, 0), (i + bw, bw)], fill=pattern_color, width=1)
                     draw.line([(i, canvas_h - bw), (i + bw, canvas_h)], fill=pattern_color, width=1)
                 # 左边框 & 右边框
                 for i in range(bw, canvas_h - bw, spacing):
                     draw.line([(0, i), (bw, i + bw)], fill=pattern_color, width=1)
                     draw.line([(canvas_w - bw, i), (canvas_w, i + bw)], fill=pattern_color, width=1)
        
        elif pattern == 'dots':
            spacing = max(8, bw)
            dot_r = max(2, bw // 4)
            # 上下边框
            for x in range(spacing // 2, canvas_w, spacing):
                draw.ellipse([x - dot_r, bw // 2 - dot_r, x + dot_r, bw // 2 + dot_r], fill=pattern_color)
                draw.ellipse([x - dot_r, canvas_h - bw // 2 - dot_r, x + dot_r, canvas_h - bw // 2 + dot_r], fill=pattern_color)
            # 左右边框
            for y in range(bw + spacing // 2, canvas_h - bw, spacing):
                draw.ellipse([bw // 2 - dot_r, y - dot_r, bw // 2 + dot_r, y + dot_r], fill=pattern_color)
                draw.ellipse([canvas_w - bw // 2 - dot_r, y - dot_r, canvas_w - bw // 2 + dot_r, y + dot_r], fill=pattern_color)

        elif pattern == 'grid':
            spacing = max(pattern_size, 6)
            if pattern_size > 10: spacing = pattern_size
            for x in range(0, canvas_w, spacing):
                if x < bw or x > canvas_w - bw:
                    draw.line([(x, 0), (x, height)], fill=pattern_color, width=1)
                else:
                    draw.line([(x, 0), (x, bw)], fill=pattern_color, width=1)
                    draw.line([(x, height - bw), (x, height)], fill=pattern_color, width=1)
            for y in range(0, height, spacing):
                if y < bw or y > height - bw:
                    draw.line([(0, y), (width, y)], fill=pattern_color, width=1)
                else:
                    draw.line([(0, y), (bw, y)], fill=pattern_color, width=1)
                    draw.line([(width - bw, y), (width, y)], fill=pattern_color, width=1)

        elif pattern == 'wave':
            # import math # Removed redundant import
            amplitude = max(2, bw / 4)
            wavelength = max(10, bw * 2)
            
            # 辅助绘制 (PIL line需要点列表)
            def get_wave_points(start_x, end_x, y_base, is_vertical=False):
                pts = []
                steps = max(2, int((end_x - start_x)/2))
                for i in range(steps + 1):
                    val = start_x + i * 2
                    sine = amplitude * math.sin(val / wavelength * 2 * math.pi)
                    if is_vertical:
                         pts.append((y_base + sine, val)) # x changes with sine, y is val
                    else:
                         pts.append((val, y_base + sine))
                return pts

            # 上边框
            draw.line(get_wave_points(0, width, bw/2), fill=pattern_color, width=1)
            # 下边框
            draw.line(get_wave_points(0, width, height - bw/2), fill=pattern_color, width=1)
            # 左边框
            draw.line(get_wave_points(0, height, bw/2, True), fill=pattern_color, width=1)
            # 右边框
            draw.line(get_wave_points(0, height, width - bw/2, True), fill=pattern_color, width=1)

        elif pattern in ('heart', 'club', 'triangle', 'diamond'):
            # 沿边框绘制
            step = max(pattern_size * 2, 10)
            # 上下边框
            for x in range(step//2, canvas_w, step):
                draw_shape(x, bw // 2)
                draw_shape(x, canvas_h - bw // 2)
            # 左右边框
            for y in range(bw + step//2, canvas_h - bw, step):
                draw_shape(bw // 2, y)
                draw_shape(canvas_w - bw // 2, y)

    def get_image(self):
        """获取最终图片"""
        return self.canvas
    
    def save(self, file_path, quality=95):
        """保存图片"""
        try:
            save_img = self.canvas
            import os # local import
            ext = os.path.splitext(file_path)[1].lower()
            
            # 如果是JPG，必须转换为RGB，并将透明部分填充为白色
            if ext in ['.jpg', '.jpeg']:
                if save_img.mode == 'RGBA':
                    background = Image.new('RGB', save_img.size, (255, 255, 255))
                    background.paste(save_img, mask=save_img.split()[3])
                    save_img = background
                elif save_img.mode != 'RGB':
                    save_img = save_img.convert('RGB')
            
            save_img.save(file_path, quality=quality, optimize=True)
            return True
        except Exception as e:
            print(f"保存图片失败: {e}")
            return False
