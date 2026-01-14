"""
图片处理核心模块
"""

from PIL import Image, ImageDraw, ImageFont, ImageFilter
import io


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
            # 1. 创建图案层
            pattern_layer = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
            pattern_draw = ImageDraw.Draw(pattern_layer)
            
            # 复用draw_background_pattern的逻辑，但需要适配
            # 为了更好的代码复用，我们将draw_background_pattern逻辑提取或直接在这里实现
            self._draw_pattern(pattern_draw, pattern, color, width, self.width, self.height)
            
            # 2. 创建边框遮罩 (白色为保留区域)
            mask = Image.new('L', (self.width, self.height), 255)
            mask_draw = ImageDraw.Draw(mask)
            # 挖空中间 (黑色为剔除区域)
            mask_draw.rectangle(
                [width, width, self.width - 1 - width, self.height - 1 - width],
                fill=0
            )
            
            # 3. 将图案层通过遮罩覆盖到画布上
            self.canvas.paste(pattern_layer, (0, 0), mask)

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
        output = Image.new('RGB', (self.width, self.height), 'white')
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

        elif pattern_id == 'wave':
            # 波浪 (复用canvas widget的逻辑，适配PIL)
            import math
            amplitude = max(2, pattern_size / 4)
            wavelength = max(10, pattern_size * 2)
            
            # 简单的全屏波浪线条填充? 不，Canvas是仅在边框处绘制单条波浪线
            # 这里我们尝试绘制满屏波浪，然后Mask裁剪，效果可能更好（类似于波浪纹理）
            # 或者，严格模仿Canvas，只在边缘绘制波浪线？
            # 鉴于Mask逻辑是通用的，我们绘制满屏波浪纹理可能更简单且效果一致
            
            # 这里为了简单，我们绘制水平波浪线铺满屏幕
            step = max(4, int(wavelength / 4))
            for y_base in range(0, height, int(wavelength/2)): # 间距
                points = []
                for x in range(0, width, step):
                    y = y_base + amplitude * math.sin(x / wavelength * 2 * math.pi)
                    points.append((x, y))
                if len(points) > 1:
                    draw.line(points, fill=color, width=1)
            
            # 垂直波浪
            for x_base in range(0, width, int(wavelength/2)):
                points = []
                for y in range(0, height, step):
                    x = x_base + amplitude * math.sin(y / wavelength * 2 * math.pi)
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
    
    def get_image(self):
        """获取最终图片"""
        return self.canvas
    
    def save(self, file_path, quality=95):
        """保存图片"""
        try:
            self.canvas.save(file_path, quality=quality, optimize=True)
            return True
        except Exception as e:
            print(f"保存失败: {e}")
            return False
