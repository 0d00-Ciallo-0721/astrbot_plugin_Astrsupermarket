# feifeisupermarket/achievements.py

"""
成就系统定义模块

定义了所有成就的ID、名称、描述、奖励和解锁条件。
- 'unlock_condition' 是一个lambda函数，将在主逻辑中被调用，接收所需的数据字典作为参数，返回布尔值。
"""

ACHIEVEMENTS = {
    # 签到与成长类
    'signin_1': {
        'name': "初来乍到",
        'description': "完成首次签到。",
        'reward_points': 10,
        'reward_title': "",
        'unlock_condition': lambda u_data, **kwargs: u_data.get("total_days", 0) >= 1
    },
    'signin_2': {
        'name': "坚持不懈",
        'description': "连续签到7天。",
        'reward_points': 50,
        'reward_title': "毅力",
        'unlock_condition': lambda u_data, **kwargs: u_data.get("streak_days", 0) >= 7
    },
    'signin_3': {
        'name': "风雨无阻",
        'description': "连续签到30天。",
        'reward_points': 200,
        'reward_title': "签到大师",
        'unlock_condition': lambda u_data, **kwargs: u_data.get("streak_days", 0) >= 30
    },
    'signin_4': {
        'name': "后悔药",
        'description': "首次使用补签功能。",
        'reward_points': 5,
        'reward_title': "",
        # [已修复] 由特定事件触发，通用检查时应为False
        'unlock_condition': lambda **kwargs: False
    },

    # 财富与经济类
    'wealth_1': {
        'name': "第一桶金",
        'description': "拥有的Astr币首次超过1000。",
        'reward_points': 50,
        'reward_title': "小有资产",
        'unlock_condition': lambda u_data, **kwargs: u_data.get("points", 0) >= 1000
    },
    'wealth_2': {
        'name': "万元户",
        'description': "拥有的Astr币首次超过10000。",
        'reward_points': 200,
        'reward_title': "富豪",
        'unlock_condition': lambda u_data, **kwargs: u_data.get("points", 0) >= 10000
    },
     'wealth_3': {
        'name': "一夜赤贫",
        'description': "因操作导致Astr币归零。",
        'reward_points': 10, # 安慰奖
        'reward_title': "破产",
        'unlock_condition': lambda u_data, **kwargs: u_data.get("points", 0) <= 0
    },

    # 商城与奴役类
    'market_1': {
        'name': "初次收购",
        'description': "首次成功购买一位群友。",
        'reward_points': 20,
        'reward_title': "奴隶主",
        'unlock_condition': lambda m_data, **kwargs: len(m_data.get("owned_members", [])) >= 1
    },
    'market_2': {
        'name': "自由的代价",
        'description': "首次使用赎身功能。",
        'reward_points': 10,
        'reward_title': "自由人",
        # [已修复] 补充了缺失的键，并修正了逻辑
        'unlock_condition': lambda **kwargs: False
    },
    'market_3': {
        'name': "无情资本家",
        'description': "通过打工累计为自己赚取超过5000Astr币。",
        'reward_points': 100,
        'reward_title': "资本家",
        'unlock_condition': lambda m_data, **kwargs: m_data.get("total_work_revenue", 0.0) >= 5000
    },
    'market_4': {
        'name': "黑心老板",
        'description': "名下的奴隶打工失败次数累计超过10次。",
        'reward_points': 30,
        'reward_title': "黑心老板",
        'unlock_condition': lambda m_data, **kwargs: m_data.get("total_work_failures", 0) >= 10
    },

    # 抽奖与运气类
    'luck_1': {
        'name': "幸运星",
        'description': "首次抽中6星奖励。",
        'reward_points': 30,
        'reward_title': "幸运星",
        'unlock_condition': lambda u_data, **kwargs: u_data.get("high_tier_wins", 0) >= 1
    },
    'luck_2': {
        'name': "天选之人",
        'description': "抽中隐藏大奖。",
        'reward_points': 111,
        'reward_title': "天选之人",
        # [已修复] 由特定事件触发，通用检查时应为False
        'unlock_condition': lambda **kwargs: False
    },
    'luck_3': {
        'name': "非酋在世",
        'description': "连续5次抽中1星奖励。",
        'reward_points': 50, # 精神损失费
        'reward_title': "非洲酋长",
        'unlock_condition': lambda u_data, **kwargs: u_data.get("consecutive_1star", 0) >= 5
    },

    # 趣味与彩蛋类
    'fun_2': {
        'name': "自娱自乐",
        'description': "尝试购买自己。",
        'reward_points': 1,
        'reward_title': "",
        # [已修复] 由特定事件触发，通用检查时应为False
        'unlock_condition': lambda **kwargs: False
    },
    'work_1': {
        'name': "赌神",
        'description': "在“偷窃苏特尔的宝库”中成功，这需要神一般的运气。",
        'reward_points': 88,
        'reward_title': "赌神",
        # [已修复] 由特定事件触发，通用检查时应为False
        'unlock_condition': lambda **kwargs: False
    },
    "generous": {
        "name": "乐善好施",
        "description": "累计赠送Astr币达到500。",
        "reward_points": 20,
        "reward_title": "好人", # 为"乐善好施"也加上称号，增加趣味性
        'unlock_condition': lambda u_data, **kwargs: u_data.get("total_gifted", 0) >= 500
    },
    "big_donor": {
        "name": "慷慨大方",
        "description": "累计赠送Astr币达到1000。",
        "reward_points": 100,
        "reward_title": "慈善家",
        'unlock_condition': lambda u_data, **kwargs: u_data.get("total_gifted", 0) >= 10000
    },
    "big_gift": {
        "name": "一掷千金",
        "description": "单次赠送Astr币达到100。",
        "reward_points": 30,
        "reward_title": "", # 单次行为通常不设永久称号，但可以按需添加
        'unlock_condition': lambda **kwargs: False # 这是一个事件驱动成就，通用检查时应为False
    },
    "gift_master": {
        "name": "送礼达人",
        "description": "累计赠送次数达到50次。",
        "reward_points": 50,
        "reward_title": "慷慨使者",
        'unlock_condition': lambda u_data, **kwargs: u_data.get("gift_count", 0) >= 50
    },
    "daily_giver": {
        "name": "日行一善",
        "description": "连续7天每天都赠送Astr币。",
        "reward_points": 77,
        "reward_title": "善心使者",
        'unlock_condition': lambda u_data, **kwargs: u_data.get("consecutive_gift_days", 0) >= 7
    },
    'adventure_beginner': {
        'name': "初次冒险",
        'description': "完成第一次大冒险。",
        'reward_points': 20,
        'reward_title': "冒险新手",
        'unlock_condition': lambda u_data, **kwargs: u_data.get("adventure_count", 0) >= 1
    },
    'adventure_master': {
        'name': "勇往直前",
        'description': "累计进行100次冒险判定。",
        'reward_points': 100,
        'reward_title': "资深冒险家",
        'unlock_condition': lambda u_data, **kwargs: u_data.get("adventure_count", 0) >= 100
    },
    'adventure_king': {
        'name': "冒险王",
        'description': "赢得了创世神的认可。",
        'reward_points': 200,
        'reward_title': "冒险王",
        'unlock_condition': lambda **kwargs: False  # 事件触发时手动解锁
    },
    'social_date_beginner': {
        'name': "约会新手",
        'description': "完成首次约会。",
        'reward_points': 30,
        'reward_title': "约会达人",
        'unlock_condition': lambda u_data, **kwargs: False  # 由事件直接触发，不通过通用检查
    },
    'social_master': {
        'name': "社交达人",
        'description': "与5名不同用户的好感度在50以上。",
        'reward_points': 50,
        'reward_title': "魅力四射",
        'unlock_condition': lambda u_data, **kwargs: False  # 需要查询社交数据，不通过通用检查
    },
    'social_patron': {
        'name': "金主爸爸",
        'description': "首次建立包养关系。",
        'reward_points': 100,
        'reward_title': "金主",
        'unlock_condition': lambda u_data, **kwargs: False  # 由事件直接触发，不通过通用检查
    }
}