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
    # 精选靓丽表情 - 最常用 (12个)
    {'id': 'heart', 'emoji': '❤️', 'name': '爱心', 'file': 'heart.png'},
    {'id': 'star', 'emoji': '⭐', 'name': '星星', 'file': 'star.png'},
    {'id': 'sparkles', 'emoji': '✨', 'name': '闪光', 'file': 'sparkles.png'},
    {'id': 'fire', 'emoji': '🔥', 'name': '火焰', 'file': 'fire.png'},
    {'id': 'smile', 'emoji': '😊', 'name': '笑脸', 'file': 'smile.png'},
    {'id': 'flower', 'emoji': '🌸', 'name': '花朵', 'file': 'flower.png'},
    {'id': 'crown', 'emoji': '👑', 'name': '皇冠', 'file': 'crown.png'},
    {'id': 'ribbon', 'emoji': '🎀', 'name': '蝴蝶结', 'file': 'ribbon.png'},
    {'id': 'cake', 'emoji': '🎂', 'name': '蛋糕', 'file': 'cake.png'},
    {'id': 'gift', 'emoji': '🎁', 'name': '礼物', 'file': 'gift.png'},
    {'id': 'balloon', 'emoji': '🎈', 'name': '气球', 'file': 'balloon.png'},
    {'id': 'music', 'emoji': '🎵', 'name': '音符', 'file': 'music.png'},
    # 表情符号 (20个)
    {'id': 'laughing', 'emoji': '😂', 'name': '大笑', 'file': 'laughing.png'},
    {'id': 'love_eyes', 'emoji': '😍', 'name': '花痴', 'file': 'love_eyes.png'},
    {'id': 'wink', 'emoji': '😉', 'name': '眨眼', 'file': 'wink.png'},
    {'id': 'kiss', 'emoji': '😘', 'name': '飞吻', 'file': 'kiss.png'},
    {'id': 'party', 'emoji': '🥳', 'name': '派对', 'file': 'party.png'},
    {'id': 'cool', 'emoji': '😎', 'name': '墨镜', 'file': 'cool.png'},
    {'id': 'clap', 'emoji': '👏', 'name': '鼓掌', 'file': 'clap.png'},
    {'id': 'thumbsup', 'emoji': '👍', 'name': '点赞', 'file': 'thumbsup.png'},
    {'id': 'grinning', 'emoji': '😀', 'name': '大笑脸', 'file': 'grinning.png'},
    {'id': 'star_struck', 'emoji': '🤩', 'name': '星星眼', 'file': 'star_struck.png'},
    {'id': 'hugging', 'emoji': '🤗', 'name': '拥抱', 'file': 'hugging.png'},
    {'id': 'smiling_eyes', 'emoji': '😄', 'name': '大笑', 'file': 'smiling_eyes.png'},
    {'id': 'grin', 'emoji': '😁', 'name': '咧嘴笑', 'file': 'grin.png'},
    {'id': 'sweat_smile', 'emoji': '😅', 'name': '流汗笑', 'file': 'sweat_smile.png'},
    {'id': 'rofl', 'emoji': '🤣', 'name': '打滚笑', 'file': 'rofl.png'},
    {'id': 'smiling_face_hearts', 'emoji': '🥰', 'name': '爱心脸', 'file': 'smiling_face_hearts.png'},
    {'id': 'kissing_closed_eyes', 'emoji': '😚', 'name': '闭眼吻', 'file': 'kissing_closed_eyes.png'},
    {'id': 'stuck_out_tongue', 'emoji': '😛', 'name': '吐舌', 'file': 'stuck_out_tongue.png'},
    {'id': 'stuck_out_tongue_wink', 'emoji': '😜', 'name': '眨眼吐舌', 'file': 'stuck_out_tongue_wink.png'},
    {'id': 'zany', 'emoji': '🤪', 'name': '疯狂', 'file': 'zany.png'},
    {'id': 'thinking', 'emoji': '🤔', 'name': '思考', 'file': 'thinking.png'},
    # 动物 (20个)
    {'id': 'panda', 'emoji': '🐼', 'name': '熊猫', 'file': 'panda.png'},
    {'id': 'unicorn', 'emoji': '🦄', 'name': '独角兽', 'file': 'unicorn.png'},
    {'id': 'butterfly', 'emoji': '🦋', 'name': '蝴蝶', 'file': 'butterfly.png'},
    {'id': 'dog', 'emoji': '🐶', 'name': '狗狗', 'file': 'dog.png'},
    {'id': 'cat', 'emoji': '🐱', 'name': '猫咪', 'file': 'cat.png'},
    {'id': 'bunny', 'emoji': '🐰', 'name': '兔子', 'file': 'bunny.png'},
    {'id': 'bear', 'emoji': '🐻', 'name': '小熊', 'file': 'bear.png'},
    {'id': 'tiger', 'emoji': '🐯', 'name': '老虎', 'file': 'tiger.png'},
    {'id': 'lion', 'emoji': '🦁', 'name': '狮子', 'file': 'lion.png'},
    {'id': 'fox', 'emoji': '🦊', 'name': '狐狸', 'file': 'fox.png'},
    {'id': 'koala', 'emoji': '🐨', 'name': '考拉', 'file': 'koala.png'},
    {'id': 'pig', 'emoji': '🐷', 'name': '小猪', 'file': 'pig.png'},
    {'id': 'frog', 'emoji': '🐸', 'name': '青蛙', 'file': 'frog.png'},
    {'id': 'chicken', 'emoji': '🐔', 'name': '小鸡', 'file': 'chicken.png'},
    {'id': 'penguin', 'emoji': '🐧', 'name': '企鹅', 'file': 'penguin.png'},
    {'id': 'owl', 'emoji': '🦉', 'name': '猫头鹰', 'file': 'owl.png'},
    {'id': 'bee', 'emoji': '🐝', 'name': '蜜蜂', 'file': 'bee.png'},
    {'id': 'dolphin', 'emoji': '🐬', 'name': '海豚', 'file': 'dolphin.png'},
    {'id': 'whale', 'emoji': '🐳', 'name': '鲸鱼', 'file': 'whale.png'},
    {'id': 'fish', 'emoji': '🐟', 'name': '鱼', 'file': 'fish.png'},
    {'id': 'turtle', 'emoji': '🐢', 'name': '乌龟', 'file': 'turtle.png'},
    # 美食 (20个)
    {'id': 'icecream', 'emoji': '🍦', 'name': '冰淇淋', 'file': 'icecream.png'},
    {'id': 'donut', 'emoji': '🍩', 'name': '甜甜圈', 'file': 'donut.png'},
    {'id': 'pizza', 'emoji': '🍕', 'name': '披萨', 'file': 'pizza.png'},
    {'id': 'strawberry', 'emoji': '🍓', 'name': '草莓', 'file': 'strawberry.png'},
    {'id': 'watermelon', 'emoji': '🍉', 'name': '西瓜', 'file': 'watermelon.png'},
    {'id': 'cherry', 'emoji': '🍒', 'name': '樱桃', 'file': 'cherry.png'},
    {'id': 'lollipop', 'emoji': '🍭', 'name': '棒棒糖', 'file': 'lollipop.png'},
    {'id': 'coffee', 'emoji': '☕', 'name': '咖啡', 'file': 'coffee.png'},
    {'id': 'apple', 'emoji': '🍎', 'name': '苹果', 'file': 'apple.png'},
    {'id': 'orange', 'emoji': '🍊', 'name': '橙子', 'file': 'orange.png'},
    {'id': 'banana', 'emoji': '🍌', 'name': '香蕉', 'file': 'banana.png'},
    {'id': 'grapes', 'emoji': '🍇', 'name': '葡萄', 'file': 'grapes.png'},
    {'id': 'peach', 'emoji': '🍑', 'name': '桃子', 'file': 'peach.png'},
    {'id': 'pineapple', 'emoji': '🍍', 'name': '菠萝', 'file': 'pineapple.png'},
    {'id': 'mango', 'emoji': '🥭', 'name': '芒果', 'file': 'mango.png'},
    {'id': 'cookie', 'emoji': '🍪', 'name': '饼干', 'file': 'cookie.png'},
    {'id': 'cupcake', 'emoji': '🧁', 'name': '纸杯蛋糕', 'file': 'cupcake.png'},
    {'id': 'hamburger', 'emoji': '🍔', 'name': '汉堡', 'file': 'hamburger.png'},
    {'id': 'fries', 'emoji': '🍟', 'name': '薯条', 'file': 'fries.png'},
    {'id': 'taco', 'emoji': '🌮', 'name': '塔可', 'file': 'taco.png'},
    {'id': 'sushi', 'emoji': '🍣', 'name': '寿司', 'file': 'sushi.png'},
    # 自然/天气 (15个)
    {'id': 'rainbow', 'emoji': '🌈', 'name': '彩虹', 'file': 'rainbow.png'},
    {'id': 'sun', 'emoji': '☀️', 'name': '太阳', 'file': 'sun.png'},
    {'id': 'moon', 'emoji': '🌙', 'name': '月亮', 'file': 'moon.png'},
    {'id': 'snowflake', 'emoji': '❄️', 'name': '雪花', 'file': 'snowflake.png'},
    {'id': 'lightning', 'emoji': '⚡', 'name': '闪电', 'file': 'lightning.png'},
    {'id': 'droplet', 'emoji': '💧', 'name': '水滴', 'file': 'droplet.png'},
    {'id': 'sun_with_face', 'emoji': '🌞', 'name': '太阳脸', 'file': 'sun_with_face.png'},
    {'id': 'full_moon', 'emoji': '🌕', 'name': '满月', 'file': 'full_moon.png'},
    {'id': 'star2', 'emoji': '🌟', 'name': '闪亮星', 'file': 'star2.png'},
    {'id': 'cloud', 'emoji': '☁️', 'name': '云朵', 'file': 'cloud.png'},
    {'id': 'tulip', 'emoji': '🌷', 'name': '郁金香', 'file': 'tulip.png'},
    {'id': 'rose', 'emoji': '🌹', 'name': '玫瑰', 'file': 'rose.png'},
    {'id': 'hibiscus', 'emoji': '🌺', 'name': '芙蓉', 'file': 'hibiscus.png'},
    {'id': 'sunflower', 'emoji': '🌻', 'name': '向日葵', 'file': 'sunflower.png'},
    {'id': 'four_leaf_clover', 'emoji': '🍀', 'name': '四叶草', 'file': 'four_leaf_clover.png'},
    # 手势/符号 (15个)
    {'id': 'check', 'emoji': '✅', 'name': '完成', 'file': 'check.png'},
    {'id': 'hundred', 'emoji': '💯', 'name': '满分', 'file': 'hundred.png'},
    {'id': 'ok', 'emoji': '👌', 'name': 'OK', 'file': 'ok.png'},
    {'id': 'victory', 'emoji': '✌️', 'name': '胜利', 'file': 'victory.png'},
    {'id': 'rock', 'emoji': '🤘', 'name': '摇滚', 'file': 'rock.png'},
    {'id': 'love_you', 'emoji': '🤟', 'name': '我爱你', 'file': 'love_you.png'},
    {'id': 'fingers_crossed', 'emoji': '🤞', 'name': '交叉手指', 'file': 'fingers_crossed.png'},
    {'id': 'call_me', 'emoji': '🤙', 'name': '打电话', 'file': 'call_me.png'},
    {'id': 'muscle', 'emoji': '💪', 'name': '肌肉', 'file': 'muscle.png'},
    {'id': 'point_right', 'emoji': '👉', 'name': '指向右', 'file': 'point_right.png'},
    {'id': 'point_left', 'emoji': '👈', 'name': '指向左', 'file': 'point_left.png'},
    {'id': 'point_up', 'emoji': '👆', 'name': '指向上', 'file': 'point_up.png'},
    {'id': 'point_down', 'emoji': '👇', 'name': '指向下', 'file': 'point_down.png'},
    {'id': 'pray', 'emoji': '🙏', 'name': '祈祷', 'file': 'pray.png'},
    {'id': 'wave', 'emoji': '👋', 'name': '挥手', 'file': 'wave.png'},
    # 物品/符号 (18个)
    {'id': 'diamond', 'emoji': '💎', 'name': '钻石', 'file': 'diamond.png'},
    {'id': 'rocket', 'emoji': '🚀', 'name': '火箭', 'file': 'rocket.png'},
    {'id': 'trophy', 'emoji': '🏆', 'name': '奖杯', 'file': 'trophy.png'},
    {'id': 'medal', 'emoji': '🏅', 'name': '奖牌', 'file': 'medal.png'},
    {'id': 'camera', 'emoji': '📷', 'name': '相机', 'file': 'camera.png'},
    {'id': 'confetti', 'emoji': '🎊', 'name': '彩带', 'file': 'confetti.png'},
    {'id': 'party_popper', 'emoji': '🎉', 'name': '派对', 'file': 'party_popper.png'},
    {'id': 'sparkler', 'emoji': '🎆', 'name': '烟花', 'file': 'sparkler.png'},
    {'id': 'fireworks', 'emoji': '🎇', 'name': '焰火', 'file': 'fireworks.png'},
    {'id': 'purple_heart', 'emoji': '💜', 'name': '紫心', 'file': 'purple_heart.png'},
    {'id': 'green_heart', 'emoji': '💚', 'name': '绿心', 'file': 'green_heart.png'},
    {'id': 'blue_heart', 'emoji': '💙', 'name': '蓝心', 'file': 'blue_heart.png'},
    {'id': 'yellow_heart', 'emoji': '💛', 'name': '黄心', 'file': 'yellow_heart.png'},
    {'id': 'orange_heart', 'emoji': '🧡', 'name': '橙心', 'file': 'orange_heart.png'},
    {'id': 'sparkling_heart', 'emoji': '💖', 'name': '闪亮心', 'file': 'sparkling_heart.png'},
    {'id': 'two_hearts', 'emoji': '💕', 'name': '双心', 'file': 'two_hearts.png'},
    {'id': 'cupid', 'emoji': '💘', 'name': '丘比特', 'file': 'cupid.png'},
    {'id': 'gift_heart', 'emoji': '💝', 'name': '礼物心', 'file': 'gift_heart.png'},
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

# 高亮专用色系 (剔除深色/冷色，只保留高亮荧光感颜色)
BRIGHT_HIGHLIGHT_COLORS = [
    '#FF2D55', # 亮粉
    '#FF3B30', # 亮红
    '#FF9500', # 亮橙
    '#FFCC00', # 亮黄
    '#34C759', # 亮绿 (Lime Green)
    '#5AC8FA', # 亮青 (Cyan)
    '#FF6EC7', # 霓虹粉
    '#FFD60A', # 柠檬黄
    '#30D158', # 鲜绿
    '#66D4CF', # 蒂芙尼蓝
    '#FF00FF', # 洋红
    '#00FF00', # 荧光绿
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
