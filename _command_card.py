# 文件: feifeisupermarket/_command_card.py

import os
import math
import textwrap
from typing import Dict, Optional
from datetime import datetime
from astrbot.api import logger

# 导入您项目中的绘图工具箱
from . import drawing_utils as utils

# -------------------------------------------------------------------
# 1. 命令信息统一定义
# -------------------------------------------------------------------
# 将所有命令的用法和描述集中在此处，方便统一管理和生成卡片
# "usage" 字段用于展示如何使用该命令
COMMANDS_INFO = {
    # 基础功能
    "注意事项": {
        "usage": "空格的使用，命令后面有变量的话请使用空格键，如：一键打工（空格）<工作>（空格）@用户",
        "description": "命令后面有变量的话请使用空格键，如：一键打工（空格）<工作>（空格）@用户"
    },
    "签到": {
        "usage": "签到",
        "description": "进行每日签到，获取Astr币和奖励。"
    },
    "补签": {
        "usage": "补签",
        "description": "花费50Astr币补签昨天的记录，维持连签。"
    },
    "抽奖": {
        "usage": "抽奖",
        "description": "花费15Astr币进行一次抽奖，每日限3次。"
    },
    "排行榜": {
        "usage": "排行榜 <财富/签到/欧皇>",
        "description": "查看指定类型的排行榜。"
    },
    "我的成就": {
        "usage": "我的成就",
        "description": "查看你已解锁的全部成就。"
    },
    "我的称号": {
        "usage": "我的称号",
        "description": "列出你已获得的所有称号。"
    },
    "佩戴称号": {
        "usage": "佩戴称号 <称号名>",
        "description": "佩戴一个你已拥有的称号。"
    },
    "卸下称号": {
        "usage": "卸下称号",
        "description": "卸下当前佩戴的称号。"
    },
    # 商城玩法
    "购买": {
        "usage": "购买 @用户",
        "description": "购买一位群友作为你的“奴隶”。"
    },
    "强制购买": {
        "usage": "强制购买 @用户",
        "description": "花费更多Astr币抢夺已有主人的群友。"
    },
    "出售": {
        "usage": "出售 @用户",
        "description": "出售你拥有的“奴隶”以换取Astr币。"
    },
    "打工": {
        "usage": "打工 @用户",
        "description": "命令你的“奴隶”为你工作。"
    },
    "赎身": {
        "usage": "赎身",
        "description": "当你被购买时，为自己赎回自由。"
    },
    "商城状态": {
        "usage": "商城状态",
        "description": "查看你在商城系统中的详细状态。"
    },
    "强制赎身": {
        "usage": "强制赎身",
        "description": "在未打工的情况下，用更多Astr币强制赎回自由。"
    },
    "一键打工": {
        "usage": "一键打工 <工作>@用户",
        "description": "自动完成购买、打工、出售的全流程操作。"
    },
    # 商店与冒险
    "商店": {
        "usage": "商店 <道具/食物/礼物>",
        "description": "查看商店指定类别的商品。"
    },
    "买入": {
        "usage": "买入 <商品ID> [数量]",
        "description": "从商店购买指定ID的商品。"
    },
    "我的背包": {
        "usage": "我的背包",
        "description": "查看你的物品、Astr币和体力值。"
    },
    "使用": {
        "usage": "使用 <物品名> [数量]",
        "description": "使用背包中的道具或食物。"
    },
    "一键使用": {
        "usage": "一键使用 <物品名> [数量]",
        "description": "从商城购买道具或食物并使用。"
    },
    "冒险": {
        "usage": "冒险 [次数]",
        "description": "消耗20体力进行一次冒险。"
    },
    "超级冒险": {
        "usage": "超级冒险",
        "description": "消耗所有可用体力进行连续冒险。"
    },
    "我的状态": {
        "usage": "我的状态",
        "description": "查看当前激活的增益效果。"
    },
    # 社交玩法
    "赠礼": {
        "usage": "赠礼 <礼物名> @用户",
        "description": "赠送礼物，提升对方对你的好感度。"
    },
    "约会": {
        "usage": "约会 @用户",
        "description": "邀请用户进行双人约会，影响双方好感度。"
    },
    "缔结": {
        "usage": "缔结 <关系名> @用户",
        "description": "好感度满后，缔结唯一特殊关系。"
    },
    "解除关系": {
        "usage": "解除关系 @用户",
        "description": "单方面解除与用户的特殊关系。"
    },
    "关系": {
        "usage": "关系 @用户",
        "description": "查看你与指定用户的详细关系。"
    },
    "我的关系网": {
        "usage": "我的关系网",
        "description": "查看与你好感度最高的5位朋友。"
    },
    "赠送": {
        "usage": "赠送 <金额> @用户",
        "description": "向指定用户赠送Astr币。"
    }
}

