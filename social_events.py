# feifeisupermarket/social_events.py

"""
AstrAstr超级市场 - 社会生活系统
约会事件配置文件
"""

DATE_EVENTS = [
    {
        "id": "movie",
        "name": "电影院约会",
        "description": "你们在电影院看了一场感人的电影，相视一笑。",
        "favorability_change": (3, 5)  # 双方好感度增加范围
    },
    {
        "id": "rain",
        "name": "被雨淋湿",
        "description": "约会途中突然下雨，两人被淋湿，气氛有些尴尬。",
        "favorability_change": (-2, 0)  # 可能减少好感度
    },
    {
        "id": "park",
        "name": "公园散步",
        "description": "你们在公园喂了一下午的鸽子，度过了平静而温馨的一天。",
        "favorability_change": (1, 2)
    },
    {
        "id": "restaurant",
        "name": "共进晚餐",
        "description": "你们在一家浪漫的餐厅共进晚餐，氛围很好。",
        "favorability_change": (2, 4)
    },
    {
        "id": "karaoke",
        "name": "KTV欢唱",
        "description": "在KTV唱歌时，你们默契地合唱了一首歌，引来大家的掌声。",
        "favorability_change": (1, 3)
    },
    {
        "id": "library",
        "name": "图书馆学习",
        "description": "你们在图书馆一起学习，彼此都很专注，偶尔交流学习心得。",
        "favorability_change": (1, 3)
    },
    {
        "id": "arcade",
        "name": "游戏厅",
        "description": "在游戏厅里，你们玩了各种游戏，互相配合取得了高分。",
        "favorability_change": (2, 4)
    },
    {
        "id": "cafe",
        "name": "咖啡馆",
        "description": "在咖啡馆里，你们聊了很多共同的兴趣爱好，发现彼此很合拍。",
        "favorability_change": (2, 5)
    },
    {
        "id": "shopping",
        "name": "逛街购物",
        "description": "一起逛街购物时，你们互相给对方挑选了礼物，但忘了谁付钱了...",
        "favorability_change": (0, 3)
    },
    {
        "id": "picnic",
        "name": "野餐",
        "description": "你们在郊外野餐，享受着美食和美丽的风景，度过了愉快的时光。",
        "favorability_change": (3, 5)
    },
    {
        "id": "zoo",
        "name": "动物园约会",
        "description": "在动物园里，你们一起观赏了各种可爱的动物，拍了很多照片。",
        "favorability_change": (2, 4)
    },
    {
        "id": "concert",
        "name": "音乐会",
        "description": "你们一起参加了一场音乐会，沉浸在美妙的音乐中。",
        "favorability_change": (2, 4)
    },
    {
        "id": "ice_cream",
        "name": "冰淇淋店",
        "description": "在冰淇淋店里，你们分享了各自的冰淇淋，甜蜜又开心。",
        "favorability_change": (1, 3)
    },
    {
        "id": "beach",
        "name": "海滩漫步",
        "description": "在海滩上散步，你们一起看着美丽的日落，心情愉悦。",
        "favorability_change": (3, 5)
    },
    {
        "id": "amusement_park",
        "name": "游乐园",
        "description": "在游乐园里，你们勇敢地尝试了各种刺激的项目，留下了美好的回忆。",
        "favorability_change": (2, 5)
    },
    {
        "id": "hiking",
        "name": "爬山",
        "description": "一起爬山时，你们互相鼓励，成功登顶并欣赏了壮丽的风景。",
        "favorability_change": (3, 4)
    },
    {
        "id": "cooking",
        "name": "一起做饭",
        "description": "你们一起在家做饭，虽然过程有些混乱，但最终做出了美味的菜肴。",
        "favorability_change": (2, 5)
    },
    {
        "id": "garden",
        "name": "植物园",
        "description": "在植物园里，你们欣赏了各种美丽的花草，感受大自然的魅力。",
        "favorability_change": (1, 3)
    },
    {
        "id": "dance",
        "name": "跳舞",
        "description": "在舞会上，你们一起跳舞，虽然有些笨拙，但很享受这个过程。",
        "favorability_change": (1, 4)
    },
    {
        "id": "star_gazing",
        "name": "观星",
        "description": "在郊外的草地上，你们一起观星，聊着各自的梦想和未来。",
        "favorability_change": (3, 5)
    },
    # 负面事件
    {
        "id": "argument",
        "name": "争吵",
        "description": "约会过程中，因为一些小事，你们发生了争执，气氛有些紧张。",
        "favorability_change": (-3, -1)
    },
    {
        "id": "late",
        "name": "迟到",
        "description": "其中一方迟到了很久，让对方等待了很长时间，心情有些不好。",
        "favorability_change": (-2, 0)
    },
    {
        "id": "phone",
        "name": "玩手机",
        "description": "约会中，一方总是看手机，让对方感到被忽视。",
        "favorability_change": (-3, -1)
    },
    {
        "id": "ex",
        "name": "前任话题",
        "description": "谈话中不小心提到了前任，气氛瞬间变得尴尬。",
        "favorability_change": (-4, -2)
    },
    {
        "id": "lost",
        "name": "迷路",
        "description": "你们在去约会地点的路上迷路了，花了很长时间才找到目的地。",
        "favorability_change": (-2, 0)
    },
    {
        "id": "bad_weather",
        "name": "天气糟糕",
        "description": "突如其来的大雨打乱了原本的计划，整个约会变得狼狈又混乱。",
        "favorability_change": (-3, -1)
    },
    {
        "id": "awkward_silence",
        "name": "冷场",
        "description": "你们有好几次陷入了尴尬的沉默，气氛一度变得很不自然。",
        "favorability_change": (-2, 0)
    },
    {
        "id": "wrong_place",
        "name": "选错地点",
        "description": "约会地点选得不合时宜，让人觉得无趣甚至有点失望。",
        "favorability_change": (-3, -1)
    },
    {
        "id": "spill_drink",
        "name": "打翻饮料",
        "description": "一方不小心把饮料洒到了对方身上，虽然是意外，但气氛有点尴尬。",
        "favorability_change": (-2, -1)
    },
    {
        "id": "forget_name",
        "name": "叫错名字",
        "description": "一方不小心叫错了对方的名字，瞬间空气都凝固了。",
        "favorability_change": (-4, -2)
    }    
]

# 关系等级对应表
RELATION_LEVELS = {
    "0-19": "陌生人",
    "20-49": "熟人",
    "50-89": "朋友",
    "90-99": "挚友", 
    "100": "唯一的你",
    "101+": "灵魂伴侣"
}

# 特殊关系对应的所需物品
SPECIAL_RELATION_ITEMS = {
    "恋人": "卡天亚戒指",
    "兄弟": "一壶烈酒",
    "包养": "黑金卡"
}

# 特殊关系对应的内部标识
SPECIAL_RELATION_TYPES = {
    "恋人": "lover",
    "兄弟": "brother",
    "包养": "patron"
}

# 内部标识对应的中文名称(反向映射)
RELATION_TYPE_NAMES = {
    "lover": "恋人",
    "brother": "兄弟", 
    "patron": "包养关系"
}
