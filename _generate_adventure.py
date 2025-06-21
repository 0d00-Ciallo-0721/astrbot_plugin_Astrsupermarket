import os
import textwrap
from datetime import datetime
from typing import Dict, Optional, Any, List
from PIL import ImageDraw, Image as PILImage
from astrbot.api import logger

# 导入绘图工具箱
from . import drawing_utils as utils

async def generate_adventure_report_card(results: Dict[str, Any]) -> Optional[str]:
    """
    生成冒险报告卡片
    
    Args:
        results: 冒险结果数据
    
    Returns:
        生成的图片路径，失败则返回None
    """
    try:
        # --- 1. 布局和样式常量 ---
        WIDTH, HEIGHT = 1280, 720
        
        # --- 2. 初始化画布 ---
        card, draw = utils.create_base_card(WIDTH, HEIGHT, add_decorations=True)
        if card is None: return None
        
        # --- 3. 加载字体 ---
        title_font = utils.get_font(60)
        subtitle_font = utils.get_font(36)
        info_font = utils.get_font(30)
        event_title_font = utils.get_font(32)
        event_desc_font = utils.get_font(24)
        effect_font = utils.get_font(26)
        timestamp_font = utils.get_font(22)
        
        # --- 4. 绘制标题 ---
        title_text = "冒险报告"
        w, _ = utils.get_text_dimensions(title_text, title_font)
        title_position = ((WIDTH - w) / 2, 35)
        utils.text_with_outline(draw, title_position, title_text, title_font, (255, 215, 0), (0, 0, 0))
        
        # --- 5. 绘制冒险概况（分为左右两块）---
        # 左侧信息
        left_col_x = 50
        # 日期和时间
        date_text = f"冒险日期: {results['start_time']}"
        draw.text((left_col_x, 120), date_text, font=info_font, fill=(220, 220, 220))
        
        # 冒险次数
        times_text = f"冒险次数: {results['adventure_times']}次"
        draw.text((left_col_x, 160), times_text, font=info_font, fill=(220, 220, 220))
        
        # 体力消耗
        stamina_text = f"体力消耗: {results['stamina_cost']} ({results['stamina_before']} → {results['stamina_after']})"
        draw.text((left_col_x, 200), stamina_text, font=info_font, fill=(220, 220, 220))
        
        # 右侧信息
        right_col_x = WIDTH // 2 + 50
        
        # Astr币变化
        points_change = results['total_points_gain']
        if points_change > 0:
            points_color = (50, 255, 50)  # 绿色
            points_text = f"Astr币: +{points_change} ({results['points_before']} → {results['points_after']})"
        elif points_change < 0:
            points_color = (255, 50, 50)  # 红色
            points_text = f"Astr币: {points_change} ({results['points_before']} → {results['points_after']})"
        else:
            points_color = (220, 220, 220)  # 白色
            points_text = f"Astr币: 无变化 ({results['points_before']})"
        
        draw.text((right_col_x, 120), points_text, font=info_font, fill=points_color)
        
        # 获得物品
        if results["items_gained"]:
            items_text = "获得物品:"
            draw.text((right_col_x, 160), items_text, font=info_font, fill=(220, 220, 220))
            
            for i, item in enumerate(results["items_gained"]):
                if i < 3:  # 最多显示3个物品，避免过多
                    item_text = f"- {item['name']} ({item['category']})"
                    draw.text((right_col_x + 20, 200 + i * 40), item_text, font=info_font, fill=(255, 215, 0))
                elif i == 3:
                    more_text = f"- 等{len(results['items_gained']) - 3}件物品..."
                    draw.text((right_col_x + 20, 200 + 3 * 40), more_text, font=info_font, fill=(255, 215, 0))
                    break

        # 显示自动使用的物品
        if "auto_used_items" in results and results["auto_used_items"]:
            auto_use_text = "自动使用物品(超出上限):"
            draw.text((right_col_x, 320), auto_use_text, font=info_font, fill=(220, 220, 220))
            
            for i, item in enumerate(results["auto_used_items"]):
                if i < 2:  # 最多显示2个自动使用物品
                    item_text = f"- {item['name']}"
                    draw.text((right_col_x + 20, 360 + i * 40), item_text, font=info_font, fill=(255, 165, 0))
                elif i == 2:
                    more_text = f"- 等{len(results['auto_used_items']) - 2}件物品..."
                    draw.text((right_col_x + 20, 360 + 2 * 40), more_text, font=info_font, fill=(255, 165, 0))
                    break


        # --- 6. 绘制分隔线 (提前到280像素位置) ---
        separator_y = 280
        draw.line([(50, separator_y), (WIDTH - 50, separator_y)], fill=(150, 150, 150), width=2)
        
        # --- 7. 绘制事件列表 ---
        events_title = "冒险事件"
        w, _ = utils.get_text_dimensions(events_title, subtitle_font)
        draw.text(((WIDTH - w) / 2, separator_y + 20), events_title, font=subtitle_font, fill=(255, 255, 255))
        
        # 计算每个事件的高度和位置
        events_start_y = separator_y + 70  # 提前事件起始位置
        event_height = 90  # 增加事件高度
        events_per_column = 4  # 每列显示4个事件
        event_width = (WIDTH - 150) / 2
        
        for i, event in enumerate(results["events"]):
            col = i // events_per_column
            row = i % events_per_column
            
            x = 50 + col * (event_width + 50)
            y = events_start_y + row * event_height
            
            # 绘制事件背景
            draw.rounded_rectangle(
                [(x, y), (x + event_width, y + event_height - 10)],
                radius=10,
                fill=(40, 40, 40, 180)
            )
            
            # 绘制事件标题
            draw.text((x + 15, y + 10), event["name"], font=event_title_font, fill=(255, 255, 255))
            
            # 绘制事件描述（截断过长的描述）
            desc = event["description"]
            if len(desc) > 65:  # 允许更长的描述
                desc = desc[:62] + "..."
            draw.text((x + 15, y + 45), desc, font=event_desc_font, fill=(200, 200, 200))
            
            # 绘制效果（如果有）
            effects_text = []
            for effect_type, effect_desc in event.get("effects", {}).items():
                if effect_type not in ["item_id", "return"] and effect_desc:  # 排除内部使用的字段
                    effects_text.append(effect_desc)
            
            if effects_text:
                effect_x = x + event_width - 20
                for j, effect in enumerate(effects_text[:2]):  # 最多显示2个效果
                    # 根据效果类型设置颜色
                    if "+" in effect:
                        effect_color = (50, 255, 50)  # 绿色
                    elif "-" in effect:
                        effect_color = (255, 50, 50)  # 红色
                    else:
                        effect_color = (255, 215, 0)  # 金色
                    
                    # 右对齐绘制效果
                    effect_width, _ = utils.get_text_dimensions(effect, effect_font)
                    draw.text((effect_x - effect_width, y + 10 + j * 30), effect, font=effect_font, fill=effect_color)
        
        # --- 8. 绘制新解锁成就（如果有）---
        if "new_achievement" in results:
            achievement_text = f"🏆 新成就解锁: {results['new_achievement']}"
            achievement_width, _ = utils.get_text_dimensions(achievement_text, info_font)
            
            # 绘制成就背景
            achievement_y = HEIGHT - 100
            draw.rounded_rectangle(
                [(WIDTH/2 - achievement_width/2 - 20, achievement_y - 10), 
                 (WIDTH/2 + achievement_width/2 + 20, achievement_y + 30)],
                radius=10,
                fill=(60, 60, 150, 220)
            )
            
            # 绘制成就文本
            draw.text((WIDTH/2 - achievement_width/2, achievement_y), achievement_text, 
                      font=info_font, fill=(255, 255, 100))
        
        # 如果有冒险中断消息，显示它
        if "message" in results and "中断" in results["message"] and any("return" in event.get("effects", {}) for event in results["events"]):
            message_text = f"⚠️ {results['message']}"
            message_width, _ = utils.get_text_dimensions(message_text, info_font)
            
            # 绘制消息背景
            message_y = HEIGHT - 160
            draw.rounded_rectangle(
                [(WIDTH/2 - message_width/2 - 20, message_y - 10), 
                (WIDTH/2 + message_width/2 + 20, message_y + 30)],
                radius=10,
                fill=(150, 60, 60, 220)
            )
            
            # 绘制消息文本
            draw.text((WIDTH/2 - message_width/2, message_y), message_text, 
                    font=info_font, fill=(255, 255, 200))
        
        # --- 9. 添加时间戳 ---
        timestamp_text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        draw.text((WIDTH - 20, HEIGHT - 20), timestamp_text, font=timestamp_font, fill=(180, 180, 180), anchor="rs")
        
        # --- 10. 保存图片 ---
        output_dir = os.path.join(utils.BASE_DIR, "data/adventure_reports")
        os.makedirs(output_dir, exist_ok=True)
        file_name = f"adventure_{int(datetime.now().timestamp())}.png"
        output_path = os.path.join(output_dir, file_name)
        card.save(output_path, "PNG")
        return output_path
        
    except Exception as e:
        logger.error(f"生成冒险报告卡片失败: {e}", exc_info=True)
        return None
