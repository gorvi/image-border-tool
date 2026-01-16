"""
常量定义模块
"""

# 预设尺寸
SIZE_PRESETS = [
    {
        'id': 'id_photo_1inch',
        'name': '1寸证件照',
        'width': 295,
        'height': 413,
        'dpi': 300
    },
    {
        'id': 'id_photo_2inch',
        'name': '2寸证件照',
        'width': 413,
        'height': 626,
        'dpi': 300
    },
    {
        'id': 'square_1_1',
        'name': '正方形 1:1',
        'width': 800,
        'height': 800,
        'dpi': 72
    },
    {
        'id': 'xiaohongshu_3_4',
        'name': '小红书 3:4',
        'width': 1242,
        'height': 1660,
        'dpi': 72
    },
    {
        'id': 'post_16_9',
        'name': '横版海报 16:9',
        'width': 1920,
        'height': 1080,
        'dpi': 72
    },
    {
        'id': 'post_9_16',
        'name': '竖版海报 9:16',
        'width': 1080,
        'height': 1920,
        'dpi': 72
    },
    {
        'id': 'custom',
        'name': '自定义尺寸',
        'width': 800,
        'height': 800,
        'dpi': 72
    }
]

# 边框样式
BORDER_STYLES = [
    {'id': 'none', 'name': '无边框', 'width': 0, 'color': '#000000'},
    {'id': 'simple', 'name': '简单边框', 'width': 10, 'color': '#000000'},
    {'id': 'thick', 'name': '粗边框', 'width': 20, 'color': '#333333'},
    {'id': 'white', 'name': '白色边框', 'width': 15, 'color': '#FFFFFF'},
    {'id': 'rounded', 'name': '圆角边框', 'width': 10, 'color': '#000000', 'radius': 20},
]

# 贴纸列表（支持PNG图片）
STICKER_LIST = [
    # 表情
    {'id': 'heart', 'emoji': '❤️', 'name': '爱心'},
    {'id': 'star', 'emoji': '⭐', 'name': '星星'},
    {'id': 'smile', 'emoji': '😊', 'name': '笑脸'},
    {'id': 'fire', 'emoji': '🔥', 'name': '火焰'},
    {'id': 'sparkles', 'emoji': '✨', 'name': '闪光'},
    {'id': 'flower', 'emoji': '🌸', 'name': '花朵'},
    {'id': 'crown', 'emoji': '👑', 'name': '皇冠'},
    {'id': 'ribbon', 'emoji': '🎀', 'name': '蝴蝶结'},
    {'id': 'cake', 'emoji': '🎂', 'name': '蛋糕'},
    {'id': 'gift', 'emoji': '🎁', 'name': '礼物'},
    {'id': 'balloon', 'emoji': '🎈', 'name': '气球'},
    {'id': 'music', 'emoji': '🎵', 'name': '音符'},
    # 更多表情
    {'id': 'laughing', 'emoji': '😂', 'name': '大笑'},
    {'id': 'cool', 'emoji': '😎', 'name': '墨镜'},
    {'id': 'wink', 'emoji': '😉', 'name': '眨眼'},
    {'id': 'kiss', 'emoji': '😘', 'name': '飞吻'},
    {'id': 'love_eyes', 'emoji': '😍', 'name': '花痴'},
    {'id': 'thinking', 'emoji': '🤔', 'name': '思考'},
    {'id': 'clap', 'emoji': '👏', 'name': '鼓掌'},
    {'id': 'party', 'emoji': '🥳', 'name': '派对'},
    # 动物
    {'id': 'dog', 'emoji': '🐶', 'name': '狗狗'},
    {'id': 'cat', 'emoji': '🐱', 'name': '猫咪'},
    {'id': 'bunny', 'emoji': '🐰', 'name': '兔子'},
    {'id': 'bear', 'emoji': '🐻', 'name': '小熊'},
    {'id': 'panda', 'emoji': '🐼', 'name': '熊猫'},
    {'id': 'unicorn', 'emoji': '🦄', 'name': '独角兽'},
    {'id': 'butterfly', 'emoji': '🦋', 'name': '蝴蝶'},
    {'id': 'bee', 'emoji': '🐝', 'name': '蜜蜂'},
    # 食物
    {'id': 'pizza', 'emoji': '🍕', 'name': '披萨'},
    {'id': 'donut', 'emoji': '🍩', 'name': '甜甜圈'},
    {'id': 'icecream', 'emoji': '🍦', 'name': '冰淇淋'},
    {'id': 'coffee', 'emoji': '☕', 'name': '咖啡'},
    {'id': 'watermelon', 'emoji': '🍉', 'name': '西瓜'},
    {'id': 'strawberry', 'emoji': '🍓', 'name': '草莓'},
    {'id': 'cherry', 'emoji': '🍒', 'name': '樱桃'},
    {'id': 'lollipop', 'emoji': '🍭', 'name': '棒棒糖'},
    # 天气/自然
    {'id': 'sun', 'emoji': '☀️', 'name': '太阳'},
    {'id': 'moon', 'emoji': '🌙', 'name': '月亮'},
    {'id': 'rainbow', 'emoji': '🌈', 'name': '彩虹'},
    {'id': 'cloud', 'emoji': '☁️', 'name': '云朵'},
    {'id': 'snowflake', 'emoji': '❄️', 'name': '雪花'},
    {'id': 'lightning', 'emoji': '⚡', 'name': '闪电'},
    {'id': 'droplet', 'emoji': '💧', 'name': '水滴'},
    {'id': 'leaf', 'emoji': '🍃', 'name': '树叶'},
    # 手势/符号
    {'id': 'thumbsup', 'emoji': '👍', 'name': '点赞'},
    {'id': 'ok', 'emoji': '👌', 'name': 'OK'},
    {'id': 'victory', 'emoji': '✌️', 'name': '胜利'},
    {'id': 'rock', 'emoji': '🤘', 'name': '摇滚'},
    {'id': 'pray', 'emoji': '🙏', 'name': '祈祷'},
    {'id': 'check', 'emoji': '✅', 'name': '完成'},
    {'id': 'cross', 'emoji': '❌', 'name': '错误'},
    {'id': 'hundred', 'emoji': '💯', 'name': '满分'},
    # 物品
    {'id': 'diamond', 'emoji': '💎', 'name': '钻石'},
    {'id': 'rocket', 'emoji': '🚀', 'name': '火箭'},
    {'id': 'camera', 'emoji': '📷', 'name': '相机'},
    {'id': 'megaphone', 'emoji': '📣', 'name': '喇叭'},
    {'id': 'trophy', 'emoji': '🏆', 'name': '奖杯'},
    {'id': 'medal', 'emoji': '🏅', 'name': '奖牌'},
    {'id': 'key', 'emoji': '🔑', 'name': '钥匙'},
    {'id': 'bell', 'emoji': '🔔', 'name': '铃铛'},
]

