"""
图片处理核心模块
"""

from PIL import Image, ImageDraw, ImageFont, ImageFilter
import io
import os
import random
import math


class ImageProcessor:
    """图片处理器类"""
    
    def __init__(self):
        self.original_image = None
        self.current_image = None
        self.canvas_size = (800, 800)
        
    def load_image(self, file_path):
        """加载图片"""
        try:
            self.original_image = Image.open(file_path)
            self.current_image = self.original_image.copy()
            return True
        except Exception as e:
            print(f"加载图片失败: {e}")
            return False
    
    def load_image_from_bytes(self, image_bytes):
        """从字节数据加载图片"""
        try:
            self.original_image = Image.open(io.BytesIO(image_bytes))
            self.current_image = self.original_image.copy()
            return True
        except Exception as e:
            print(f"加载图片失败: {e}")
            return False
    
    def set_canvas_size(self, width, height):
        """设置画布尺寸"""
        self.canvas_size = (width, height)
    
    def resize_to_canvas(self, maintain_ratio=True):
        """调整图片到画布尺寸"""
        if not self.current_image:
            return None
        
        target_width, target_height = self.canvas_size
        
        if maintain_ratio:
            # 保持宽高比
            img_ratio = self.current_image.width / self.current_image.height
            canvas_ratio = target_width / target_height
            
            if img_ratio > canvas_ratio:
                # 图片更宽，以宽度为准
                new_width = target_width
                new_height = int(target_width / img_ratio)
            else:
                # 图片更高，以高度为准
                new_height = target_height
                new_width = int(target_height * img_ratio)
            
            self.current_image = self.current_image.resize(
                (new_width, new_height), 
                Image.Resampling.LANCZOS
            )
        else:
            # 直接拉伸到目标尺寸
            self.current_image = self.current_image.resize(
                (target_width, target_height), 
                Image.Resampling.LANCZOS
            )
        
        return self.current_image
    
    def crop_image(self, left, top, right, bottom):
        """裁剪图片"""
        if not self.current_image:
            return None
        
        try:
            self.current_image = self.current_image.crop((left, top, right, bottom))
            return self.current_image
        except Exception as e:
            print(f"裁剪失败: {e}")
            return None
    
    def rotate_image(self, angle):
        """旋转图片"""
        if not self.current_image:
            return None
        
        self.current_image = self.current_image.rotate(
            angle, 
            expand=True, 
            fillcolor='white'
        )
        return self.current_image
    
    def flip_image(self, horizontal=True):
        """翻转图片"""
        if not self.current_image:
            return None
        
        if horizontal:
            self.current_image = self.current_image.transpose(Image.FLIP_LEFT_RIGHT)
        else:
            self.current_image = self.current_image.transpose(Image.FLIP_TOP_BOTTOM)
        
        return self.current_image
    
    def apply_filter(self, filter_type):
        """应用滤镜"""
        if not self.current_image:
            return None
        
        if filter_type == 'blur':
            self.current_image = self.current_image.filter(ImageFilter.BLUR)
        elif filter_type == 'sharpen':
            self.current_image = self.current_image.filter(ImageFilter.SHARPEN)
        elif filter_type == 'smooth':
            self.current_image = self.current_image.filter(ImageFilter.SMOOTH)
        elif filter_type == 'grayscale':
            self.current_image = self.current_image.convert('L').convert('RGB')
        elif filter_type == 'contour':
            self.current_image = self.current_image.filter(ImageFilter.CONTOUR)
        elif filter_type == 'emboss':
            self.current_image = self.current_image.filter(ImageFilter.EMBOSS)
        elif filter_type == 'edge':
            self.current_image = self.current_image.filter(ImageFilter.FIND_EDGES)
        
        return self.current_image
    
    def adjust_brightness(self, factor):
        """调整亮度 (factor: 0.0-2.0, 1.0为原始)"""
        if not self.current_image:
            return None
        from PIL import ImageEnhance
        enhancer = ImageEnhance.Brightness(self.current_image)
        self.current_image = enhancer.enhance(factor)
        return self.current_image
    
    def adjust_contrast(self, factor):
        """调整对比度 (factor: 0.0-2.0, 1.0为原始)"""
        if not self.current_image:
            return None
        from PIL import ImageEnhance
        enhancer = ImageEnhance.Contrast(self.current_image)
        self.current_image = enhancer.enhance(factor)
        return self.current_image
    
    def adjust_saturation(self, factor):
        """调整饱和度 (factor: 0.0-2.0, 1.0为原始)"""
        if not self.current_image:
            return None
        from PIL import ImageEnhance
        enhancer = ImageEnhance.Color(self.current_image)
        self.current_image = enhancer.enhance(factor)
        return self.current_image
    
    def reset_image(self):
        """重置图片到原始状态"""
        if self.original_image:
            self.current_image = self.original_image.copy()
            return self.current_image
        return None
    
    def get_current_image(self):
        """获取当前图片"""
        return self.current_image
    
    def save_image(self, file_path, quality=95):
        """保存图片"""
        if not self.current_image:
            return False
        
        try:
            self.current_image.save(file_path, quality=quality, optimize=True)
            return True
        except Exception as e:
            print(f"保存图片失败: {e}")
            return False


