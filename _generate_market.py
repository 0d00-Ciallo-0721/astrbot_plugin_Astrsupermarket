# feifeisupermarket/_generate_market.py

import os
from datetime import datetime
from typing import Dict, Any, Optional

from astrbot.api import logger

# 导入全新的绘图工具箱，所有绘图操作都将通过它进行
from . import drawing_utils as utils


async def generate_market_card_pillow(
    user_id: str,
    user_name: str,
    avatar_url: str,
    card_type: str,
    card_data: Dict[str, Any],
    title: Optional[str] = None
) -> Optional[str]:
    """
    使用重构后的工具函数生成商城卡片。
    此函数现在只负责内容的布局，所有底层绘图已移至drawing_utils。

    Args:
        user_id: 用户ID
        user_name: 用户名称
        avatar_url: 头像URL
        card_type: 卡片类型 ('coins', 'status')
        card_data: 卡片所需的数据
        title: 用户佩戴的称号

    Returns:
        成功则返回图片路径，失败则返回None
    """
    try:
        # --- 1. 布局和样式常量 ---
        WIDTH, HEIGHT = 1280, 720
        TITLE_COLOR, OUTLINE_COLOR = (255, 215, 0), (0, 0, 0)
        TEXT_COLOR, SUB_TEXT_COLOR = (255, 255, 255), (200, 200, 200)
        FREE_COLOR = (173, 255, 47) # 自由身状态的颜色

        # --- 2. 初始化画布和通用元素 ---
        # 使用工具函数创建带装饰的基础卡片
        card, draw = utils.create_base_card(WIDTH, HEIGHT, add_decorations=True)
        if card is None:
            return None
        
        # 使用工具函数绘制整个左侧的用户信息区域（头像、昵称、称号）
        await utils.draw_user_profile(card, draw, avatar_url, user_name, title)

        # --- 3. 加载所需字体 ---
        title_font = utils.get_font(70)
        label_font = utils.get_font(35)
        value_font = utils.get_font(42)
        highlight_font = utils.get_font(45)
        timestamp_font = utils.get_font(22)

        # --- 4. 根据卡片类型绘制特定内容 ---
        # 所有内容绘制在卡片的右半部分
        content_start_x = WIDTH // 2 + 40

        if card_type == 'status':
            title_text = "🏪 Astr商城状态"
            w, _ = utils.get_text_dimensions(title_text, title_font)
            # 标题居中于右半部分
            utils.text_with_outline(draw, (WIDTH * 0.75 - w / 2, 100), title_text, title_font, TITLE_COLOR, OUTLINE_COLOR)
            
            # 绘制详细状态信息
            current_y = 220
            line_height = 55
            
            # 身份状态
            if card_data.get('owner_id'):
                draw.text((content_start_x, current_y), f"当前主人: {card_data.get('owner_name', '未知')}", font=value_font, fill=TEXT_COLOR)
                current_y += line_height
                work_status = "✅ 已为主人打工" if card_data.get('has_worked_for_owner') else "❌ 尚未为主人打工"
                draw.text((content_start_x, current_y), work_status, font=label_font, fill=SUB_TEXT_COLOR)
            else:
                draw.text((content_start_x, current_y), "当前状态: ✨自由身✨", font=value_font, fill=FREE_COLOR)
            
            current_y += int(line_height * 1.5)

            # 拥有的奴仆列表
            owned = card_data.get('owned_members', [])
            draw.text((content_start_x, current_y), f"名下奴仆 ({len(owned)}/3):", font=value_font, fill=TEXT_COLOR)
            current_y += line_height
            
            if not owned:
                draw.text((content_start_x + 20, current_y), "无", font=label_font, fill=SUB_TEXT_COLOR)
            else:
                for member in owned[:5]: # 最多显示5个
                    status = "✅" if member.get('has_worked') else "❌"
                    draw.text((content_start_x + 20, current_y), f"- {member.get('name', '未知')} {status}", font=label_font, fill=SUB_TEXT_COLOR)
                    current_y += 45

        # --- 5. 添加时间戳 ---
        timestamp_text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        draw.text((WIDTH - 20, HEIGHT - 20), timestamp_text, font=timestamp_font, fill=(180, 180, 180), anchor="rs")
        
        # --- 6. 保存图片 ---
        output_dir = os.path.join(utils.BASE_DIR, "data/market_cards")
        os.makedirs(output_dir, exist_ok=True)
        file_name = f"market_card_{user_id}_{card_type}_{int(datetime.now().timestamp())}.png"
        output_path = os.path.join(output_dir, file_name)
        
        card.convert("RGB").save(output_path, "PNG", quality=95)
        return output_path

    except Exception as e:
        logger.error(f"Pillow生成商城卡片失败: {e}", exc_info=True)
        return None