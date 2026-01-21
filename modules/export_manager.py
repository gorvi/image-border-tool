"""
导出管理器模块
负责处理图片导出的核心逻辑，包括背景、主图、贴纸、文字和边框的合成
"""

from PIL import Image, ImageDraw, ImageFont
import os
from datetime import datetime
from image_processor import TextLayer
from modules.composite_image import CompositeImage

class ExportManager:
    """导出管理器"""
    
    def __init__(self):
        pass
        
    def create_export_image(self, 
                          preset_width, 
                          preset_height, 
                          background_color,
                          background_pattern,
                          background_pattern_color,
                          background_pattern_size,
                          main_image,
                          main_image_id,
                          canvas_widget, # 需要访问 canvas 获取坐标
                          text_layers,
                          stickers,
                          border_config,
                          main_image_geometry=None, # (x, y, w, h) 目标区域 (可选)
                          main_image_fit_mode='contain', # 'contain' or 'cover'
                          background_image=None): # [NEW] 可选背景图片
        """
        创建导出图片
        """
        
        # 画布显示尺寸
        display_width = canvas_widget.width
        display_height = canvas_widget.height
        
        # 计算缩放比例
        scale_x = preset_width / display_width if display_width > 0 else 1.0
        scale_y = preset_height / display_height if display_height > 0 else 1.0
        
        # 1. 创建背景图层
        final_img = Image.new('RGB', (preset_width, preset_height), background_color)
        
        # [NEW] 绘制背景图片 (如果有)
        if background_image:
             # Scale mode: Cover
             # Resize background image to fill the canvas
             bg_w, bg_h = background_image.size
             ratio_w = preset_width / bg_w
             ratio_h = preset_height / bg_h
             scale = max(ratio_w, ratio_h)
             new_w = int(bg_w * scale)
             new_h = int(bg_h * scale)
             bg_resized = background_image.resize((new_w, new_h), Image.Resampling.LANCZOS)
             
             # Center crop
             left = (new_w - preset_width) // 2
             top = (new_h - preset_height) // 2
             bg_cropped = bg_resized.crop((left, top, left + preset_width, top + preset_height))
             
             # Composite
             if bg_cropped.mode == 'RGBA':
                 final_img.paste(bg_cropped, (0, 0), bg_cropped)
             else:
                 final_img.paste(bg_cropped, (0, 0))
        
        # 2. 绘制背景图案
        if background_pattern and background_pattern != 'none':
            scaled_pattern_size = int(background_pattern_size * max(scale_x, scale_y))
            
            # 使用临时 CompositeImage 实例绘制图案
            temp_comp = CompositeImage(preset_width, preset_height)
            temp_comp.current_image = final_img
            
            temp_comp.render_background_pattern(
                background_pattern,
                background_pattern_color,
                scaled_pattern_size
            )
            final_img = temp_comp.current_image
            
        # 3. 绘制主图片
        if main_image:
            # 优先使用显式传入的几何信息 (用于批量处理)
            if main_image_geometry:
                target_x, target_y, target_w, target_h = main_image_geometry
                
                # 使用 CompositeImage 的辅助方法进行适配绘制
                # 这里我们需要临时的 composite 实例来复用 logic，或者手动实现 fit
                # 为了复用逻辑，我们实例化一个
                comp = CompositeImage(preset_width, preset_height)
                comp.canvas = final_img # 引用传递
                comp.draw = ImageDraw.Draw(comp.canvas)
                
                # 调用 add_main_image_with_geometry 逻辑 (需确保该方法在 CompositeImage 中可用)
                # 如果不可用，手动实现简单的 contain/cover
                
                # 简单实现 smart fit
                img_ratio = main_image.width / main_image.height
                if target_h > 0:
                     box_ratio = target_w / target_h
                else:
                     box_ratio = 1.0
                     
                new_w, new_h = target_w, target_h
                
                if main_image_fit_mode == 'contain':
                    if img_ratio > box_ratio: # 图片更宽，定宽
                        new_w = target_w
                        new_h = int(new_w / img_ratio)
                    else: # 图片更高，定高
                        new_h = target_h
                        new_w = int(new_h * img_ratio)
                else: # cover (简单实现，居中裁剪)
                    # 批量处理通常用 contain 或智能对齐，此处暂且只实现 resize 到目标框中心
                    pass
                    
                # 缩放
                if new_w > 0 and new_h > 0:
                    resized_img = main_image.resize((int(new_w), int(new_h)), Image.Resampling.LANCZOS)
                    # 居中粘贴到目标区域
                    paste_x = int(target_x + (target_w - new_w) / 2)
                    paste_y = int(target_y + (target_h - new_h) / 2)
                    
                    final_img.paste(resized_img, (paste_x, paste_y), resized_img if resized_img.mode == 'RGBA' else None)

            # 否则从 Canvas 获取位置 (单图导出)
            elif main_image_id and canvas_widget:
                # 获取图片在画布上的实际位置
                coords = canvas_widget.canvas.coords(main_image_id)
                if coords:
                    cx, cy = coords
                    # Tkinter 图片坐标是中心点
                    
                    # 按比例缩放
                    scaled_main_w = int(main_image.width * scale_x)
                    scaled_main_h = int(main_image.height * scale_y)
                    scaled_main_pil = main_image.resize((scaled_main_w, scaled_main_h), Image.Resampling.LANCZOS)
                    
                    # 计算粘贴位置
                    paste_x = int(cx * scale_x - scaled_main_w / 2)
                    paste_y = int(cy * scale_y - scaled_main_h / 2)
                    
                    # 粘贴 (处理透明通道)
                    final_img.paste(scaled_main_pil, (paste_x, paste_y), scaled_main_pil if scaled_main_pil.mode == 'RGBA' else None)
        
        # 4. 绘制贴纸
        for sticker in stickers:
            scaled_x = int(sticker['x'] * scale_x)
            scaled_y = int(sticker['y'] * scale_y)
            scaled_size = int(sticker['size'] * max(scale_x, scale_y))
            
            # 绘制不同类型的贴纸
            if sticker.get('is_image'):
                 # 图片贴纸 (PNG)
                 try:
                     sticker_path = sticker.get('path')
                     if sticker_path and os.path.exists(sticker_path):
                         with Image.open(sticker_path) as sticker_img:
                             # 保持比例缩放
                             aspect = sticker_img.width / sticker_img.height
                             new_w = scaled_size
                             new_h = int(new_w / aspect)
                             
                             sticker_img = sticker_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                             if sticker_img.mode != 'RGBA':
                                 sticker_img = sticker_img.convert('RGBA')
                                 
                             # 居中粘贴
                             paste_x = scaled_x - new_w // 2
                             paste_y = scaled_y - new_h // 2
                             final_img.paste(sticker_img, (paste_x, paste_y), sticker_img)
                 except Exception as e:
                     print(f"[ExportManager] Error rendering image sticker: {e}")
            else:
                # Emoji 贴纸
                try:
                    # 使用系统字体绘制 Emoji
                    # 注意：这里简化处理，实际可能需要复杂的 Emoji 渲染逻辑或 fallback 到文本
                    # 也可以尝试使用 composite_image 中的逻辑如果存在，或者直接绘制文本
                    
                    # 简单文本绘制 fallback
                    sticker_draw = ImageDraw.Draw(final_img)
                    try:
                        # 尝试加载支持中文/Emoji的字体
                        font_path = "/System/Library/Fonts/STHeiti Light.ttc"
                        font = ImageFont.truetype(font_path, scaled_size)
                    except:
                        font = ImageFont.load_default()
                    
                    sticker_draw.text((scaled_x, scaled_y), sticker.get('text', ''), fill='black', font=font, anchor="mm")
                    
                except Exception as e:
                    print(f"[ExportManager] Error rendering emoji sticker: {e}")

        # 5. 绘制文字层
        # 使用 border_config 先计算有效边框宽度，用于文字安全边距（Text Wrapping）
        effective_border_width = 0
        if border_config.get('width', 0) > 0: # 统一使用 width > 0 检查
             effective_border_width = int(border_config.get('width', 0) * scale_x)
             
             # [Consistency Fix] 动态调整安全边距
             if preset_width > preset_height:
                 effective_border_width += int(60 * scale_x) # 横屏大边距
             else:
                 effective_border_width += int(10 * scale_x) # 竖屏小边距

        # 优先绘制边框？不，文字通常在边框之下还是之上？
        # 原逻辑：文字在边框之下（被边框遮挡），所以需要 Safe Margin
        # 但原逻辑是在边框之后绘制文字？Wait
        # 查看 main_window.py 原逻辑：
        #   Line 3280: 绘制边框
        #   Line 3293: 绘制文字层 (Moved to be AFTER border...) -> 注释说在边框后，但代码顺序是在边框绘制之后
        #   如果是 After border，那文字会覆盖边框。
        #   但 safe_margin 的存在是为了让文字避开边框区域。
        #   让我们保持原逻辑顺序：先边框，后文字（如果文字需要覆盖边框），或者先文字后边框（如果边框覆盖文字）。
        #   原代码 Line 3280-3289 绘制边框到 final_img
        #   Line 3294 绘制文字
        #   所以是 边框 -> 文字。文字在最上层。
        
        # 5.1 先绘制边框
        composite = CompositeImage(preset_width, preset_height)
        composite.canvas = final_img # 引用传递
        composite.draw = ImageDraw.Draw(composite.canvas)
        
        # [FIX] 缩放边框配置以适配导出分辨率
        scaled_border_config = border_config.copy()
        if 'width' in scaled_border_config:
            scaled_border_config['width'] = int(scaled_border_config['width'] * scale_x)
        if 'radius' in scaled_border_config:
            scaled_border_config['radius'] = int(scaled_border_config['radius'] * scale_x)
        if 'pattern_size' in scaled_border_config:
            scaled_border_config['pattern_size'] = int(scaled_border_config['pattern_size'] * scale_x)

        # 应用边框
        if scaled_border_config.get('radius', 0) > 0:
            composite.add_rounded_border(scaled_border_config)
        else:
            composite.add_border(scaled_border_config)
            
        # 更新 final_img 因为 composite.canvas 可能被重新赋值（虽然 copy 是浅拷贝图片对象，但 PIL Image copy 是深拷贝像素）
        # composite.canvas = final_img.copy() 在 main_window 中是这样
        # 这里我们传入了 final_img，CompositeImage 初始化时会创建新 canvas，我们需要把 final_img 赋给它
        # 或者是让 CompositeImage 在现有的 image 上绘制。
        # CompositeImage 构造函数会创建 self.canvas = Image.new...
        # 所以我们需要替换它。
        
        # 修正：CompositeImage 的用法
        # composite = CompositeImage(w, h)
        # composite.canvas = final_img.copy() ...
        # ... drawing ...
        # final_img = composite.canvas
        final_img = composite.canvas 
        
        # 5.2 绘制文字层 (Top Layer)
        if text_layers:
            # 通常只支持一个文字层？ main_window 里是 self.current_text_layer
            # 但也支持多个？ self.text_layers
            # 原逻辑只处理了 current_text_layer
            
            # 支持传入单个 layer 或 list
            layers_to_draw = text_layers if isinstance(text_layers, list) else [text_layers]
            
            for layer in layers_to_draw:
                if not layer: continue
                
                # [Consistency Fix] 使用 scale=1.0，因为尺寸已经是 preset 尺寸
                # text_scale = 1.0 
                
                # Render
                text_img, tx, ty = layer.render(preset_width, preset_height, scale=1.0,
                                               safe_margin_x=effective_border_width,
                                               safe_margin_y=effective_border_width)
                
                if text_img:
                    if final_img.mode != 'RGBA':
                        final_img = final_img.convert('RGBA')
                    if text_img.mode != 'RGBA':
                        text_img = text_img.convert('RGBA')
                        
                    final_img.paste(text_img, (tx, ty), text_img)
                    
        return final_img