# 边框图案定义
BORDER_PATTERNS = [
    {'id': 'none', 'name': '无', 'icon': '○'},
    {'id': 'stripe', 'name': '斜纹', 'icon': '╱'},
    {'id': 'dots', 'name': '波点', 'icon': '●'},
    {'id': 'grid', 'name': '网格', 'icon': '▦'},
    {'id': 'wave', 'name': '波浪', 'icon': '〰'},
    {'id': 'heart', 'name': '心形', 'icon': '♥'},
    {'id': 'club', 'name': '梅花', 'icon': '♣'},
    {'id': 'triangle', 'name': '三角形', 'icon': '▲'},
    {'id': 'diamond', 'name': '菱形', 'icon': '◆'},
]

# 线条样式定义
LINE_STYLES = [
    {'id': 'solid', 'name': '实线'},
    {'id': 'dashed', 'name': '虚线'},
    {'id': 'dotted', 'name': '点线'},
    {'id': 'double', 'name': '双线'},
]

# 预设颜色列表（用于随机）
PRESET_COLORS = [
    '#000000', '#FFFFFF', '#FF0000', '#00FF00', '#0000FF',
    '#FFFF00', '#00FFFF', '#FF00FF', '#C0C0C0', '#808080',
    '#800000', '#808000', '#008000', '#800080', '#008080',
    '#000080', '#FF4500', '#DA70D6', '#EEE8AA', '#98FB98',
    '#AFEEEE', '#DB7093', '#FFEFD5', '#FFDAB9', '#CD853F',
    '#FFC0CB', '#DDA0DD', '#B0E0E6', '#800080', '#FF0000',
    '#BC8F8F', '#4169E1', '#8B4513', '#FA8072', '#FAA460',
    '#2E8B57', '#FFF5EE', '#A0522D', '#C0C0C0', '#87CEEB',
    '#6A5ACD', '#708090', '#FFFAFA', '#00FF7F', '#4682B4',
    '#D2B48C', '#008080', '#D8BFD8', '#FF6347', '#40E0D0',
    '#EE82EE', '#F5DEB3', '#FFFFFF', '#F5F5F5', '#FFFF00',
    '#9ACD32'
]

