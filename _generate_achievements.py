# feifeisupermarket/_generate_achievements.py

import os
import math
import textwrap
from typing import List, Dict, Optional
from PIL import ImageDraw
from datetime import datetime
from astrbot.api import logger

# 导入全新的绘图工具箱
from . import drawing_utils as utils


def _draw_achievement_icon(draw: ImageDraw.Draw, position: tuple, size: int, unlocked: bool):
    """
    一个简单的辅助函数，用于绘制成就图标（一个星星）。
    这个函数是成就墙专用的，所以保留在此文件中。
    """
    x, y = position
    star_color = (255, 215, 0) if unlocked else (100, 100, 100)
    
    # 绘制一个简单的五角星
    p1 = (x + size / 2, y)
    p2 = (x + size * 0.77, y + size * 0.95)
    p3 = (x, y + size * 0.38)
    p4 = (x + size, y + size * 0.38)
    p5 = (x + size * 0.23, y + size * 0.95)
    
    draw.polygon([p1, p2, p3, p4, p5], fill=star_color)


async def generate_achievements_image(
    user_name: str,
    unlocked_ids: List[str],
    all_achievements: Dict
) -> Optional[str]:
    """
    使用重构后的工具函数生成用户的个人成就列表图片。

    Args:
        user_name (str): 用户昵称。
        unlocked_ids (List[str]): 用户已解锁的成就ID列表。
        all_achievements (Dict): 包含所有成就定义的字典。

    Returns:
        Optional[str]: 成功则返回图片路径，失败则返回None。
    """
    try:
        # --- 1. 布局和样式常量 ---
        WIDTH = 1280
        COLUMNS = 2
        ITEM_WIDTH, ITEM_HEIGHT = 560, 160
        GAP_X, GAP_Y = 60, 40
        MARGIN_X = (WIDTH - (COLUMNS * ITEM_WIDTH) - (COLUMNS - 1) * GAP_X) // 2
        MARGIN_TOP, MARGIN_BOTTOM = 180, 80
        
        # 动态计算总高度
        num_rows = math.ceil(len(all_achievements) / COLUMNS)
        HEIGHT = MARGIN_TOP + (num_rows * ITEM_HEIGHT) + ((num_rows - 1) * GAP_Y) + MARGIN_BOTTOM

        # 颜色定义
        TITLE_COLOR, OUTLINE_COLOR = (255, 215, 0), (0, 0, 0)
        UNLOCKED_NAME_COLOR, LOCKED_NAME_COLOR = (255, 215, 0), (200, 200, 200)
        UNLOCKED_DESC_COLOR, LOCKED_DESC_COLOR = (220, 220, 220), (120, 120, 120)
        REWARD_COLOR, TIMESTAMP_COLOR = (129, 255, 115), (180, 180, 180)

        # --- 2. 初始化画布 ---
        # 使用工具函数创建基础卡片，不包含装饰
        card, draw = utils.create_base_card(WIDTH, int(HEIGHT), add_decorations=False)
        if card is None: 
            return None

        # --- 3. 加载字体 ---
        title_font = utils.get_font(70)
        ach_name_font = utils.get_font(32)
        ach_desc_font = utils.get_font(24)
        ach_reward_font = utils.get_font(22)
        timestamp_font = utils.get_font(22)

        # --- 4. 绘制标题 ---
        title_text = f"{user_name} 的成就墙"
        w, _ = utils.get_text_dimensions(title_text, title_font)
        utils.text_with_outline(draw, ((WIDTH - w) / 2, 60), title_text, title_font, TITLE_COLOR, OUTLINE_COLOR)

        # --- 5. 遍历并绘制所有成就项 ---
        for i, (ach_id, ach_data) in enumerate(all_achievements.items()):
            unlocked = ach_id in unlocked_ids
            
            row, col = i // COLUMNS, i % COLUMNS
            x = MARGIN_X + col * (ITEM_WIDTH + GAP_X)
            y = MARGIN_TOP + row * (ITEM_HEIGHT + GAP_Y)

            # 绘制背景框
            box_fill = (40, 40, 40, 180) if unlocked else (20, 20, 20, 180)
            draw.rounded_rectangle([(x, y), (x + ITEM_WIDTH, y + ITEM_HEIGHT)], radius=15, fill=box_fill)

            # 绘制图标
            _draw_achievement_icon(draw, (x + 25, y + (ITEM_HEIGHT - 60) / 2), 60, unlocked)

            # 绘制文本信息
            text_x = x + 125
            draw.text((text_x, y + 20), ach_data['name'], font=ach_name_font, fill=(UNLOCKED_NAME_COLOR if unlocked else LOCKED_NAME_COLOR))
            
            desc_color = UNLOCKED_DESC_COLOR if unlocked else LOCKED_DESC_COLOR
            for j, line in enumerate(textwrap.wrap(ach_data['description'], width=35)[:2]):
                draw.text((text_x, y + 60 + j * 28), line, font=ach_desc_font, fill=desc_color)

            if unlocked:
                reward_text = f"奖励: {ach_data.get('reward_points', 0)}币"
                if ach_data.get('reward_title'):
                    reward_text += f" | 称号: {ach_data['reward_title']}"
                draw.text((text_x, y + ITEM_HEIGHT - 35), reward_text, font=ach_reward_font, fill=REWARD_COLOR)

        # --- 6. 绘制时间戳 ---
        timestamp_text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        draw.text((WIDTH - 20, HEIGHT - 20), timestamp_text, font=timestamp_font, fill=TIMESTAMP_COLOR, anchor="rs")

        # --- 7. 保存并返回图片路径 ---
        output_dir = os.path.join(utils.BASE_DIR, "data/achievements")
        os.makedirs(output_dir, exist_ok=True)
        safe_user_name = "".join(c for c in user_name if c.isalnum()) or "user"
        file_name = f"achievements_{safe_user_name}_{int(datetime.now().timestamp())}.png"
        output_path = os.path.join(output_dir, file_name)
        
        card.convert("RGB").save(output_path, "PNG", quality=95)
        logger.info(f"已成功为 {user_name} 生成成就墙图片: {output_path}")

        return output_path

    except Exception as e:
        logger.error(f"Pillow生成成就图片失败: {e}", exc_info=True)
        return None