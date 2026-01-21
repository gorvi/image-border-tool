"""
批量处理器模块
负责批量图片处理、随机化配置生成和 Excle 文字替换逻辑
"""

import os
import random
import pandas as pd
from PIL import Image
from constants import (MACARON_COLORS, BORDER_PATTERNS)
from image_processor import ImageProcessor

class BatchProcessor:
    """批量处理器"""
    
    def __init__(self, export_manager):
        self.export_manager = export_manager
        self.log_callback = None
        
    def set_log_callback(self, callback):
        """设置日志回调函数"""
        self.log_callback = callback
        
    def log(self, message):
        """记录日志"""
        if self.log_callback:
            self.log_callback(message)
        else:
            print(f"[BatchProcessor] {message}")

    def process_batch(self,
                     images_to_process,
                     output_dir,
                     preset_config, # width, height
                     base_border_config,
                     random_options, # {color, style, pattern, background}
                     text_config, # {use_text_dir, text_dir, text_mapping, text_sequence, template_layer}
                     sticker_config, # list of stickers
                     background_config, # {color, pattern, pattern_color, pattern_size}
                     canvas_widget, # needed for geometry calculation and legacy support
                     match_canvas_geom=False, # 是否匹配画布主图位置
                     image_as_bg=False # [NEW] 图片作为背景
                     ):
        """
        执行批量处理
        """
        from constants import MACARON_COLORS, DOPAMINE_COLORS, BORDER_PATTERNS, BORDER_LINE_STYLES
        
        success_count = 0
        preset_width = preset_config['width']
        preset_height = preset_config['height']
        
        # 确定源类型
        source_type = 'image' if images_to_process and images_to_process[0] else 'text_only'
        
        # 预计算预览缩放比例 (用于某些基于预览大小的计算，如果有的话)
        display_width = canvas_widget.width
        preview_scale = preset_width / display_width if display_width > 0 else 1.0
        
        # 临时 ImageProcessor (用于加载图片)
        processor = ImageProcessor()
        
        for idx, img_path in enumerate(images_to_process):
            # 1. 确定文件名
            # [FIX] 统一文件名规则: 源文件名/ID + 年月日时分秒毫秒
            import datetime
            timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')[:-3]
            
            if img_path:
                base_name = os.path.basename(img_path)
                file_root, _ = os.path.splitext(base_name)
                filename = f"{file_root}_{timestamp}.png"
            else:
                # 纯文字模式，尝试从 Excel 序列获取文件名或使用默认
                text_row = text_config.get('text_sequence', [])[idx] if idx < len(text_config.get('text_sequence', [])) else {}
                # 尝试查找通常用作文件名的列
                file_root = f"text_{idx+1:04d}"
                # 扩展文件名匹配关键字: 加上 'Image Name', '图片名称'
                for key in ['Image Name', '图片名称', '文件名', 'filename', 'ID', 'id']:
                    if key in text_row and str(text_row[key]).strip():
                        file_root = str(text_row[key]).strip()
                        break
                
                filename = f"{file_root}_{timestamp}.png"
                
            self.log(f"[{idx+1}/{len(images_to_process)}] 处理: {filename}")
            
            try:
                # 2. 准备配置 (Border)
                current_border_config = base_border_config.copy()
                
                # 随机化边框
                log_details = []
                if random_options.get('color'):
                    # 简单随机逻辑 (需要引入 main_window 的逻辑或在此重新实现)
                    # 暂时为了简单，这里需要传入随机生成器或逻辑
                    # 简化：随机 Hex 颜色
                     current_border_config['color'] = "#{:06x}".format(random.randint(0, 0xFFFFFF))
                     log_details.append(f"随机边框色")
                     
                if random_options.get('style'):
                     # BORDER_LINE_STYLES 是列表，需要提取 id
                     from constants import BORDER_LINE_STYLES
                     styles = [s['id'] for s in BORDER_LINE_STYLES]
                     current_border_config['line_style'] = random.choice(styles)
                     log_details.append(f"随机样式:{current_border_config['line_style']}")
                     
                if random_options.get('pattern'):
                     from constants import BORDER_PATTERNS
                     patterns = [p['id'] for p in BORDER_PATTERNS]
                     current_border_config['pattern'] = random.choice(patterns)
                     # 自动调整大小
                     current_border_config['pattern_size'] = max(4, int(current_border_config.get('width', 10) * 0.6))
                     log_details.append(f"随机图案:{current_border_config['pattern']}")

                # 3. 准备配置 (Background)
                current_bg_color = background_config.get('color')
                current_bg_pattern = background_config.get('pattern')
                current_bg_pattern_color = background_config.get('pattern_color')
                current_bg_pattern_size = background_config.get('pattern_size')
                
                if random_options.get('background'):
                    # 随机背景逻辑
                    current_bg_color = random.choice(MACARON_COLORS)
                    
                    pattern_ids = [p['id'] for p in BORDER_PATTERNS]
                    current_bg_pattern = random.choice(pattern_ids)
                    
                    # pattern color based on bg color
                    try:
                        bg_rgb = tuple(int(current_bg_color.lstrip('#')[i:i+2], 16) for i in (0,2,4))
                        pattern_rgb = tuple(max(0, int(c * 0.7)) for c in bg_rgb)
                        current_bg_pattern_color = '#{:02X}{:02X}{:02X}'.format(*pattern_rgb)
                    except:
                        current_bg_pattern_color = '#CCCCCC'
                        
                    current_bg_pattern_size = random.randint(8, 20)
                    log_details.append(f"随机背景")

                # 4. 加载主图片 & 计算几何信息
                batch_main_image = None
                batch_geometry = None # (x, y, w, h)
                batch_bg_image = None # [FIX] Initialize variable
                fit_mode = 'contain'
                
                if img_path:
                    processor.load_image(img_path)
                    # processor.resize_to_canvas... 不，我们不需要在这里缩放，
                    # ExportManager 需要原始图片和目标区域
                    batch_main_image = processor.get_current_image()
                    
                    # [NEW] 处理图片作为背景
                    batch_bg_image = None
                    if image_as_bg and batch_main_image:
                        # 转换为 RGBA
                        if batch_main_image.mode != 'RGBA':
                            batch_main_image = batch_main_image.convert('RGBA')
                        
                        # 设置透明度 50% (128/255)
                        # 注意: putalpha 会替换原有 alpha。如果原图有透明度，最好 merge。
                        # 这里简单处理: 假设原图是不透明照片。
                        # Create a solid alpha mask
                        alpha = Image.new('L', batch_main_image.size, 128)
                        batch_main_image.putalpha(alpha)
                        
                        batch_bg_image = batch_main_image
                        batch_main_image = None # 移除主图身份，转为背景

                    
                    if match_canvas_geom:
                        # 计算目标几何信息
                        # 需要调用 canvas_widget.get_main_image_geometry()
                        # 注意：这需要 canvas 上必须有主图供参考
                        geom = canvas_widget.get_main_image_geometry()
                        if geom:
                            rel_x, rel_y, rel_w, rel_h = geom
                            target_x = rel_x * preset_width
                            target_y = rel_y * preset_height
                            target_w = rel_w * preset_width
                            target_h = rel_h * preset_height
                            batch_geometry = (target_x, target_y, target_w, target_h)
                            
                            # 对齐与 Fit 模式判断 (复用原有逻辑)
                            # 简化为默认 contain，ExportManager 内有简单 fit 实现
                        else:
                             # 默认全屏
                             batch_geometry = (0, 0, preset_width, preset_height)
                    else:
                        # 默认适应画布
                        batch_geometry = (0, 0, preset_width, preset_height)
                        log_details.append("位置: 默认全屏适应")

                # 5. 文字处理 (Excel 替换)
                text_layers = []
                template_layer = text_config.get('template_layer')
                
                # [DEBUG] 检查模板源
                if template_layer:
                     # Check if content is empty?
                     if not template_layer.content or not str(template_layer.content).strip():
                         template_layer = None # Treat empty layer as None
                         print("[DEBUG] Template layer exists but empty -> ignore")
                     else:
                         print("[DEBUG] Using Existing Template Layer from Config")
                else:
                     print("[DEBUG] No Template Layer -> will create dynamic")

                # 如果没有模版层但有文字数据，创建默认文字层
                if not template_layer and text_config.get('use_text_dir'):
                    text_seq = text_config.get('text_sequence', [])
                    text_seq = text_config.get('text_sequence', [])
                    # [FIX] 支持循环使用文字 (移除 idx < len 限制)
                    if text_seq:
                        from image_processor import TextLayer
                        # [FIX] 使用取模运算
                        row = text_seq[idx % len(text_seq)]
                        # 从 dict 中提取 content
                        if isinstance(row, dict):
                            content = row.get('content') or row.get('文字内容') or str(list(row.values())[0])
                        else:
                            content = str(row)
                        content = content.replace('\\n', '\n')
                        # 创建默认文字层 (带动态随机样式 - 仿摇一摇逻辑)
                        default_font_size = text_config.get('default_font_size', 48)
                        default_font_family = text_config.get('default_font_family', 'PingFang SC')
                        
                        # 计算背景亮度 (简单估算)
                        bg_color = current_bg_color.lstrip('#')
                        try:
                            r = int(bg_color[0:2], 16)
                            g = int(bg_color[2:4], 16)
                            b = int(bg_color[4:6], 16)
                            brightness = (r * 299 + g * 587 + b * 114) / 1000
                        except:
                            brightness = 200 # 默认浅色背景
                            
                        # 根据亮度选择文字颜色
                        # 恢复全随机颜色，但通过描边保证可读性
                        # 以前的逻辑可能是完全随机? 用户说"以前是实现的"
                        # 我们使用多巴胺/马卡龙色系 + 基础色
                        from constants import MACARON_COLORS, DOPAMINE_COLORS
                        all_colors = MACARON_COLORS + DOPAMINE_COLORS + ['#FFFFFF', '#000000', '#FF2D55', '#FFCC00']
                        text_color = random.choice(all_colors)
                        
                        # 根据文字亮度决定描边颜色，而不是背景
                        # 这样无论背景如何，文字本身都自带对比度
                        try:
                            tc = text_color.lstrip('#')
                            tr, tg, tb = int(tc[0:2], 16), int(tc[2:4], 16), int(tc[4:6], 16)
                            text_brightness = (tr * 299 + tg * 587 + tb * 114) / 1000
                            stroke_color = '#FFFFFF' if text_brightness < 128 else '#000000'
                        except:
                            stroke_color = '#FFFFFF'
                        
                            
                        template_layer = TextLayer(
                            content=content,
                            font_size=default_font_size,
                            color=text_color,
                            font_family=default_font_family,
                            align='left', # [FIX] 改为左对齐
                            position='center', # 整体居中，但内部文字左对齐
                            margin=40 # [FIX] 增加边距，优化视觉 (原20)
                        )
                        
                        # 添加对比度描边
                        template_layer.stroke = {
                            'enabled': True,
                            'color': stroke_color,
                            'width': 2 # [FIX]稍微减细一点描边，原3
                        }
                        
                        # 总是启用 'random' 高亮 (类似摇一摇效果)
                        # 注意：需要确保 ImageProcessor 支持 random 值
                        template_layer.highlight = {
                            'enabled': True,
                            'color': 'random', # 让 ImageProcessor 处理
                            'opacity': 0.6
                        }
                        
                        log_details.append(f"文字(随机样式): {content[:10]}...")
                
                if template_layer:
                    # 创建副本
                    new_layer = self._clone_text_layer(template_layer)
                    
                    # [FIX] 如果是自动生成的默认层，确保样式被正确传递
                    if not text_config.get('template_layer') and template_layer.stroke.get('enabled'):
                        new_layer.stroke = template_layer.stroke.copy()
                        new_layer.highlight = template_layer.highlight.copy()
                        
                    # [FIX] 即使有模板层，如果开启了随机样式，也强制随机化文字颜色和描边
                    # 这样能解决 "导出的文字颜色不随机" 问题
                    if random_options.get('color') or random_options.get('style'):
                         from constants import MACARON_COLORS, DOPAMINE_COLORS
                         all_colors = MACARON_COLORS + DOPAMINE_COLORS + ['#FFFFFF', '#000000', '#FF2D55', '#FFCC00']
                         r_text_color = random.choice(all_colors)
                         new_layer.color = r_text_color
                         
                         # 重新计算描边
                         try:
                            tc = r_text_color.lstrip('#')
                            tr, tg, tb = int(tc[0:2], 16), int(tc[2:4], 16), int(tc[4:6], 16)
                            tbright = (tr * 299 + tg * 587 + tb * 114) / 1000
                            r_stroke_color = '#FFFFFF' if tbright < 128 else '#000000'
                         except:
                            r_stroke_color = '#FFFFFF'
                            
                         new_layer.stroke = {
                            'enabled': True,
                            'color': r_stroke_color,
                            'width': 3
                         }
                         # 高亮也随机
                         keywords = template_layer.highlight.get('keywords', []) if template_layer.highlight else []
                         # 如果没有关键词，使用 NLP 算法提取 (jieba)
                         if not keywords and new_layer.content:
                            try:
                                import jieba.analyse
                                # 提取前5个关键词
                                new_keywords = jieba.analyse.extract_tags(new_layer.content, topK=5, withWeight=False)
                                keywords.extend(new_keywords)
                                log_details.append(f"AI高亮词: {','.join(new_keywords)}")
                                print(f"[DEBUG] Jieba Extracted Keywords for '{new_layer.content[:10]}...': {new_keywords}")
                            except ImportError:
                                print("[DEBUG] Jieba module not found")
                                pass
                            except Exception as e:
                                print(f"[Batch] Keyword extraction failed: {e}")
                         else:
                             print(f"[DEBUG] Skipping NLP: keywords={keywords}, content_len={len(new_layer.content) if new_layer.content else 0}")
                         
                         new_layer.highlight = {
                            'enabled': True,
                            'keywords': keywords,
                            'color': 'random',
                            'style': 'random' # [FIX] 让 render 阶段决定，实现同一图片多种样式混搭
                         }
                         
                         # 随机字体
                         fonts = ['yuanti', 'kaiti', 'songti', 'heiti', 'pingfang', 'Arial']
                         new_layer.font_family = random.choice(fonts)
                    
                    # 替换内容
                    if text_config.get('use_text_dir'):
                        # 1. 按文件名匹配 (Mapping)
                        if file_root in text_config.get('text_mapping', {}):
                            new_content = text_config['text_mapping'][file_root]
                            new_layer.content = str(new_content).replace('\\n', '\n')
                            log_details.append(f"文字替换(Map): {new_layer.content[:5]}...")
                        # 2. 按顺序匹配 (Sequence) - 支持循环使用
                        elif text_config.get('text_sequence'):
                             seq = text_config.get('text_sequence', [])
                             if seq:
                                 # [FIX] 使用取模运算实现循环
                                 row_idx = idx % len(seq)
                                 row = seq[row_idx]
                             if row:
                                 if isinstance(row, dict):
                                     new_content = row.get('content') or row.get('文字内容') or str(list(row.values())[0])
                                 else:
                                     new_content = str(row)
                                 new_layer.content = new_content.replace('\\n', '\n')
                                 log_details.append(f"文字替换(Seq): {new_layer.content[:5]}...")
                    
                    text_layers.append(new_layer)

                if log_details:
                    self.log(f"  配置: {'; '.join(log_details)}")

                # 6. 调用 ExportManager
                final_img = self.export_manager.create_export_image(
                    preset_width=preset_width,
                    preset_height=preset_height,
                    background_color=current_bg_color,
                    background_pattern=current_bg_pattern,
                    background_pattern_color=current_bg_pattern_color,
                    background_pattern_size=current_bg_pattern_size,
                    main_image=batch_main_image,
                    main_image_id=None, # 批量模式不需要 ID
                    canvas_widget=canvas_widget, # 仍需传入以支持某些兼容性逻辑
                    text_layers=text_layers,
                    stickers=sticker_config,
                    border_config=current_border_config,
                    main_image_geometry=batch_geometry,
                    main_image_fit_mode=fit_mode,
                    background_image=batch_bg_image # [NEW] 传入背景图
                )
                
                # 7. 保存
                save_path = os.path.join(output_dir, filename)
                final_img.save(save_path)
                success_count += 1
                
                # Yield 用于更新进度条 (0-100)
                yield (idx + 1) / len(images_to_process) * 100
                
            except Exception as e:
                self.log(f"  ❌ 失败: {str(e)}")
                import traceback
                traceback.print_exc()
        
        self.log(f"═══ 完成: 成功 {success_count}/{len(images_to_process)} ═══")
        
    def _clone_text_layer(self, layer):
        """克隆文字层对象"""
        from image_processor import TextLayer
        # 创建新实例
        new_layer = TextLayer(
            content=layer.content,
            font_size=layer.font_size,
            color=layer.color,
            font_family=layer.font_family,
            align=layer.align,
            position=layer.position,
            margin=layer.margin
        )
        # 复制其他属性
        new_layer.rel_x = layer.rel_x
        new_layer.rel_y = layer.rel_y
        new_layer.shadow = layer.shadow.copy() if layer.shadow else {}
        new_layer.stroke = layer.stroke.copy() if layer.stroke else {}
        new_layer.highlight = layer.highlight.copy() if layer.highlight else {}
        new_layer.bold = layer.bold
        new_layer.italic = layer.italic
        new_layer.underline = layer.underline
        new_layer.indent = layer.indent
        new_layer.line_spacing = getattr(layer, 'line_spacing', 1.5)
        new_layer.letter_spacing = getattr(layer, 'letter_spacing', 0)
        
        return new_layer