# 边框样式（增加预览图）
BORDER_STYLES_WITH_PREVIEW = [
    {'id': 'none', 'name': '无边框', 'width': 0, 'color': '#000000', 'preview': None},
    {'id': 'simple', 'name': '简单边框', 'width': 10, 'color': '#000000', 'preview': 'simple.png'},
    {'id': 'thick', 'name': '粗边框', 'width': 20, 'color': '#333333', 'preview': 'thick.png'},
    {'id': 'white', 'name': '白色边框', 'width': 15, 'color': '#FFFFFF', 'preview': None},
    {'id': 'rounded', 'name': '圆角边框', 'width': 10, 'color': '#000000', 'radius': 20, 'preview': 'rounded.png'},
    {'id': 'double', 'name': '双线边框', 'width': 15, 'style': 'double', 'preview': 'double.png'},
    {'id': 'decorative', 'name': '装饰边框', 'width': 15, 'color': '#FFD700', 'preview': 'decorative.png'},
]

# 专业边框分类
BORDER_CATEGORIES = {
    'modern': {
        'name': '🎨 现代',
        'styles': ['simple', 'double', 'shadow', 'rounded', 'dashed', 'gradient', 'decorative'],
        'colors': ['black', 'white', 'blue', 'red', 'green', 'purple']
    },
    'vintage': {
        'name': '📜 复古',
        'styles': ['vintage'],
        'colors': ['brown', 'gold', 'black']
    },
    'cute': {
        'name': '💕 可爱',
        'styles': ['cute'],
        'colors': ['pink', 'purple', 'cyan', 'yellow', 'orange', 'green']
    }
}

# 边框颜色选项
BORDER_COLORS = {
    'black': {'name': '黑色', 'hex': '#000000', 'preview': '#000000'},
    'white': {'name': '白色', 'hex': '#FFFFFF', 'preview': '#DDDDDD'},
    'red': {'name': '红色', 'hex': '#FF3B30', 'preview': '#FF3B30'},
    'pink': {'name': '粉色', 'hex': '#FF2D55', 'preview': '#FF2D55'},
    'purple': {'name': '紫色', 'hex': '#AF52DE', 'preview': '#AF52DE'},
    'blue': {'name': '蓝色', 'hex': '#007AFF', 'preview': '#007AFF'},
    'cyan': {'name': '青色', 'hex': '#5AC8FA', 'preview': '#5AC8FA'},
    'green': {'name': '绿色', 'hex': '#34C759', 'preview': '#34C759'},
    'yellow': {'name': '黄色', 'hex': '#FFCC00', 'preview': '#FFCC00'},
    'orange': {'name': '橙色', 'hex': '#FF9500', 'preview': '#FF9500'},
    'brown': {'name': '棕色', 'hex': '#8B4513', 'preview': '#8B4513'},
    'gold': {'name': '金色', 'hex': '#FFD700', 'preview': '#FFD700'},
}

# 边框样式名称（中文）
BORDER_STYLE_NAMES = {
    'simple': '简约',
    'double': '双线',
    'shadow': '阴影',
    'rounded': '圆角',
    'dashed': '虚线',
    'gradient': '渐变',
    'decorative': '装饰',
    'vintage': '复古',
    'cute': '可爱',
}

# 边框形状选项
BORDER_SHAPES = [
    {'id': 'rectangle', 'name': '矩形', 'icon': '▭'},
    {'id': 'rounded_rect', 'name': '圆角矩形', 'icon': '▢'},
    {'id': 'circle', 'name': '圆形', 'icon': '○'},
    {'id': 'ellipse', 'name': '椭圆', 'icon': '⬭'},
]

# 边框线条样式
BORDER_LINE_STYLES = [
    {'id': 'solid', 'name': '实线', 'icon': '━'},
    {'id': 'dashed', 'name': '虚线', 'icon': '┅'},
    {'id': 'dotted', 'name': '点线', 'icon': '···'},
    {'id': 'double', 'name': '双线', 'icon': '═'},
]



# 背景图案样式
BACKGROUND_PATTERNS = [
    {'id': 'none', 'name': '纯色', 'icon': '■'},
    {'id': 'stripe', 'name': '斜纹', 'icon': '╱'},
    {'id': 'dots', 'name': '波点', 'icon': '●'},
    {'id': 'grid', 'name': '网格', 'icon': '▦'},
    {'id': 'horizontal', 'name': '横线', 'icon': '═'},
    {'id': 'vertical', 'name': '竖线', 'icon': '║'},
    {'id': 'punch_hole', 'name': '打孔纸', 'icon': '○='},
]

