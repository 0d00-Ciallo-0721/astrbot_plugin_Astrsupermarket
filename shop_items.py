SHOP_DATA = {
    "道具": {
        "便当": { 
            "name": "便当", 
            "price": 30, 
            "description": "使用后，你的下一次打工必定成功（特定高风险工作除外）。",
            "effect_buff": "work_guarantee_success",
            "category": "道具"
        },
        "守护符": { 
            "name": "守护符", 
            "price": 10, 
            "description": "使用后，下一次打工即使失败也不会扣除Astr币。",
            "effect_buff": "work_no_penalty",
            "category": "道具"
        },
        "能量饮料": {
            "name": "能量饮料", 
            "price": 30,
            "description": "使用后，下一次打工成功时，获得的Astr币奖励随机提升1%-50%。",
            "effect_buff": "work_reward_boost",
            "category": "道具"
        },
        "幸运药水": {
            "name": "幸运药水", 
            "price": 15,
            "description": "使用后，你的下一次抽奖必定为3星或以上的结果。",
            "effect_buff": "lottery_min_3star",
            "category": "道具"
        },
        "幸运四叶草": {
            "name": "幸运四叶草", 
            "price": 15,
            "description": "使用后，下一次抽奖获得的Astr币奖励翻倍。",
            "effect_buff": "lottery_double_reward",
            "category": "道具"
        },
        "择优券": {
            "name": "择优券", 
            "price": 30,
            "description": "使用后，下一次抽奖将进行两次并取最高星级奖励。",
            "effect_buff": "lottery_best_of_two",
            "category": "道具"
        },
        "探险家护符": {
            "name": "探险家护符",
            "price": 25,
            "description": "使用后，下一次冒险若遭遇“危机与挑战”事件，将免受其负面影响。",
            "effect_buff": "adventure_negate_crisis",
            "category": "道具"
        },
        "奇遇信标": {
            "name": "奇遇信标",
            "price": 35,
            "description": "使用后，下一次冒险有更高概率遭遇“稀世奇遇”事件。",
            "effect_buff": "adventure_rare_boost",
            "category": "道具"
        }
    },
    "食物": {
        "小饼干": {
            "name": "Astr的小饼干", 
            "price": 10, 
            "description": "食用后，恢复20点体力。",
            "category": "食物"
        },
        "章鱼烧": {
            "name": "章鱼烧", 
            "price": 15, 
            "description": "食用后，恢复30点体力。",
            "category": "食物"
        },
        "肉包": {
            "name": "肉包", 
            "price": 20, 
            "description": "食用后，恢复40点体力。",
            "category": "食物"
        },
        "布丁": {
            "name": "布丁", 
            "price": 80, 
            "description": "食用后，恢复100点体力。",
            "category": "食物"
        },
        "KFC": {
            "name": "KFC", 
            "price": 50, 
            "description": "食用后，恢复100点体力。",
            "category": "食物"
        },
        "拼好饭": {
            "name": "拼好饭", 
            "price": 15, 
            "description": "食用后，体力在1到60之间随机恢复。",
            "category": "食物"
        },
        "华莱士": {
            "name": "华莱士三汉堡", 
            "price": 12, 
            "description": "食用后，体力清空或者恢复至50。",
            "category": "食物"
        },
        "方便面": {
            "name": "方便面", 
            "price": 5, 
            "description": "食用后，体力在1-20之间随机恢复。",
            "category": "食物"
        }
    },
    "礼物": {
        "花": {
            "name": "花", 
            "price": 10, 
            "description": "赠送后，目标好感度+1。", 
            "effect": {"favorability_gain": 1},
            "category": "礼物"
        },
        "棒棒糖": {
            "name": "棒棒糖", 
            "price": 20, 
            "description": "赠送后，目标好感度+2。", 
            "effect": {"favorability_gain": 2},
            "category": "礼物"
        },
        "奶茶": {
            "name": "奶茶", 
            "price": 30, 
            "description": "赠送后，目标好感度+3。", 
            "effect": {"favorability_gain": 3},
            "category": "礼物"
        },
        "巧克力": {
            "name": "巧克力", 
            "price": 100, 
            "description": "赠送后，目标好感度+10。", 
            "effect": {"favorability_gain": 10},
            "category": "礼物"
        },
        "V我50": {
            "name": "V我50", 
            "price": 50, 
            "description": "赠送后，目标好感度+5。", 
            "effect": {"favorability_gain": 5},
            "category": "礼物"
        },
        "卡天亚戒指": {
            "name": "卡天亚戒指", 
            "price": 1000, 
            "description": "好感度满时，可缔结恋人关系。", 
            "effect": {"relation_type": "lover"},
            "category": "礼物"
        },
        "一壶烈酒": {
            "name": "一壶烈酒", 
            "price": 1000, 
            "description": "好感度满时，可缔结兄弟关系。", 
            "effect": {"relation_type": "brother"},
            "category": "礼物"
        },
        "黑金卡": {
            "name": "黑金卡", 
            "price": 1000, 
            "description": "好感度满时，可缔结包养关系。", 
            "effect": {"relation_type": "sugar_daddy"},
            "category": "礼物"
        }
    }
}
