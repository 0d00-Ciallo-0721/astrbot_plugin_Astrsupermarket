# feifeisupermarket/_generate_leaderboard.py

import os
import textwrap
from datetime import datetime
from typing import Dict, List, Optional

from astrbot.api import logger

# 导入全新的绘图工具箱
from . import drawing_utils as utils


async def generate_leaderboard_image(
    board_type: str,
    top_users: List[Dict],
    requester_data: Dict
) -> Optional[str]:
    """
    使用重构后的工具函数生成功能完善的排行榜图片。

    Args:
        board_type (str): 榜单类型 ('财富', '签到', '欧皇').
        top_users (List[Dict]): 前10名用户数据列表。每个字典包含 'id', 'name', 'value'。
        requester_data (Dict): 请求者的数据。包含 'rank', 'name', 'value'。

    Returns:
        Optional[str]: 成功则返回图片路径，失败则返回None。
    """
    try:
        # --- 1. 布局和样式常量 ---
        WIDTH, HEIGHT = 1280, 720
        TITLE_COLOR = (255, 215, 0)
        TEXT_COLOR = (255, 255, 255)
        SUB_TEXT_COLOR = (200, 200, 200)
        OUTLINE_COLOR = (0, 0, 0)
        RANK_COLORS = {1: (255, 215, 0), 2: (192, 192, 192), 3: (205, 127, 50)}
        
        # 动态内容配置
        BOARD_CONFIG = {
            '财富': {'title': 'Astr币财富榜', 'unit': 'Astr币'},
            '签到': {'title': '签到毅力榜', 'unit': '天'},
            '欧皇': {'title': '欧皇幸运榜', 'unit': '次'}
        }
        config = BOARD_CONFIG.get(board_type, {'title': '排行榜', 'unit': ''})

        # --- 2. 初始化画布 ---
        # 使用工具函数创建基础卡片，不含装饰
        card, draw = utils.create_base_card(WIDTH, HEIGHT, add_decorations=False)
        if card is None:
            return None

        # --- 3. 加载字体 ---
        title_font = utils.get_font(70)
        header_font = utils.get_font(36)
        item_font = utils.get_font(36) # 统一列表项字体
        footer_font = utils.get_font(30)
        timestamp_font = utils.get_font(22)

        # --- 4. 绘制标题 ---
        title_text = config['title']
        w, _ = utils.get_text_dimensions(title_text, title_font)
        utils.text_with_outline(draw, ((WIDTH - w) / 2, 50), title_text, title_font, TITLE_COLOR, OUTLINE_COLOR)

        # --- 5. 绘制列表头和分割线 ---
        header_y = 160
        draw.text((100, header_y), "排名", font=header_font, fill=SUB_TEXT_COLOR)
        draw.text((250, header_y), "用户", font=header_font, fill=SUB_TEXT_COLOR)
        w, _ = utils.get_text_dimensions("数值", header_font)
        draw.text((WIDTH - 100 - w, header_y), "数值", font=header_font, fill=SUB_TEXT_COLOR)
        draw.line([(80, header_y + 50), (WIDTH - 80, header_y + 50)], fill=(100, 100, 100), width=2)

        # --- 6. 绘制Top 10用户列表 ---
        start_y = 225
        line_height = 48
        for i, user in enumerate(top_users):
            rank = i + 1
            y_pos = start_y + i * line_height
            
            # 绘制排名，前三名使用特殊颜色
            rank_color = RANK_COLORS.get(rank, TEXT_COLOR)
            draw.text((100, y_pos), f"#{rank}", font=item_font, fill=rank_color)
            
            # 绘制昵称 (限制长度)
            user_name = textwrap.shorten(user['name'], width=20, placeholder="...")
            draw.text((250, y_pos), user_name, font=item_font, fill=TEXT_COLOR)

            # 绘制数值 (右对齐)
            value_text = f"{user['value']} {config['unit']}"
            w, _ = utils.get_text_dimensions(value_text, item_font)
            draw.text((WIDTH - 100 - w, y_pos), value_text, font=item_font, fill=TEXT_COLOR)

        # --- 7. 绘制页脚（当前请求者信息） ---
        footer_y = HEIGHT - 80
        draw.rectangle([(50, footer_y - 15), (WIDTH - 50, footer_y + 45)], fill=(0, 0, 0, 100))
        
        req_name = textwrap.shorten(requester_data['name'], width=25, placeholder="...")
        req_info_text = f"您是: {req_name}   |   当前排名: #{requester_data['rank']}   |   数值: {requester_data['value']} {config['unit']}"
        w, _ = utils.get_text_dimensions(req_info_text, footer_font)
        draw.text(((WIDTH - w) / 2, footer_y), req_info_text, font=footer_font, fill=TEXT_COLOR)

        # --- 8. 绘制时间戳 ---
        timestamp_text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        draw.text((WIDTH - 20, HEIGHT - 20), timestamp_text, font=timestamp_font, fill=SUB_TEXT_COLOR, anchor="rs")

        # --- 9. 保存并返回图片路径 ---
        output_dir = os.path.join(utils.BASE_DIR, "data/leaderboards")
        os.makedirs(output_dir, exist_ok=True)
        file_name = f"leaderboard_{board_type}_{int(datetime.now().timestamp())}.png"
        output_path = os.path.join(output_dir, file_name)
        
        card.convert("RGB").save(output_path, "PNG", quality=95)
        logger.info(f"已成功生成 {config['title']} 图片: {output_path}")
        
        return output_path

    except Exception as e:
        logger.error(f"Pillow生成排行榜图片失败: {e}", exc_info=True)
        return None