class TextLayer:
    """文字层 - 用于渲染带样式的文字"""
    
    # 系统字体路径 (支持多个候选路径)
    # 系统字体路径 (支持多个候选路径，包含 macOS 和 Windows)
    FONT_PATHS = {
        'sf_pro': ['/System/Library/Fonts/SFNS.ttf', '/System/Library/Fonts/SFPro.ttf', 'C:/Windows/Fonts/arial.ttf'],
        'pingfang': ['/System/Library/Fonts/PingFang.ttc', '/System/Library/Fonts/PingFang.ttf', 'C:/Windows/Fonts/msyh.ttc', 'C:/Windows/Fonts/msyh.ttf'],
        'hiragino': ['/System/Library/Fonts/Hiragino Sans GB.ttc', '/Library/Fonts/Hiragino Sans GB.ttc', 'C:/Windows/Fonts/msyh.ttc', 'C:/Windows/Fonts/micross.ttf'],
        'heiti': ['/System/Library/Fonts/STHeiti Light.ttc', '/System/Library/Fonts/Supplemental/STHeiti Light.ttc', 'C:/Windows/Fonts/simhei.ttf'],
        'songti': ['/System/Library/Fonts/Songti.ttc', '/System/Library/Fonts/Supplemental/Songti.ttc', 'C:/Windows/Fonts/simsun.ttc'],
        'kaiti': ['/System/Library/Fonts/STKaiti.ttc', '/System/Library/Fonts/Supplemental/STKaiti.ttc', '/Library/Fonts/STKaiti.ttf', 'C:/Windows/Fonts/simkai.ttf'],
        'yuanti': ['/System/Library/Fonts/STYuanti.ttc', '/System/Library/Fonts/Supplemental/STYuanti.ttc', '/Library/Fonts/STYuanti.ttf', 'C:/Windows/Fonts/simyou.ttf'],
        'xingkai': ['/System/Library/Fonts/STXingkai.ttc', '/System/Library/Fonts/Supplemental/STXingkai.ttc', '/Library/Fonts/STXingkai.ttf', 'C:/Windows/Fonts/STXINGKA.TTF'],
        'weibei': ['/Library/Fonts/WeibeiSC-Bold.otf', '/System/Library/Fonts/Supplemental/WeibeiSC-Bold.otf']
    }
    
    # 字体友好名称映射 (用于UI显示)
    FONT_NAMES = {
        'pingfang': '苹方 (默认)',
        'sf_pro': 'SF Pro (英文)',
        'hiragino': '冬青黑体',
        'heiti': 'ST黑体',
        'songti': 'ST宋体',
        'kaiti': 'ST楷体',
        'yuanti': 'ST圆体',
        'xingkai': 'ST行楷',
        'weibei': '魏碑'
    }

    def __init__(self, content, font_size=48, color='#FFFFFF', 
                 font_family='pingfang', align='left', position='top',
                 margin=20, shadow=None, stroke=None, highlight=None):
        """
        初始化文字层
        
        Args:
            content: 文字内容
            font_size: 字体大小
            color: 文字颜色 (hex)
            font_family: 字体键名 (pingfang, sf_pro, etc.)
            align: 水平对齐 (left, center, right)
            position: 垂直位置 (top, center, bottom)
            margin: 边距 (像素)
            shadow: 阴影配置 {'enabled': True, 'color': '#000000', 'offset': (2,2), 'blur': 4}
            stroke: 描边配置 {'enabled': True, 'color': '#000000', 'width': 2}
            highlight: 高亮配置 {'enabled': True, 'keywords': ['word1','word2'], 'color': '#FFB7B2'}
        """
        self.content = content
        self.font_size = font_size
        self.color = color
        self.font_family = font_family
        self.align = align
        self.position = position
        self.margin = margin
        self.shadow = shadow or {'enabled': False, 'color': '#000000', 'offset': (2, 2), 'blur': 4}
        self.stroke = stroke or {'enabled': False, 'color': '#000000', 'width': 2}
        self.highlight = highlight or {'enabled': False, 'keywords': [], 'color': '#FFB7B2'}
        
        # 相对坐标 (用于拖拽)
        self.rel_x = 0.5
        self.rel_y = 0.1 if position == 'top' else (0.9 if position == 'bottom' else 0.5)
        
    def _get_font(self, size):
        """获取字体对象"""
        candidate_paths = self.FONT_PATHS.get(self.font_family, [])
        
        # 确保是列表
        if isinstance(candidate_paths, str):
            candidate_paths = [candidate_paths]
            
        font_path = None
        for path in candidate_paths:
            if os.path.exists(path):
                font_path = path
                break
        
        # 尝试加载字体
        if font_path:
            try:
                # 对于 TTC 文件，通常需要指定 index (默认0可能不是想要的字重)
                # 苹方: 0=Regular, 1=Thin, 2=Light...
                # 简单起见，暂时使用默认 index=0
                # TODO: 如果用户反馈字体太细，可以尝试 index=5 (Medium) for PingFang
                font = ImageFont.truetype(font_path, size)
                # print(f"[DEBUG] 加载字体成功: {font_path}, size={size}")
                return font
            except Exception as e:
                print(f"加载字体失败 ({font_path}): {e}")
        
        # 回退字体列表 (硬编码的一些常见路径)
        fallback_fonts = [
            '/System/Library/Fonts/PingFang.ttc',
            '/System/Library/Fonts/STHeiti Light.ttc',
            '/System/Library/Fonts/Hiragino Sans GB.ttc',
            '/System/Library/Fonts/Helvetica.ttc',
            '/Library/Fonts/Arial.ttf',
            '/System/Library/Fonts/Supplemental/Arial.ttf',
            'C:/Windows/Fonts/msyh.ttc',
            'C:/Windows/Fonts/simsun.ttc',
            'C:/Windows/Fonts/arial.ttf'
        ]
        
        for fallback in fallback_fonts:
            if os.path.exists(fallback):
                try:
                    font = ImageFont.truetype(fallback, size)
                    print(f"[DEBUG] 使用回退字体: {fallback}")
                    return font
                except:
                    continue
        
        # 最终回退到默认
        print("[DEBUG] 使用 Pillow 默认字体")
        return ImageFont.load_default()
    
    def render(self, canvas_width, canvas_height, scale=1.0):
        """
        渲染文字为 RGBA 图像
        
        Args:
            canvas_width: 画布宽度
            canvas_height: 画布高度
            scale: 缩放比例 (用于导出时按分辨率缩放)
            
        Returns:
            (PIL.Image, x, y): 渲染后的图像和位置
        """
        if not self.content:
            return None, 0, 0
        
        # 缩放参数
        scaled_font_size = int(self.font_size * scale)
        scaled_margin = int(self.margin * scale)
        scaled_stroke_width = int(self.stroke.get('width', 2) * scale) if self.stroke.get('enabled') else 0
        
        font = self._get_font(scaled_font_size)
        
        # 创建临时画布测量文字
        temp_img = Image.new('RGBA', (1, 1), (0, 0, 0, 0))
        temp_draw = ImageDraw.Draw(temp_img)
        
        # 自动换行处理：按画布宽度减去边距
        max_text_width = canvas_width - scaled_margin * 2
        
        # 将文本按行拆分，然后对每行进行自动换行
        original_lines = self.content.split('\n')
        wrapped_lines = []
        
        for original_line in original_lines:
            if not original_line:
                wrapped_lines.append('')
                continue
            
            # 逐字符测量，找到换行点
            words = list(original_line)  # 中文按字符拆分
            current_line = ''
            
            for char in words:
                test_line = current_line + char
                bbox = temp_draw.textbbox((0, 0), test_line, font=font)
                line_width = bbox[2] - bbox[0]
                
                if line_width > max_text_width and current_line:
                    wrapped_lines.append(current_line)
                    current_line = char
                else:
                    current_line = test_line
            
            if current_line:
                wrapped_lines.append(current_line)
        
        # 计算每行尺寸
        lines = wrapped_lines
        line_heights = []
        line_widths = []
        
        for line in lines:
            if line:
                bbox = temp_draw.textbbox((0, 0), line, font=font)
                line_widths.append(bbox[2] - bbox[0])
                line_heights.append(bbox[3] - bbox[1])
            else:
                line_widths.append(0)
                line_heights.append(scaled_font_size)
        
        text_width = max(line_widths) if line_widths else 0
        line_spacing = int(scaled_font_size * 0.3)
        text_height = sum(line_heights) + line_spacing * (len(lines) - 1) if lines else 0
        
        # 添加描边和阴影的额外空间
        padding = scaled_stroke_width * 2 + 10
        if self.shadow.get('enabled'):
            shadow_offset = self.shadow.get('offset', (2, 2))
            padding += max(abs(shadow_offset[0]), abs(shadow_offset[1])) * int(scale) + 5
        
        # 创建渲染画布
        render_width = text_width + padding * 2
        render_height = text_height + padding * 2
        render_img = Image.new('RGBA', (render_width, render_height), (0, 0, 0, 0))
        render_draw = ImageDraw.Draw(render_img)
        
        # 绘制起始位置
        draw_x = padding
        draw_y = padding
        
        for i, line in enumerate(lines):
            # 计算每行的水平位置 (对齐)
            line_x = draw_x
            if self.align == 'center':
                line_x = draw_x + (text_width - line_widths[i]) // 2
            elif self.align == 'right':
                line_x = draw_x + (text_width - line_widths[i])
            
            line_y = draw_y + sum(line_heights[:i]) + line_spacing * i
            
            # 0. 绘制关键字高亮下划线
            if self.highlight.get('enabled') and self.highlight.get('keywords'):
                highlight_color = self.highlight.get('color', '#FFB7B2')
                underline_height = max(4, int(scaled_font_size * 0.15))  # 下划线高度
                
                for keyword in self.highlight.get('keywords', []):
                    if not keyword:
                        continue
                    # 查找关键字在行中的位置
                    start_idx = 0
                    while True:
                        idx = line.lower().find(keyword.lower(), start_idx)
                        if idx == -1:
                            break
                        
                        # 计算关键字的x位置和宽度
                        prefix = line[:idx]
                        keyword_text = line[idx:idx+len(keyword)]
                        
                        prefix_bbox = temp_draw.textbbox((0, 0), prefix, font=font) if prefix else (0, 0, 0, 0)
                        keyword_bbox = temp_draw.textbbox((0, 0), keyword_text, font=font)
                        
                        kw_x = line_x + (prefix_bbox[2] - prefix_bbox[0])
                        kw_width = keyword_bbox[2] - keyword_bbox[0]
                        kw_y = line_y + line_heights[i] - underline_height  # 在文字底部
                        
                        # 绘制随机样式高亮
                        style_type = random.choice(['underline', 'wavy', 'background', 'marker'])
                        base_color = highlight_color
                        
                        # 解析颜色 (如果需要处理透明度)
                        if base_color.startswith('#'):
                            rgb = tuple(int(base_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
                        else:
                            rgb = (255, 183, 178) # Default pink
                            
                        if style_type == 'underline':
                            # 1. 经典下划线 (加一点手绘感的偏移)
                            h_h = max(3, int(scaled_font_size * 0.1))
                            h_y = kw_y + underline_height - h_h
                            render_draw.rectangle(
                                [kw_x, h_y, kw_x + kw_width, h_y + h_h],
                                fill=rgb + (255,)
                            )
                            
                        elif style_type == 'wavy':
                            # 2. 波浪线
                            wave_amp = max(2, int(scaled_font_size * 0.08))
                            wave_freq = 0.3
                            points = []
                            steps = int(kw_width)
                            start_y = kw_y + underline_height - wave_amp
                            for sx in range(0, steps, 2):
                                # y = A * sin(wx)
                                dy = wave_amp * math.sin(sx * wave_freq)
                                points.append((kw_x + sx, start_y + dy))
                            
                            if len(points) > 1:
                                render_draw.line(points, fill=rgb + (220,), width=max(2, int(scaled_font_size * 0.05)))
                                
                        elif style_type == 'background':
                            # 3. 圆角矩形背景 (半透明)
                            pad = int(scaled_font_size * 0.1)
                            bg_rect = [kw_x - pad, line_y, kw_x + kw_width + pad, line_y + line_heights[i]]
                            render_draw.rounded_rectangle(bg_rect, radius=pad, fill=rgb + (100,))
                            
                        elif style_type == 'marker':
                            # 4. 马克笔涂抹效果 (底部2/3高度，半透明)
                            marker_h = int(line_heights[i] * 0.6)
                            marker_y = line_y + line_heights[i] - marker_h
                            render_draw.rectangle(
                                [kw_x, marker_y, kw_x + kw_width, marker_y + marker_h],
                                fill=rgb + (140,)
                            )
                        
                        start_idx = idx + len(keyword)
            
            # 1. 绘制阴影
            if self.shadow.get('enabled'):
                shadow_offset = self.shadow.get('offset', (2, 2))
                shadow_color = self.shadow.get('color', '#000000')
                sx = line_x + int(shadow_offset[0] * scale)
                sy = line_y + int(shadow_offset[1] * scale)
                render_draw.text((sx, sy), line, font=font, fill=shadow_color)
            
            # 2. 绘制描边
            if self.stroke.get('enabled') and scaled_stroke_width > 0:
                stroke_color = self.stroke.get('color', '#000000')
                render_draw.text((line_x, line_y), line, font=font, 
                               fill=self.color, stroke_width=scaled_stroke_width,
                               stroke_fill=stroke_color)
            else:
                # 3. 绘制文字
                render_draw.text((line_x, line_y), line, font=font, fill=self.color)
        
        # 计算在画布上的位置
        x, y = self._calculate_position(canvas_width, canvas_height, 
                                         render_width, render_height, scaled_margin)
        
        return render_img, x, y
    
    def _calculate_position(self, canvas_width, canvas_height, text_width, text_height, margin):
        """计算文字在画布上的位置"""
        # 水平位置
        if self.align == 'left':
            x = margin
        elif self.align == 'right':
            x = canvas_width - text_width - margin
        else:  # center
            x = (canvas_width - text_width) // 2
        
        # 垂直位置
        if self.position == 'top':
            y = margin
        elif self.position == 'bottom':
            y = canvas_height - text_height - margin
        else:  # center
            y = (canvas_height - text_height) // 2
        
        return x, y
    
    def to_dict(self):
        """转换为字典 (用于保存)"""
        return {
            'content': self.content,
            'font_size': self.font_size,
            'color': self.color,
            'font_family': self.font_family,
            'align': self.align,
            'position': self.position,
            'margin': self.margin,
            'shadow': self.shadow,
            'stroke': self.stroke,
            'rel_x': self.rel_x,
            'rel_y': self.rel_y,
        }
    
    @classmethod
    def from_dict(cls, data):
        """从字典创建 (用于加载)"""
        layer = cls(
            content=data.get('content', ''),
            font_size=data.get('font_size', 48),
            color=data.get('color', '#FFFFFF'),
            font_family=data.get('font_family', 'pingfang'),
            align=data.get('align', 'center'),
            position=data.get('position', 'bottom'),
            margin=data.get('margin', 20),
            shadow=data.get('shadow'),
            stroke=data.get('stroke'),
        )
        layer.rel_x = data.get('rel_x', 0.5)
        layer.rel_y = data.get('rel_y', 0.9)
        return layer


class CompositeImage:
    """复合图片生成器 - 用于合成最终图片"""
    
    def __init__(self, width, height, bg_color='white'):
        self.width = width
        self.height = height
        self.canvas = Image.new('RGB', (width, height), bg_color)
        self.draw = ImageDraw.Draw(self.canvas)
        
    def add_main_image(self, image, fit_mode='contain'):
        """添加主图片"""
        if not image:
            return
        
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
    
    def add_text_layer(self, text_layer, scale=1.0):
        """添加文字层到画布
        
        Args:
            text_layer: TextLayer 实例
            scale: 缩放比例 (用于导出时按分辨率缩放)
        """
        if not text_layer or not text_layer.content:
            return
        
        rendered, x, y = text_layer.render(self.width, self.height, scale)
        if rendered:
            # 确保画布是 RGBA 模式
            if self.canvas.mode != 'RGBA':
                self.canvas = self.canvas.convert('RGBA')
            self.canvas.paste(rendered, (x, y), rendered)
            # 重新创建 draw 对象
            self.draw = ImageDraw.Draw(self.canvas)
    
    def add_sticker(self, emoji_text, x, y, font_size=64):
        """添加贴纸（表情符号）"""
        try:
            # 使用系统字体支持emoji
            font = ImageFont.truetype("/System/Library/Fonts/Apple Color Emoji.ttc", font_size)
            self.draw.text((x, y), emoji_text, font=font, embedded_color=True)
        except Exception as e:
            print(f"添加贴纸失败: {e}")
            # 降级方案：使用默认字体
            self.draw.text((x, y), emoji_text, fill='black')
    
    
    def add_border(self, border_style):
        """添加边框 (支持图案)"""
        if border_style.get('id', '') == 'none':
            return
        
        width = border_style.get('width', 10)
        color = border_style.get('color', '#000000')
        pattern = border_style.get('pattern', 'solid')
        
        print(f"[DEBUG] add_border: width={width}, color={color}, pattern={pattern}")
        
        # 'solid' 或 'none' 或空值都表示纯色边框
        if pattern in ('solid', 'none', '', None):
            # 纯色边框
            for i in range(width):
                 self.draw.rectangle(
                    [i, i, self.width - 1 - i, self.height - 1 - i],
                    outline=color
                )
        else:
            # 图案边框
            # 获取图案颜色和大小
            pattern_color = border_style.get('pattern_color', '#FFFFFF')
            pattern_size = border_style.get('pattern_size', 10)
            
            # 1. 先创建边框背景层（使用边框主色）
            border_bg = Image.new('RGBA', (self.width, self.height), color)
            
            # 2. 在边框背景上绘制图案（使用图案颜色和大小）
            border_draw = ImageDraw.Draw(border_bg)
            self._draw_pattern(border_draw, pattern, pattern_color, pattern_size, self.width, self.height)
            
            # 3. 创建边框遮罩 (白色为保留区域)
            mask = Image.new('L', (self.width, self.height), 255)
            mask_draw = ImageDraw.Draw(mask)
            # 挖空中间 (黑色为剔除区域)
            mask_draw.rectangle(
                [width, width, self.width - 1 - width, self.height - 1 - width],
                fill=0
            )
            
            # 4. 将边框层通过遮罩覆盖到画布上
            if self.canvas.mode != 'RGBA':
                self.canvas = self.canvas.convert('RGBA')
            self.canvas.paste(border_bg, (0, 0), mask)

    def add_rounded_border(self, border_style):
        """添加圆角边框 (支持图案)"""
        if border_style.get('id', '') == 'none':
            return
        
        width = border_style.get('width', 10)
        color = border_style.get('color', '#000000')
        radius = border_style.get('radius', 20)
        pattern = border_style.get('pattern', 'solid')
        
        # 1. 先应用圆角裁剪 (统一逻辑)
        # 创建圆角矩形遮罩
        mask = Image.new('L', (self.width, self.height), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rounded_rectangle(
            [width, width, self.width - width, self.height - width],
            radius=radius,
            fill=255
        )
        
        # 应用遮罩裁切主内容
        output = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
        if self.canvas.mode != 'RGBA':
            self.canvas = self.canvas.convert('RGBA')
        output.paste(self.canvas, (0, 0), mask)
        self.canvas = output
        self.draw = ImageDraw.Draw(self.canvas)
        
        # 2. 绘制边框
        if pattern == 'solid' or not pattern:
            self.draw.rounded_rectangle(
                [0, 0, self.width - 1, self.height - 1],
                radius=radius,
                outline=color,
                width=width
            )
        else:
            # 图案边框
            pattern_layer = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
            pattern_draw = ImageDraw.Draw(pattern_layer)
            
            self._draw_pattern(pattern_draw, pattern, color, width, self.width, self.height)
            
            # 创建边框遮罩
            border_mask = Image.new('L', (self.width, self.height), 0)
            mask_draw = ImageDraw.Draw(border_mask)
            
            # 外圈白
            mask_draw.rounded_rectangle(
                [0, 0, self.width - 1, self.height - 1],
                radius=radius,
                fill=255
            )
            # 内圈黑 (挖空)
            mask_draw.rounded_rectangle(
                [width, width, self.width - 1 - width, self.height - 1 - width],
                radius=radius,
                fill=0
            )
            
            # 合成
            self.canvas.paste(pattern_layer, (0, 0), border_mask)

    def _draw_pattern(self, draw, pattern_id, color, pattern_size, width, height):
        """绘制图案 (内部辅助方法)"""
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
            spacing = max(pattern_size, 6) # 网格间距与边框宽度相关，这里简化处理，也可传入width作为参考
            if pattern_size > 10: spacing = pattern_size
            
            for x in range(0, width, spacing):
                draw.line([(x, 0), (x, height)], fill=color, width=1)
            for y in range(0, height, spacing):
                draw.line([(0, y), (width, y)], fill=color, width=1)

        elif pattern_id == 'heart':
            # 心形图案
            import math
            spacing = max(pattern_size * 2, 10)
            icon_size = max(pattern_size, 4)
            step = spacing
            
            for y in range(0, height, step):
                for x in range(0, width, step):
                    cx, cy = x + step//2, y + step//2
                    # 简化绘制心形：使用两个圆弧和一个三角形组合，或者贝塞尔曲线
                    # 这里使用简单的点集模拟
                    pts = []
                    for t in range(0, 360, 20): # 角度步长
                        rad = math.radians(t)
                        # 心形公式: x = 16sin^3(t), y = 13cos(t)-5cos(2t)-2cos(3t)-cos(4t)
                        # 坐标系调整：y轴向下为正，需要翻转y
                        px = cx + (icon_size/32) * (16 * math.sin(rad)**3)
                        py = cy - (icon_size/32) * (13 * math.cos(rad) - 5 * math.cos(2*rad) - 2 * math.cos(3*rad) - math.cos(4*rad))
                        pts.append((px, py))
                    
                    if len(pts) > 2:
                        draw.polygon(pts, fill=color, outline=None)

        elif pattern_id == 'club':
            # 梅花图案 (三叶草)
            import math
            spacing = max(pattern_size * 2, 10)
            icon_size = max(pattern_size, 4)
            step = spacing
            r = icon_size / 3  # 叶子半径
            
            for y in range(0, height, step):
                for x in range(0, width, step):
                    cx, cy = x + step//2, y + step//2
                    # 绘制三个圆
                    # 上
                    draw.ellipse([cx-r, cy-r-r, cx+r, cy-r+r], fill=color)
                    # 左下
                    dx = r * math.sin(math.radians(60))
                    dy = r * math.cos(math.radians(60))
                    draw.ellipse([cx-dx-r, cy+dy-r, cx-dx+r, cy+dy+r], fill=color)
                    # 右下
                    draw.ellipse([cx+dx-r, cy+dy-r, cx+dx+r, cy+dy+r], fill=color)
                    # 茎
                    draw.polygon([(cx, cy), (cx-r/3, cy+r*2), (cx+r/3, cy+r*2)], fill=color)

        elif pattern_id == 'triangle':
            # 三角形图案
            spacing = max(pattern_size * 2, 10)
            icon_size = max(pattern_size, 4)
            step = spacing
            h = icon_size * 0.866 # sqrt(3)/2
            
            for y in range(0, height, step):
                for x in range(0, width, step):
                    cx, cy = x + step//2, y + step//2
                    pts = [
                        (cx, cy - h/2),
                        (cx - icon_size/2, cy + h/2),
                        (cx + icon_size/2, cy + h/2)
                    ]
                    draw.polygon(pts, fill=color)

        elif pattern_id == 'diamond':
            # 菱形图案
            spacing = max(pattern_size * 2, 10)
            icon_size = max(pattern_size, 4)
            step = spacing
            r = icon_size / 2
            
            for y in range(0, height, step):
                for x in range(0, width, step):
                    cx, cy = x + step//2, y + step//2
                    pts = [
                        (cx, cy - r),      # 顶
                        (cx + r, cy),      # 右
                        (cx, cy + r),      # 底
                        (cx - r, cy)       # 左
                    ]
                    draw.polygon(pts, fill=color)

        elif pattern_id == 'wave':
            # 波浪 (优化逻辑)
            import math
            amplitude = max(2, pattern_size / 3)
            wavelength = max(10, pattern_size * 2)
            step_y = max(8, pattern_size) # 波浪线之间的垂直距离
            
            # 仅绘制水平波浪线，铺满背景
            x_step = 2 # 绘制精度
            for y_base in range(0, height, int(step_y)):
                points = []
                for x in range(0, width, x_step):
                    # 使用正弦函数生成波浪
                    y = y_base + amplitude * math.sin(x / wavelength * 2 * math.pi)
                    points.append((x, y))
                if len(points) > 1:
                    draw.line(points, fill=color, width=1)

    
    def draw_background_pattern(self, pattern_id, pattern_color, pattern_size=10):
        """绘制背景图案"""
        if not pattern_id or pattern_id == 'none':
            return
            
        width, height = self.width, self.height
        
        if pattern_id == 'stripe':
            # 斜纹图案
            spacing = pattern_size * 2
            for i in range(-height, width + height, spacing):
                self.draw.line(
                    [(i, 0), (i + height, height)],
                    fill=pattern_color, width=1
                )
        
        elif pattern_id == 'dots':
            # 波点图案
            spacing = pattern_size * 2
            dot_radius = pattern_size // 3
            for y in range(0, height + spacing, spacing):
                offset = (y // spacing) % 2 * (spacing // 2)
                for x in range(offset, width + spacing, spacing):
                    self.draw.ellipse(
                        [x - dot_radius, y - dot_radius, x + dot_radius, y + dot_radius],
                        fill=pattern_color, outline=None
                    )
        
        elif pattern_id == 'grid':
            # 网格图案
            spacing = pattern_size * 2
            for x in range(0, width, spacing):
                self.draw.line([(x, 0), (x, height)], fill=pattern_color, width=1)
            for y in range(0, height, spacing):
                self.draw.line([(0, y), (width, y)], fill=pattern_color, width=1)
        
        elif pattern_id == 'horizontal':
            # 横线图案
            spacing = pattern_size * 2
            for y in range(0, height, spacing):
                self.draw.line([(0, y), (width, y)], fill=pattern_color, width=1)
        
        elif pattern_id == 'vertical':
            # 竖线图案
            spacing = pattern_size * 2
            for x in range(0, width, spacing):
                self.draw.line([(x, 0), (x, height)], fill=pattern_color, width=1)
        
        elif pattern_id == 'punch_hole':
            # 打孔纸效果
            # 1. 画横线 (使用传入的颜色或默认浅蓝)
            line_c = pattern_color if pattern_color != '#000000' else '#A0C0E0'
            spacing = max(40, int(pattern_size * 4)) # 行间距大一点
            
            for y in range(spacing, height, spacing):
                self.draw.line([(0, y), (width, y)], fill=line_c, width=1)
                
            # 2. 画竖线 (红色)
            margin_left = int(width * 0.12)
            margin_left = max(50, min(120, margin_left))
            self.draw.line([(margin_left, 0), (margin_left, height)], fill='#FF8080', width=2)
            
            # 3. 画打孔 (左侧居中)
            hole_radius = max(8, int(width * 0.012))
            hole_x = margin_left // 2
            
            num_holes = 3 if height < width else 4
            hole_spacing = height // (num_holes + 1)
            
            for i in range(1, num_holes + 1):
                hy = hole_spacing * i
                # 模拟孔洞 (深灰色)
                self.draw.ellipse(
                    [hole_x - hole_radius, hy - hole_radius, hole_x + hole_radius, hy + hole_radius],
                    fill='#505050', outline=None
                )
    
    def get_image(self):
        """获取最终图片"""
        return self.canvas
    
    def save(self, file_path, quality=95):
        """保存图片"""
        try:
            save_img = self.canvas
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