# 默认背景色
DEFAULT_BACKGROUNDS = [
    {'id': 'white', 'name': '纯白', 'color': '#FFFFFF'},
    {'id': 'light_gray', 'name': '浅灰', 'color': '#F5F5F5'},
    {'id': 'cream', 'name': '米色', 'color': '#FFF8DC'},
    {'id': 'light_blue', 'name': '浅蓝', 'color': '#E3F2FD'},
    {'id': 'light_pink', 'name': '浅粉', 'color': '#FCE4EC'},
    {'id': 'light_green', 'name': '浅绿', 'color': '#E8F5E9'},
    {'id': 'lavender', 'name': '薰衣草', 'color': '#F3E5F5'},
    {'id': 'peach', 'name': '桃色', 'color': '#FFE0B2'},
]

# 默认边框配置
DEFAULT_BORDER_CONFIG = {
    'shape': 'rectangle',
    'width': 30,  # 宽度30
    'radius': 0,
    'color': '#BBDEFB',  # 浅蓝色
    'line_style': 'solid',
    'pattern': 'grid',  # 网格图案
    'pattern_color': '#FFFFFF',
    'pattern_size': 10,
}

# 画布默认配置
DEFAULT_CANVAS_WIDTH = 800
DEFAULT_CANVAS_HEIGHT = 800
DEFAULT_BACKGROUND_COLOR = '#FFFFFF'

# 颜色配置 - 现代深色主题 (高对比度)
COLORS = {
    'primary': '#0A84FF',
    'secondary': '#98989D',
    'success': '#30D158',
    'danger': '#FF453A',
    'warning': '#FFD60A',
    # 深色背景
    'bg': '#1E1E1E',
    'bg_secondary': '#252526',
    'bg_tertiary': '#2D2D2D',
    'border': '#3C3C3C',
    # 面板
    'panel_bg': '#252526',
    'panel_hover': '#2A2D2E',
    'panel_active': '#37373D',
    'hover': '#37373D',
    'active': '#404040',
    # 文字 - 提高对比度
    'text_primary': '#E8E8E8',
    'text_secondary': '#A0A0A0',
    'text_tertiary': '#808080',
    'text_bright': '#FFFFFF',
    # 分隔和边框
    'separator': '#404040',
    'input_bg': '#3C3C3C',
    'input_border': '#4C4C4C',
    # 强调色
    'accent': '#0A84FF',
    'accent_light': '#0A84FF20',
    'accent_hover': '#409CFF',
    'selected_bg': '#0A84FF',
    'selected_text': '#FFFFFF',
    # 按钮
    'btn_primary': '#0A84FF',
    'btn_secondary': '#404040',
    'btn_danger': '#FF453A',
}

# 马卡龙色系（低饱和度，清新柔和）
MACARON_COLORS = [
    '#FFB7B2', # 柔粉
    '#FFDAC1', # 杏色
    '#E2F0CB', # 嫩绿
    '#B5EAD7', # 薄荷
    '#C7CEEA', # 淡紫
    '#F8BBD0', # 浅玫瑰
    '#E1BEE7', # 浅紫罗兰
    '#D1C4E9', # 浅靛蓝
    '#C5CAE9', # 浅蓝灰
    '#BBDEFB', # 浅蓝
    '#B3E5FC', # 浅天蓝
    '#B2EBF2', # 浅青
    '#B2DFDB', # 浅蓝绿
    '#C8E6C9', # 浅绿
    '#DCEDC8', # 浅黄绿
    '#F0F4C3', # 浅柠檬
    '#FFF9C4', # 浅黄
    '#FFECB3', # 浅琥珀
]

# 多巴胺色系（高饱和度，明亮鲜艳）
DOPAMINE_COLORS = [
    '#FF2D55', # 亮粉
    '#FF3B30', # 亮红
    '#FF9500', # 亮橙
    '#FFCC00', # 亮黄
    '#34C759', # 亮绿
    '#5AC8FA', # 亮青
    '#007AFF', # 亮蓝
    '#5856D6', # 亮靛
    '#AF52DE', # 亮紫
    '#FF6EC7', # 霓虹粉
    '#FFD60A', # 柠檬黄
    '#30D158', # 鲜绿
    '#66D4CF', # 蒂芙尼蓝
    '#BF5AF2', # 鲜紫
    '#AC8E68', # 金色
]

# 快速颜色选择列表
QUICK_COLORS = [
    '#000000', # 黑
    '#FFFFFF', # 白
    *MACARON_COLORS
]

# 随机字体列表 (跨平台常用 + 中文)
RANDOM_FONTS = [
    # macOS / iOS
    "PingFang SC", "Heiti SC", "Songti SC", "Kaiti SC", "Apple LiGothic",
    # Windows / Office
    "Microsoft YaHei", "SimHei", "SimSun", "KaiTi", "FangSong",
    # English / Universal
    "Arial", "Helvetica", "Georgia", "Times New Roman", "Courier New", 
    "Verdana", "Trebuchet MS", "Impact", "Comic Sans MS", "Chalkboard SE"
]
