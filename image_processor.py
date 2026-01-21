"""
图片处理核心模块
"""

from PIL import Image, ImageDraw, ImageFont, ImageFilter
import io
import os
import random
import math
import hashlib
import platform
from constants import MACARON_COLORS, DOPAMINE_COLORS


class ImageProcessor:
    """图片处理器类"""
    
    def __init__(self):
        self.original_image = None
        self.current_image = None
        self.canvas_size = (800, 800)
        self.text_layers = []
    
    def clear_text_layers(self):
        """清空文字层"""
        self.text_layers = []
        
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
    
    # 字体友好名称映射 (用于UI显示) - 只保留中英文兼容字体
    FONT_NAMES = {
        'yuanti': 'ST圆体 (默认)',
        'pingfang': '苹方',
        'hiragino': '冬青黑体',
        'heiti': 'ST黑体',
        'songti': 'ST宋体',
        'kaiti': 'ST楷体',
    }

    # 字体文件名映射 (用于动态搜索)
    FONT_FILENAMES = {
        'pingfang': ['PingFang.ttc', 'PingFang SC.ttc', 'PingFangUI.ttc'],
        'kaiti': ['Kaiti.ttc', 'STKaiti.ttc', 'STKaiti.ttf', 'simkai.ttf'],
        'yuanti': ['Yuanti.ttc', 'STYuanti.ttc', 'STYuanti.ttf', 'simyou.ttf'],
        'songti': ['Songti.ttc', 'STSongti.ttc', 'simsun.ttc'],
        'heiti': ['STHeiti Light.ttc', 'STHeiti', 'simhei.ttf'],
        'xingkai': ['STXingkai.ttc', 'STXingkai.ttf', 'STXINGKA.TTF'],
        'weibei': ['WeibeiSC-Bold.otf']
    }
    
    _font_search_cache = {}

    @classmethod
    def _find_font_path(cls, family):
        """动态搜索系统字体路径"""
        if family in cls._font_search_cache:
            return cls._font_search_cache[family]
            
        filenames = cls.FONT_FILENAMES.get(family, [])
        if not filenames:
            return None
            
        # 需要搜索的根目录 (macOS AssetsV2 是重点)
        search_roots = [
            '/System/Library/AssetsV2', 
            '/System/Library/PrivateFrameworks',
            '/System/Library/Fonts'
        ]
        
        print(f"[DEBUG] Searching for font family '{family}' in system...")
        for root_dir in search_roots:
            if not os.path.exists(root_dir):
                continue
            for root, dirs, files in os.walk(root_dir):
                for file in files:
                    if file in filenames:
                        full_path = os.path.join(root, file)
                        print(f"[DEBUG] Found font: {full_path}")
                        cls._font_search_cache[family] = full_path
                        return full_path
                        
        cls._font_search_cache[family] = None
        return None

    def __init__(self, content, font_size=48, color='#FFFFFF', font_family='pingfang', 
                 align='center', position='bottom', margin=20, shadow=None, stroke=None, 
                 highlight=None, bold=False, italic=False, underline=False, indent=False):
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
            bold: 加粗
            italic: 斜体
            underline: 下划线
            indent: 首行缩进 (True/False)
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
        self.bold = bold
        self.italic = italic
        self.underline = underline
        self.indent = indent if indent is not None else False
        
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
        
        # 如果静态路径未找到，尝试动态搜索
        if not font_path:
            font_path = self._find_font_path(self.font_family)
        
        # print(f"[DEBUG] _get_font: family='{self.font_family}', resolved_path='{font_path}'")
        
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
    
    @classmethod
    def _get_emoji_font_path(cls):
        """获取系统 emoji 字体路径"""
        system = platform.system()
        if system == 'Darwin':
            paths = [
                '/System/Library/Fonts/Apple Color Emoji.ttc',
                '/System/Library/Fonts/Supplemental/Apple Color Emoji.ttc',
            ]
            for p in paths:
                if os.path.exists(p): return p
        elif system == 'Windows':
            return 'C:/Windows/Fonts/seguiemj.ttf'
        return None

    def _get_emoji_font(self, size):
        """加载 emoji 字体"""
        path = self._get_emoji_font_path()
        if not path: 
            print("[DEBUG] Emoji font path not found")
            return None
        try:
            # Apple Color Emoji 是位图字体，必须匹配特定字号
            # 常见尺寸: 20, 32, 40, 48, 64, 96, 160
            valid_sizes = [20, 32, 40, 48, 64, 96, 160]
            
            # 找到最接近的有效尺寸
            target_size = int(size * 1.0)
            best_size = min(valid_sizes, key=lambda x: abs(x - target_size))
            
            # 如果目标尺寸远大于最大尺寸，或者 PIL支持缩放，尝试直接加载? 
            # 但错误 'invalid pixel size' 说明不支持。
            # 我们直接使用最接近的 size
            return ImageFont.truetype(path, best_size)
        except Exception as e:
            print(f"[DEBUG] Failed to load emoji font (size={size}): {e}")
            return None

    def _split_text_with_emoji(self, text):
        """将文本拆分为 (内容, 是否emoji) 的片段列表"""
        if not text: return []
        import emoji
        
        segments = []
        emoji_list = emoji.emoji_list(text)
        
        last_idx = 0
        for item in emoji_list:
            start = item['match_start']
            end = item['match_end']
            
            # 添加前面的普通文本
            if start > last_idx:
                segments.append((text[last_idx:start], False))
            
            # 添加 emoji
            segments.append((text[start:end], True))
            last_idx = end
            
        # 添加剩余文本
        if last_idx < len(text):
            segments.append((text[last_idx:], False))
            
        return segments

    def _measure_text_width(self, draw, text, font, emoji_font):
        """测量混合文本宽度"""
        segments = self._split_text_with_emoji(text)
        total_width = 0
        for content, is_emoji in segments:
            f = emoji_font if (is_emoji and emoji_font) else font
            bbox = draw.textbbox((0, 0), content, font=f)
            total_width += bbox[2] - bbox[0]
        return total_width

    def render(self, canvas_width, canvas_height, scale=1.0, safe_margin_x=0, safe_margin_y=0):
        """
        渲染文字为 RGBA 图像 (支持 Emoji)
        """
        if not self.content:
            return None, 0, 0
        
        # 缩放参数
        scaled_font_size = int(self.font_size * scale)
        scaled_margin = int(self.margin * scale)
        scaled_stroke_width = int(self.stroke.get('width', 2) * scale) if self.stroke.get('enabled') else 0
        
        # [DEBUG]
        print(f"[DEBUG] Render Layer: font={self.font_family}, size={self.font_size}, stroke={self.stroke}, highlight={self.highlight}")
        
        # 计算额外的内部留白 (padding)
        image_padding = scaled_stroke_width * 2 + int(10 * scale)
        if self.shadow.get('enabled'):
            shadow_offset = self.shadow.get('offset', (2, 2))
            image_padding += max(abs(shadow_offset[0]), abs(shadow_offset[1])) * int(scale) + int(5 * scale)
            
        font = self._get_font(scaled_font_size)
        emoji_font = self._get_emoji_font(scaled_font_size)
        
        # 创建临时画布测量文字
        temp_img = Image.new('RGBA', (1, 1), (0, 0, 0, 0))
        temp_draw = ImageDraw.Draw(temp_img)
        
        # 自动换行处理
        skew_padding = 0
        if self.italic:
            skew_padding = int(scaled_font_size * 2 * 0.2) 
            
        max_text_width = int(canvas_width - (self.margin * 2 * scale) - (safe_margin_x * 2) - (image_padding * 2) - skew_padding)
        aspect_ratio = canvas_width / canvas_height
        if aspect_ratio > 1.2: 
            ratio_limit = 0.7
        else:
            ratio_limit = 0.9
            
        max_text_width = min(max_text_width, int(canvas_width * ratio_limit))
        max_text_width = max(100, max_text_width)
        
        original_lines = self.content.split('\n')
        wrapped_lines = []
        
        for original_line in original_lines:
            if not original_line:
                wrapped_lines.append('')
                continue
                
            if self.indent and self.align != 'center':
                original_line = '\u3000\u3000' + original_line.lstrip()

            # 逐字符测量换行 (支持 Emoji)
            # 为了简化，我们按字符split，但 emoji 需要当做一个单元
            # 使用 split_text_with_emoji 分割，如果 segment 是 text，再逐字拆
            
            raw_segments = self._split_text_with_emoji(original_line)
            # 展平为 units: [(char, is_emoji), ...]
            units = []
            for content, is_emoji in raw_segments:
                if is_emoji:
                    units.append((content, True))
                else:
                    for char in content:
                        units.append((char, False))
            
            current_line_units = []
            current_line_str = ''
            
            for content, is_emoji in units:
                test_str = current_line_str + content
                
                # 测量 test_str 宽度 (近似法：累加)
                # 因为混合字体测量很麻烦，这里用累加判断
                # 或者：构造当前行的 segments 列表进行测量
                
                # 快速测量当前字符宽度
                f = emoji_font if (is_emoji and emoji_font) else font
                char_w = temp_draw.textlength(content, font=f)
                
                # 测量当前累积行宽
                # 为性能考虑，我们维护 current_width
                # 但需要准确，还是调用 _measure_text_width 比较好
                # 优化：只在接近 limit 时精确测量? 
                
                # 这里的逻辑： current_width + char_w
                current_width = self._measure_text_width(temp_draw, current_line_str, font, emoji_font)
                
                if current_width + char_w > max_text_width and current_line_str:
                    # 换行
                    wrapped_lines.append(current_line_str)
                    current_line_units = [(content, is_emoji)]
                    current_line_str = content
                else:
                    current_line_units.append((content, is_emoji))
                    current_line_str += content
            
            if current_line_str:
                wrapped_lines.append(current_line_str)
        
        # 计算每行尺寸
        lines = wrapped_lines
        line_heights = []
        line_widths = []
        
        for line in lines:
            if line:
                w = self._measure_text_width(temp_draw, line, font, emoji_font)
                # 高度取 max (Emoji 往往更高)
                bbox = temp_draw.textbbox((0, 0), "A", font=font) # 基准高度
                h = bbox[3] - bbox[1]
                # 如果有 emoji，可能需要增加高度？
                # 简单处理：使用固定行高 scaled_font_size * 1.2
                # 或者取两者的最大 ascent/descent
                line_widths.append(w)
                line_heights.append(int(scaled_font_size * 1.2)) # 稍微宽松的行高
            else:
                line_widths.append(0)
                line_heights.append(int(scaled_font_size * 1.2))
        
        text_width = max(line_widths) if line_widths else 0
        line_spacing = int(scaled_font_size * 0.2)
        text_height = sum(line_heights) + line_spacing * (len(lines) - 1) if lines else 0
        
        padding = image_padding
        bottom_extra = int(scaled_font_size * 0.3)
        render_width = int(text_width + padding * 2)
        render_height = int(text_height + padding * 2 + bottom_extra)
        
        # [AUTO-SCALE] 检查高度是否溢出
        # 允许的最大高度 = 画布高度 - 边距 - 安全边距
        max_allowed_height = canvas_height - (scaled_margin * 2) - (safe_margin_y * 2)
        
        # 只有在还没缩小到过分小的时候才缩放 (避免无限递归)
        # 假设最小字号对应 scale 0.2 左右
        min_scale_limit = 0.1
        
        if render_height > max_allowed_height and scale > min_scale_limit:
            new_scale = scale * 0.9
            print(f"[DEBUG] Text overflow ({render_height} > {max_allowed_height}), auto-scaling to {new_scale:.2f}")
            return self.render(canvas_width, canvas_height, scale=new_scale, safe_margin_x=safe_margin_x, safe_margin_y=safe_margin_y)

        render_img = Image.new('RGBA', (render_width, render_height), (0, 0, 0, 0))
        render_draw = ImageDraw.Draw(render_img)
        
        draw_x = padding
        draw_y = padding
        
        # 斜体画布调整 logic (保持不变)
        shear_factor = 0.2
        if self.italic:
            slant_offset = int(render_height * shear_factor)
            render_width += slant_offset
            render_img = Image.new('RGBA', (render_width, render_height), (0, 0, 0, 0))
            render_draw = ImageDraw.Draw(render_img)
        
        for i, line in enumerate(lines):
            line_y = draw_y + sum(line_heights[:i]) + line_spacing * i
            
            line_x = draw_x
            if self.align == 'center':
                line_x = draw_x + (text_width - line_widths[i]) // 2
            elif self.align == 'right':
                line_x = draw_x + (text_width - line_widths[i])
            
            if self.italic:
                shift = int(line_y * shear_factor)
                line_x += shift
            
            # 绘制混合文本
            segments = self._split_text_with_emoji(line)
            curr_x = line_x
            
            # 0. 高亮绘制 (目前只支持单行、不精确的背景，因为混合排版高亮很复杂)
            # 我们简化逻辑：如果启用了高亮，我们先画背景，忽略 emoji 的精确位置
            # 或者：遍历 segment，如果是 text 且命中 keyword，画背景
            # [TODO] 恢复高亮逻辑比较复杂，这里先暂时简化为 "不支持 Emoji 的高亮" 或 "简单矩形"
            # 鉴于用户主要是为了 Emoji，我们可以先保证文字渲染正常
            # 恢复高亮逻辑：
            # 需要重新遍历 line 文本，找到 keyword 的 start/end index
            # 然后映射到 visual x 坐标。这需要测量 keyword 之前所有 segment 的宽度。
            
            # --- 重写高亮逻辑 (简化适配) ---
            if self.highlight.get('enabled') and self.highlight.get('keywords'):
                # 简单处理：仅当整个 line 包含 keyword 时，尝试定位
                # 由于 split 导致 index 偏移复杂，我们这里做一个 hack：
                # 重新复用之前的 render_draw 绘制矩形，但位置基于 _measure_text_width
                import re
                for keyword in self.highlight.get('keywords', []):
                    if not keyword: continue
                    try:
                        # 查找所有匹配
                        for match in re.finditer(re.escape(keyword), line):
                            start, end = match.span()
                            # 测量 start 之前的宽度
                            prefix_w = self._measure_text_width(temp_draw, line[:start], font, emoji_font)
                            # 测量 keyword 宽度
                            kw_w = self._measure_text_width(temp_draw, match.group(), font, emoji_font)
                            
                            kw_x = line_x + prefix_w
                            kw_y = line_y + line_heights[i] - int(scaled_font_size * 0.15)
                            
                            
                            # 获取高亮样式
                            h_style = self.highlight.get('style', 'marker')
                            if h_style == 'random':
                                import random
                                h_style = random.choice(['marker', 'full', 'underline'])

                            # 公用逻辑：计算颜色
                            # 绘制高亮
                            h_color = self.highlight.get('color', '#FFB7B2')
                            if h_color == 'random':
                                from constants import BRIGHT_HIGHLIGHT_COLORS
                                h_color = random.choice(BRIGHT_HIGHLIGHT_COLORS)
                            
                            try:
                                if h_color.startswith('#'):
                                    rgb = tuple(int(h_color.lstrip('#')[j:j+2], 16) for j in (0, 2, 4))
                                else: rgb = (255, 183, 178)
                            except: rgb = (255, 183, 178)

                            if h_style == 'full':
                                # [STYLE] Full box background
                                # Draw full height rect behind text
                                # Extend slightly vertically
                                rect_top = line_y - int(scaled_font_size * 0.1)
                                rect_bottom = line_y + line_heights[i] + int(scaled_font_size * 0.1)
                                render_draw.rectangle([kw_x, rect_top, kw_x + kw_w, rect_bottom], fill=rgb + (160,))
                                
                            elif h_style == 'underline':
                                # [STYLE] Underline (thick line)
                                u_h = max(2, int(scaled_font_size * 0.1))
                                u_y = line_y + line_heights[i] - u_h
                                render_draw.rectangle([kw_x, u_y, kw_x + kw_w, u_y + u_h], fill=rgb + (255,))
                                
                            else: # 'marker' (default)
                                # [STYLE] Bottom marker (original)
                                h_h = max(8, int(scaled_font_size * 0.35)) # Slightly taller
                                rect_y = kw_y - h_h + int(scaled_font_size * 0.1)
                                render_draw.rectangle([kw_x, rect_y, kw_x + kw_w, rect_y + h_h], fill=rgb + (160,))
                                
                    except Exception as e:
                        pass
            
            # 1. 绘制文字 (分段)
            stroke_w = scaled_stroke_width if self.stroke.get('enabled') else 0
            stroke_c = self.stroke.get('color', '#000000') if self.stroke.get('enabled') else self.color
            
            for content, is_emoji in segments:
                f = emoji_font if (is_emoji and emoji_font) else font
                args = {'font': f, 'fill': self.color}
                
                # Emoji 特殊处理
                if is_emoji:
                    # 使用 embedded_color 渲染彩色 emoji
                    try:
                        render_draw.text((curr_x, line_y), content, font=f, embedded_color=True)
                    except:
                        # 降级
                        render_draw.text((curr_x, line_y), content, font=f, fill=self.color)
                else:
                    # 普通文字：支持描边、加粗
                    if stroke_w > 0:
                        render_draw.text((curr_x, line_y), content, font=f, fill=self.color, 
                                       stroke_width=stroke_w, stroke_fill=stroke_c)
                    else:
                         render_draw.text((curr_x, line_y), content, font=f, fill=self.color)
                         
                    # 加粗模拟 (Stroke 已经有效果，如果是纯 Bold 且无 Stroke)
                    if self.bold and stroke_w == 0:
                         render_draw.text((curr_x+1, line_y), content, font=f, fill=self.color)
                
                # 移动光标
                w = temp_draw.textlength(content, font=f)
                # PIL textlength 对于 Emoji 可能不准? 使用 bbox 修正
                bbox = temp_draw.textbbox((0, 0), content, font=f)
                w = bbox[2] - bbox[0]
                curr_x += w
            
            # 4. 下划线 (整行)
            if self.underline:
                # 简单重绘一条线
                u_y = line_y + line_heights[i] + 2
                render_draw.rectangle([line_x, u_y, line_x + line_widths[i], u_y + int(scaled_font_size*0.05)], fill=self.color)
        
        # 斜体 Transform
        if self.italic:
            new_width = render_width # Already adjusted
            render_img = render_img.transform(
                (new_width, render_height),
                Image.AFFINE,
                (1, shear_factor, -render_height * shear_factor * 0.5, 0, 1, 0),
                resample=Image.BICUBIC
            )

        x, y = self._calculate_position(canvas_width, canvas_height, 
                                         render_width, render_height, scaled_margin, safe_margin_x, safe_margin_y)
        return render_img, x, y
    
    def _calculate_position(self, canvas_width, canvas_height, text_width, text_height, margin, safe_margin_x=0, safe_margin_y=0):
        """计算文字在画布上的位置"""
        # 处理自定义位置 (拖拽后)
        if self.position == 'custom':
            x = int(self.rel_x * canvas_width)
            y = int(self.rel_y * canvas_height)
            return x, y
            
        # 标准位置处理
        # 水平位置
        if self.align == 'left':
            x = margin + safe_margin_x
        elif self.align == 'right':
            x = canvas_width - text_width - margin - safe_margin_x
        else:  # center
            x = (canvas_width - text_width) // 2

        
        # 垂直位置
        if self.position == 'top':
            y = margin + safe_margin_y
        elif self.position == 'bottom':
            # 底部额外留出空间，避免太贴边
            y = canvas_height - text_height - margin * 2 - safe_margin_y # 底部也稍微避让一下边框
        else:  # center
            y = (canvas_height - text_height) // 2
        
        # [FIX] 强制限制顶部位置，防止超出上边框 (特别是在居中对齐且文字太高时)
        # 无论 vertical position 是什么，y 坐标都不能小于安全边距
        min_y = margin + safe_margin_y
        if y < min_y:
            y = min_y
            
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
            'indent': self.indent,
            'shadow': self.shadow,
            'stroke': self.stroke,
            'highlight': self.highlight,
            'bold': self.bold,
            'italic': self.italic,
            'underline': self.underline,
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
            indent=data.get('indent', False),
            shadow=data.get('shadow'),
            stroke=data.get('stroke'),
            highlight=data.get('highlight'),
            bold=data.get('bold', False),
            italic=data.get('italic', False),
            underline=data.get('underline', False),
        )
        layer.rel_x = data.get('rel_x', 0.5)
        layer.rel_y = data.get('rel_y', 0.9)
        return layer


