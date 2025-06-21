ADVENTURE_EVENTS = {
    "机缘与抉择": {
        "probability": 25,
        "events": [
            {
                "id": "ancient_coins",
                "name": "哨塔金币",
                "description": "在废弃哨塔发现一袋Astr币。",
                "effects": {"points": (10, 20)}
            },
            {
                "id": "goblin_map",
                "name": "哥布林地图",
                "description": "你在哥布林的宝藏里发现Astr币了",
                "effects": {"points": (10, 20)}
            },
            {
                "id": "moonlight_spring",
                "name": "月光之泉",
                "description": "饮用月光泉水，恢复了体力。",
                "effects": {"stamina": (10, 20)}
            },
            {
                "id": "elf_forest",
                "name": "精灵树林",
                "description": "路过精灵树林，你恢复了精力。",
                "effects": {"stamina": (10, 20)}
            },
            {
                "id": "dwarf_blacksmith",
                "name": "矮人铁匠的谢礼",
                "description": "帮助一位矮人铁匠后，他赠予你一件礼物。",
                "effects": {
                    "random_item": [
                        {"item_id": "守护符", "probability": 40, "description": "获得【守护符】"},
                        {"item_id": "幸运药水", "probability": 40, "description": "获得【幸运药水】"},
                        {"item_id": "方便面", "probability": 20, "description": "获得【方便面】"}
                    ]
                }
            }
        ]
    },
    "危机与挑战": {
        "probability": 25,
        "events": [
            {
                "id": "scammed_alchemist",
                "name": "狡猾的炼金术士",
                "description": "被炼金术士欺骗，买到了假药水。",
                "effects": {"points": (-15, -5)}
            },
            {
                "id": "lightning_monkey",
                "name": "被抢劫",
                "description": "你的钱袋被劫匪抢走一部分。",
                "effects": {"points": (-15, -5)}
            },
            {
                "id": "miasma_swamp",
                "name": "瘴气沼泽",
                "description": "穿过瘴气沼泽，体力下降。",
                "effects": {"stamina": (-15, -5)}
            },
            {
                "id": "cave_noises",
                "name": "洞中怪声",
                "description": "被洞中怪声骚扰，睡眠不足，体力下降。",
                "effects": {"stamina": (-15, -5)}
            },
            {
                "id": "canyon_storm",
                "name": "峡谷风暴",
                "description": "在峡谷遭遇风暴，损失了Astr币和体力。",
                "effects": {"points": (-15, -5), "stamina": (-10, -5)}
            }
        ]
    },
    "抉择时刻": {
        "probability": 20,
        "narratives": [
            {
                "id": "three_gates", 
                "name": "三道光门",
                "description": "走进其中一个"
            },
            {
                "id": "three_chests", 
                "name": "三个石匣",
                "description": "打开其中一个"
            },
            {
                "id": "fate_weaver", 
                "name": "三个神秘礼盒",
                "description": "打开其中一个"
            },
            {
                "id": "three_paths", 
                "name": "三条道路",
                "description": "通过其中一个"
            }
        ],
        "outcomes": {
            "good": {
                "probability": 45, 
                "message": "命运的馈赠！你获得了奖励。",
                "effects": {
                    "random_reward": [
                        {"type": "points", "value": (10, 15)},
                        {"type": "stamina", "value": (10, 15)},
                        {"type": "item", "items": ["守护符", "幸运药水", "小饼干"]}
                    ]
                }
            },
            "bad": {
                "probability": 40, 
                "message": "你触发了陷阱！",
                "effects": {
                    "random_penalty": [
                        {"type": "points", "value": (-15, -10)},
                        {"type": "stamina", "value": (-15, -10)}
                    ]
                }
            },
            "neutral": {
                "probability": 15, 
                "message": "你的选择未产生任何影响。", 
                "effects": {}
            }
        }
    },
    "稀世奇遇": {
        "probability": 10,
        "events": [
            {
                "id": "sky_garden", 
                "name": "失落的空中花园",
                "description": "你误入了失落的空中花园，获得了丰厚奖励。",
                "effects": {
                    "random_reward": [
                        {"type": "points", "value": (10, 40)}, 
                        {"type": "stamina", "value": (10, 40)}, 
                        {"type": "item", "items": ["能量饮料", "幸运四叶草"]}
                    ]
                }
            },
            {
                "id": "unicorn_rescue", 
                "name": "独角兽的报恩",
                "description": "你救下独角兽，获得了它的报答。",
                "effects": {
                    "random_reward": [
                        {"type": "points", "value": (10, 40)}, 
                        {"type": "stamina", "value": (10, 40)}, 
                        {"type": "item", "items": ["便当", "择优券"]}
                    ]
                }
            },
            {
                "id": "dragon_dream", 
                "name": "巨龙之梦",
                "description": "你闯入巨龙的的领地，死里逃生。",
                "effects": {
                    "random_penalty": [
                        {"type": "points", "value": (-20, -10)}, 
                        {"type": "stamina", "value": (-20, -10)}
                    ]
                }
            },
            {
                "id": "swordmaster_duel", 
                "name": "魔剑士决斗",
                "description": "你与魔剑士决斗，虽胜但精疲力尽。",
                "effects": {
                    "item": "KFC", 
                    "random_penalty": [
                        {"type": "points", "value": (10, 25)}, 
                        {"type": "stamina", "value": (-20, -10)}
                    ]
                }
            }
        ]
    },
    "无事件": {
        "probability": 15,
        "events": [
            {
                "id": "two_moons", 
                "name": "双月之夜",
                "description": "你在双月之下平静地走着。",
                "effects": {}
            },
            {
                "id": "giant_mushroom", 
                "name": "巨型蘑菇",
                "description": "你在巨大的蘑菇下休息了一会儿。",
                "effects": {}
            },
            {
                "id": "magic_breeze", 
                "name": "魔法微风",
                "description": "一阵带有花香的魔法微风拂过。",
                "effects": {}
            }
        ]
    },
    "遣返事件": {
        "probability": 4,
        "events": [
            {
                "id": "goddess_call", 
                "name": "Astr的呼唤",
                "description": "Astr呼唤你，你的冒险被迫中止。",
                "effects": {"return": True}
            },
            {
                "id": "kingdom_draft", 
                "name": "王国征召",
                "description": "王国紧急征召你，冒险中止。",
                "effects": {"return": True}
            }
        ]
    },
    "天命所归": {
        "probability": 1,
        "events": [
            {
                "id": "creator_recognition",
                "name": "创世神的认可",
                "description": "创世神认可了你，授予你“冒险王”称号。",
                "effects": {"points": 200, "stamina": 100, "achievement": "冒险王", "title": "冒险王"}
            }
        ]
    }
}
