# feifeisupermarket/_generate_work_list.py

import os
from typing import Optional

from astrbot.api import logger
from .market import JOBS, MarketManager

# 导入全新的绘图工具箱
from . import drawing_utils as utils


async def generate_work_list_image(output_path: str) -> bool:
    """
    使用重构后的工具函数生成包含所有工作选项的静态图片。
    
    Args:
        output_path (str): 图片的完整保存路径。
        
    Returns:
        bool: 成功则返回True，失败则返回False。
    """
    try:
        # --- 1. 布局和样式常量 ---
        WIDTH, HEIGHT = 1280, 720
        TITLE_COLOR = (255, 215, 0)
        OUTLINE_COLOR = (0, 0, 0)
        JOB_NAME_COLOR = (255, 255, 255)
        DETAIL_COLOR = (200, 200, 200)
        FOOTER_COLOR = (180, 180, 180)

        # --- 2. 初始化画布 ---
        # 使用工具函数创建基础卡片，不包含装饰
        card, draw = utils.create_base_card(WIDTH, HEIGHT, add_decorations=False)
        if card is None:
            return False

        # --- 3. 加载字体 ---
        # 此处调用会正确从 drawing_utils.py 加载默认的 "可爱字体.ttf"
        title_font = utils.get_font(70)
        job_font = utils.get_font(40)
        detail_font = utils.get_font(32)
        footer_font = utils.get_font(28)

        # --- 4. 绘制标题 ---
        title_text = "打工列表"
        w, _ = utils.get_text_dimensions(title_text, title_font)
        utils.text_with_outline(draw, ((WIDTH - w) / 2, 60), title_text, title_font, TITLE_COLOR, OUTLINE_COLOR)

        # --- 5. 遍历并绘制工作列表 ---
        sorted_jobs = MarketManager.get_sorted_jobs()
        start_y = 180
        line_height = 65
        
        for i, job_name in enumerate(sorted_jobs, 1):
            job_info = JOBS[job_name]
            y_pos = start_y + (i - 1) * line_height
            
            # 绘制工作名称
            job_text = f"{i}. {job_name}"
            draw.text((100, y_pos), job_text, font=job_font, fill=JOB_NAME_COLOR)
            
            # 拼接并绘制详细信息 (收益和成功率)
            reward_val = job_info['reward']
            reward_text = f"{reward_val[0]:.0f}-{reward_val[1]:.0f}" if isinstance(reward_val, tuple) else f"{reward_val:.0f}"
            detail_text = f"收益: {reward_text}Astr币 | 成功率: {int(job_info['success_rate']*100)}%"
            
            # 右对齐绘制
            w, _ = utils.get_text_dimensions(detail_text, detail_font)
            draw.text((WIDTH - w - 100, y_pos + 5), detail_text, font=detail_font, fill=DETAIL_COLOR)

        # --- 6. 绘制底部提示 ---
        footer_text = "回复数字或工作名称进行选择"
        w, _ = utils.get_text_dimensions(footer_text, footer_font)
        draw.text(((WIDTH - w) / 2, HEIGHT - 60), footer_text, font=footer_font, fill=FOOTER_COLOR)

        # --- 7. 保存图片 ---
        card.save(output_path, "PNG")
        logger.info(f"已成功生成新的打工列表图片: {output_path}")
        return True

    except Exception as e:
        logger.error(f"Pillow生成打工列表图片失败: {e}", exc_info=True)
        return False