# -------------------------------------------------------------------
# 2. 命令卡片生成函数
# -------------------------------------------------------------------
async def generate_command_card() -> Optional[str]:
    """
    生成包含所有命令帮助信息的图片卡片。
    """
    try:
        # --- 布局和样式常量 ---
        WIDTH = 1280
        COLUMNS = 2
        ITEM_WIDTH, ITEM_HEIGHT = 580, 110  # 每个命令框的尺寸
        GAP_X, GAP_Y = 40, 30  # 框之间的间距
        MARGIN_X = (WIDTH - (COLUMNS * ITEM_WIDTH) - (COLUMNS - 1) * GAP_X) // 2
        MARGIN_TOP, MARGIN_BOTTOM = 180, 80
        
        # 动态计算总高度
        num_rows = math.ceil(len(COMMANDS_INFO) / COLUMNS)
        HEIGHT = MARGIN_TOP + (num_rows * ITEM_HEIGHT) + ((num_rows - 1) * GAP_Y) + MARGIN_BOTTOM

        # --- 初始化画布 ---
        card, draw = utils.create_base_card(WIDTH, int(HEIGHT), add_decorations=False)
        if card is None: 
            return None

        # --- 加载字体 ---
        title_font = utils.get_font(70)
        cmd_name_font = utils.get_font(36)
        cmd_usage_font = utils.get_font(28)
        timestamp_font = utils.get_font(22)

        # --- 绘制标题 ---
        title_text = "命令帮助手册"
        w, _ = utils.get_text_dimensions(title_text, title_font)
        utils.text_with_outline(draw, ((WIDTH - w) / 2, 60), title_text, title_font, (255, 215, 0), (0, 0, 0))

        # --- 遍历并绘制所有命令项 ---
        for i, (command_name, command_data) in enumerate(COMMANDS_INFO.items()):
            row, col = i // COLUMNS, i % COLUMNS
            x = MARGIN_X + col * (ITEM_WIDTH + GAP_X)
            y = MARGIN_TOP + row * (ITEM_HEIGHT + GAP_Y)

            # 绘制背景框
            draw.rounded_rectangle([(x, y), (x + ITEM_WIDTH, y + ITEM_HEIGHT)], radius=15, fill=(40, 40, 40, 180))

            # 绘制文本信息
            text_x = x + 30
            
            # 绘制命令名称
            draw.text((text_x, y + 15), command_name, font=cmd_name_font, fill=(255, 255, 255))
            
            # 绘制命令用法（根据您的要求格式化）
            usage_text = f"命令：{command_data['usage']}"
            draw.text((text_x, y + 60), usage_text, font=cmd_usage_font, fill=(200, 200, 200))
        
        # --- 绘制时间戳 ---
        timestamp_text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        draw.text((WIDTH - 20, int(HEIGHT) - 20), timestamp_text, font=timestamp_font, fill=(180, 180, 180), anchor="rs")

        # --- 保存并返回图片路径 ---
        output_dir = os.path.join(utils.BASE_DIR, "data/command_cards")
        os.makedirs(output_dir, exist_ok=True)
        file_name = f"command_list_{int(datetime.now().timestamp())}.png"
        output_path = os.path.join(output_dir, file_name)
        
        # 将RGBA转换为RGB以保存为PNG
        card.convert("RGB").save(output_path, "PNG", quality=95)
        logger.info(f"已成功生成命令帮助卡片: {output_path}")

        return output_path

    except Exception as e:
        logger.error(f"Pillow生成命令卡片失败: {e}", exc_info=True)
        return None