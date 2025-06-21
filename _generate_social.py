# feifeisupermarket/_generate_social.py

import os
from datetime import datetime
from typing import Dict, Any, Optional, List

from astrbot.api import logger

# 导入绘图工具箱
from . import drawing_utils as utils
from PIL import Image, ImageDraw


async def generate_relationship_card(
    user_a_id: str,
    user_a_name: str,
    user_a_avatar: str,
    user_b_id: str,
    user_b_name: str,
    user_b_avatar: str,
    relationship_data: Dict[str, Any],
    user_a_title: Optional[str] = None,
    user_b_title: Optional[str] = None
) -> Optional[str]:
    """
    生成关系卡片
    """
    try:
        # --- 1. 布局和样式常量 ---
        WIDTH, HEIGHT = 1280, 720
        
        # --- 2. 初始化画布 ---
        card, draw = utils.create_base_card(WIDTH, HEIGHT, add_decorations=True)
        if card is None: return None
        
        # --- 3. 加载字体 ---
        title_font = utils.get_font(60)
        subtitle_font = utils.get_font(48)
        normal_font = utils.get_font(36)
        value_font = utils.get_font(42)
        small_font = utils.get_font(24)
        
        # --- 4. 绘制标题 ---
        special_relation = relationship_data.get("special_relation")
        if special_relation:
            title_text = f"♥ {special_relation} ♥"
            title_color = (255, 105, 180)  # 粉色
        else:
            title_text = "关系卡片"
            title_color = (255, 215, 0)  # 金色
            
        w, _ = utils.get_text_dimensions(title_text, title_font)
        utils.text_with_outline(draw, ((WIDTH - w) / 2, 40), title_text, title_font, title_color, (0, 0, 0))
        
        # --- 5. 绘制用户A信息（左侧） ---
        avatar_a_x = WIDTH // 4
        avatar_a_y = 160
        avatar_size = 200
        
        avatar_a = await utils.download_image(user_a_avatar)
        if avatar_a is None:
            avatar_a = utils.get_default_avatar()
            
        avatar_a = avatar_a.resize((avatar_size, avatar_size), Image.LANCZOS)
        avatar_a = utils.crop_to_circle(avatar_a)
        
        # 头像边框
        avatar_canvas_a = Image.new("RGBA", (avatar_size + 16, avatar_size + 16), (0, 0, 0, 0))
        draw_border_a = ImageDraw.Draw(avatar_canvas_a)
        draw_border_a.ellipse((0, 0, avatar_size + 15, avatar_size + 15), outline=(255, 255, 255, 230), width=8)
        avatar_canvas_a.paste(avatar_a, (8, 8), avatar_a)
        
        # 绘制头像
        card.paste(avatar_canvas_a, (avatar_a_x - avatar_size // 2 - 8, avatar_a_y), avatar_canvas_a)
        
        # 绘制用户名
        w, _ = utils.get_text_dimensions(user_a_name, subtitle_font)
        draw.text((avatar_a_x - w // 2, avatar_a_y + avatar_size + 20), user_a_name, font=subtitle_font, fill=(255, 255, 255))
        
        # 绘制称号
        if user_a_title:
            title_text = f"「{user_a_title}」"
            w, _ = utils.get_text_dimensions(title_text, small_font)
            utils.text_with_outline(draw, (avatar_a_x - w // 2, avatar_a_y + avatar_size + 65), 
                                  title_text, small_font, (0, 229, 255), (0, 0, 0))
        
        # --- 6. 绘制用户B信息（右侧） ---
        avatar_b_x = WIDTH * 3 // 4
        avatar_b_y = 160
        
        avatar_b = await utils.download_image(user_b_avatar)
        if avatar_b is None:
            avatar_b = utils.get_default_avatar()
            
        avatar_b = avatar_b.resize((avatar_size, avatar_size), Image.LANCZOS)
        avatar_b = utils.crop_to_circle(avatar_b)
        
        # 头像边框
        avatar_canvas_b = Image.new("RGBA", (avatar_size + 16, avatar_size + 16), (0, 0, 0, 0))
        draw_border_b = ImageDraw.Draw(avatar_canvas_b)
        draw_border_b.ellipse((0, 0, avatar_size + 15, avatar_size + 15), outline=(255, 255, 255, 230), width=8)
        avatar_canvas_b.paste(avatar_b, (8, 8), avatar_b)
        
        # 绘制头像
        card.paste(avatar_canvas_b, (avatar_b_x - avatar_size // 2 - 8, avatar_b_y), avatar_canvas_b)
        
        # 绘制用户名
        w, _ = utils.get_text_dimensions(user_b_name, subtitle_font)
        draw.text((avatar_b_x - w // 2, avatar_b_y + avatar_size + 20), user_b_name, font=subtitle_font, fill=(255, 255, 255))
        
        # 绘制称号
        if user_b_title:
            title_text = f"「{user_b_title}」"
            w, _ = utils.get_text_dimensions(title_text, small_font)
            utils.text_with_outline(draw, (avatar_b_x - w // 2, avatar_b_y + avatar_size + 65), 
                                  title_text, small_font, (0, 229, 255), (0, 0, 0))
        
        # --- 7. 绘制关系线和好感度 ---
        center_y = 230
        
        # 获取好感度数据
        a_to_b = relationship_data.get("user_a_to_b_favorability", 0)
        a_to_b_level = relationship_data.get("user_a_to_b_level", "陌生人")
        b_to_a = relationship_data.get("user_b_to_a_favorability", 0)
        b_to_a_level = relationship_data.get("user_b_to_a_level", "陌生人")
        
        # 绘制连接线
        draw.line([(avatar_a_x + avatar_size // 2, center_y), (avatar_b_x - avatar_size // 2, center_y)], 
                 fill=(200, 200, 200), width=3)
        
        # 绘制A到B的箭头和好感度
        arrow_start_x = avatar_a_x + 80
        arrow_end_x = avatar_b_x - 80
        
        # 根据好感度设置颜色
        if a_to_b >= 90:
            a_to_b_color = (255, 192, 203)  # 粉色
        elif a_to_b >= 50:
            a_to_b_color = (144, 238, 144)  # 浅绿色
        else:
            a_to_b_color = (173, 216, 230)  # 浅蓝色
            
        draw.line([(arrow_start_x, center_y - 15), (arrow_end_x, center_y - 15)], 
                 fill=a_to_b_color, width=3)
        
        # 绘制箭头头部
        draw.polygon([(arrow_end_x - 15, center_y - 25), (arrow_end_x, center_y - 15), (arrow_end_x - 15, center_y - 5)], 
                    fill=a_to_b_color)
                    
        # 绘制好感度值和关系等级
        fav_text = f"{a_to_b} ({a_to_b_level})"
        w, _ = utils.get_text_dimensions(fav_text, normal_font)
        draw.text(((arrow_start_x + arrow_end_x) // 2 - w // 2, center_y - 50), fav_text, 
                 font=normal_font, fill=a_to_b_color)
        
        # 绘制B到A的箭头和好感度
        if b_to_a >= 90:
            b_to_a_color = (255, 192, 203)  # 粉色
        elif b_to_a >= 50:
            b_to_a_color = (144, 238, 144)  # 浅绿色
        else:
            b_to_a_color = (173, 216, 230)  # 浅蓝色
            
        draw.line([(arrow_end_x, center_y + 15), (arrow_start_x, center_y + 15)], 
                 fill=b_to_a_color, width=3)
                 
        # 绘制箭头头部
        draw.polygon([(arrow_start_x + 15, center_y + 5), (arrow_start_x, center_y + 15), (arrow_start_x + 15, center_y + 25)], 
                    fill=b_to_a_color)
                    
        # 绘制好感度值和关系等级
        fav_text = f"{b_to_a} ({b_to_a_level})"
        w, _ = utils.get_text_dimensions(fav_text, normal_font)
        draw.text(((arrow_start_x + arrow_end_x) // 2 - w // 2, center_y + 20), fav_text, 
                 font=normal_font, fill=b_to_a_color)
        
        # --- 9. 在卡片中下部统一显示说明信息 ---
        explanation_y = 450
        explanation_text = [
            "关系等级说明: 0-19 陌生人  20-49 熟人  50-89 朋友  90-99 挚友  100 唯一的你  101+ 灵魂伴侣",
            "提示: 赠送礼物可提升对方对你的好感度，约会会同时影响双方的好感度"
        ]
        
        for i, text in enumerate(explanation_text):
            w, _ = utils.get_text_dimensions(text, small_font)
            draw.text(((WIDTH - w) // 2, explanation_y + i * 35), text, 
                     font=small_font, fill=(220, 220, 220))
        
        # --- 10. 添加时间戳 ---
        timestamp_text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        timestamp_font = utils.get_font(22)
        draw.text((WIDTH - 20, HEIGHT - 20), timestamp_text, font=timestamp_font, fill=(180, 180, 180), anchor="rs")
        
        # --- 11. 保存图片 ---
        output_dir = os.path.join(utils.BASE_DIR, "data/social_cards")
        os.makedirs(output_dir, exist_ok=True)
        file_name = f"relationship_{user_a_id}_{user_b_id}_{int(datetime.now().timestamp())}.png"
        output_path = os.path.join(output_dir, file_name)
        
        card.convert("RGB").save(output_path, "PNG", quality=95)
        return output_path
        
    except Exception as e:
        logger.error(f"生成关系卡片失败: {e}", exc_info=True)
        return None



async def generate_date_report_card(
    user_a_id: str,
    user_a_name: str,
    user_a_avatar: str,
    user_b_id: str,
    user_b_name: str,
    user_b_avatar: str,
    date_results: Dict[str, Any]
) -> Optional[str]:
    """
    生成约会报告卡片
    
    Args:
        user_a_id: 用户A的ID
        user_a_name: 用户A的名称
        user_a_avatar: 用户A的头像URL
        user_b_id: 用户B的ID
        user_b_name: 用户B的名称
        user_b_avatar: 用户B的头像URL
        date_results: 约会结果数据
        
    Returns:
        生成的图片路径，失败则返回None
    """
    try:
        # --- 1. 布局和样式常量 ---
        WIDTH, HEIGHT = 1280, 720

        # --- 2. 初始化画布 ---
        card, draw = utils.create_base_card(WIDTH, HEIGHT, add_decorations=True)
        if card is None:
            return None

        # --- 3. 加载字体 ---
        title_font = utils.get_font(60)
        subtitle_font = utils.get_font(36)
        normal_font = utils.get_font(32)
        event_font = utils.get_font(28)
        small_font = utils.get_font(24)

        # --- 4. 绘制标题 ---
        title_text = "约会报告"
        w, _ = utils.get_text_dimensions(title_text, title_font)
        utils.text_with_outline(draw, ((WIDTH - w) / 2, 35), title_text, title_font, (255, 215, 0), (0, 0, 0))

        # --- 5. 绘制约会时间 ---
        date_time = date_results.get("date_time", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        date_text = f"约会时间: {date_time}"
        w, _ = utils.get_text_dimensions(date_text, subtitle_font)
        draw.text(((WIDTH - w) / 2, 110), date_text, font=subtitle_font, fill=(220, 220, 220))

        # --- 6. 绘制用户头像和结果 ---
        # 获取头像
        avatar_size = 150
        avatar_a = await utils.download_image(user_a_avatar)
        if avatar_a is None:
            avatar_a = utils.get_default_avatar()

        avatar_a = avatar_a.resize((avatar_size, avatar_size), Image.LANCZOS)
        avatar_a = utils.crop_to_circle(avatar_a)

        avatar_b = await utils.download_image(user_b_avatar)
        if avatar_b is None:
            avatar_b = utils.get_default_avatar()

        avatar_b = avatar_b.resize((avatar_size, avatar_size), Image.LANCZOS)
        avatar_b = utils.crop_to_circle(avatar_b)

        # 绘制A头像和结果
        avatar_a_x = WIDTH // 4
        avatar_a_y = 180
        card.paste(avatar_a, (avatar_a_x - avatar_size // 2, avatar_a_y), avatar_a)

        # 绘制A的姓名
        w, _ = utils.get_text_dimensions(user_a_name, normal_font)
        draw.text((avatar_a_x - w // 2, avatar_a_y + avatar_size + 10), user_a_name,
                  font=normal_font, fill=(255, 255, 255))

        # 绘制A的好感度变化
        a_change = date_results["user_a"]["favorability_change"]
        a_before = date_results["user_a"]["favorability_before"]
        a_after = date_results["user_a"]["favorability_after"]

        if a_change > 0:
            a_change_color = (50, 255, 50)  # 绿色
            a_change_text = f"+{a_change}"
        elif a_change < 0:
            a_change_color = (255, 50, 50)  # 红色
            a_change_text = f"{a_change}"
        else:
            a_change_color = (220, 220, 220)  # 白色
            a_change_text = "±0"

        draw.text((avatar_a_x - 50, avatar_a_y + avatar_size + 50), f"好感度: {a_before} → {a_after}",
                  font=small_font, fill=(220, 220, 220))
        draw.text((avatar_a_x + 60, avatar_a_y + avatar_size + 50), a_change_text,
                  font=small_font, fill=a_change_color)

        # 绘制A的关系等级变化
        if date_results["user_a"]["level_up"]:
            level_before = date_results["user_a"]["level_before"]
            level_after = date_results["user_a"]["level_after"]
            draw.text((avatar_a_x - 70, avatar_a_y + avatar_size + 80), f"关系: {level_before} → {level_after}",
                      font=small_font, fill=(255, 215, 0))

        # 绘制B头像和结果
        avatar_b_x = WIDTH * 3 // 4
        avatar_b_y = 180
        card.paste(avatar_b, (avatar_b_x - avatar_size // 2, avatar_b_y), avatar_b)

        # 绘制B的姓名
        w, _ = utils.get_text_dimensions(user_b_name, normal_font)
        draw.text((avatar_b_x - w // 2, avatar_b_y + avatar_size + 10), user_b_name,
                 font=normal_font, fill=(255, 255, 255))

        # 绘制B的好感度变化
        b_change = date_results["user_b"]["favorability_change"]
        b_before = date_results["user_b"]["favorability_before"]
        b_after = date_results["user_b"]["favorability_after"]

        if b_change > 0:
            b_change_color = (50, 255, 50)  # 绿色
            b_change_text = f"+{b_change}"
        elif b_change < 0:
            b_change_color = (255, 50, 50)  # 红色
            b_change_text = f"{b_change}"
        else:
            b_change_color = (220, 220, 220)  # 白色
            b_change_text = "±0"

        draw.text((avatar_b_x - 50, avatar_b_y + avatar_size + 50), f"好感度: {b_before} → {b_after}",
                 font=small_font, fill=(220, 220, 220))
        draw.text((avatar_b_x + 60, avatar_b_y + avatar_size + 50), b_change_text,
                 font=small_font, fill=b_change_color)

        # 绘制B的关系等级变化
        if date_results["user_b"]["level_up"]:
            level_before = date_results["user_b"]["level_before"]
            level_after = date_results["user_b"]["level_after"]
            draw.text((avatar_b_x - 70, avatar_b_y + avatar_size + 80), f"关系: {level_before} → {level_after}",
                     font=small_font, fill=(255, 215, 0))

        # --- 7. 绘制心形连接线 ---
        center_y = 230
        draw.line([(avatar_a_x + 50, center_y), (avatar_b_x - 50, center_y)],
                 fill=(255, 192, 203), width=3)

        # --- 8. 绘制事件列表 ---
        events_title = "约会过程"
        w, _ = utils.get_text_dimensions(events_title, subtitle_font)
        draw.text(((WIDTH - w) / 2, 370), events_title, font=subtitle_font, fill=(255, 255, 255))

        # 绘制事件
        events = date_results.get("events", [])
        max_events = min(len(events), 5)  # 最多显示5个事件

        for i in range(max_events):
            event = events[i]
            y_pos = 420 + i * 50

            # 事件名称和描述
            event_name = event.get("name", "未知事件")
            event_desc = event.get("description", "")

            event_text = f"{i + 1}. {event_name}: {event_desc}"

            # 如果文字太长，进行截断
            if len(event_text) > 70:
                event_text = event_text[:67] + "..."

            draw.text((50, y_pos), event_text, font=event_font, fill=(220, 220, 220))

            # 显示事件效果
            a_change = event.get("a_to_b_change", 0)
            b_change = event.get("b_to_a_change", 0)

            if a_change > 0 or b_change > 0:
                effect_color = (50, 255, 50)  # 绿色
            elif a_change < 0 or b_change < 0:
                effect_color = (255, 50, 50)  # 红色
            else:
                effect_color = (220, 220, 220)  # 白色

            effect_text = f"{user_a_name}: {a_change:+d}  {user_b_name}: {b_change:+d}"
            w, _ = utils.get_text_dimensions(effect_text, small_font)
            draw.text((WIDTH - 50 - w, y_pos), effect_text, font=small_font, fill=effect_color)

        # --- 9. 添加时间戳 ---
        timestamp_text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        timestamp_font = utils.get_font(22)
        draw.text((WIDTH - 20, HEIGHT - 20), timestamp_text, font=timestamp_font, fill=(180, 180, 180), anchor="rs")

        # --- 10. 保存图片 ---
        output_dir = os.path.join(utils.BASE_DIR, "data/date_reports")
        os.makedirs(output_dir, exist_ok=True)
        file_name = f"date_{user_a_id}_{user_b_id}_{int(datetime.now().timestamp())}.png"
        output_path = os.path.join(output_dir, file_name)

        card.convert("RGB").save(output_path, "PNG", quality=95)
        return output_path

    except Exception as e:
        logger.error(f"生成约会报告卡片失败: {e}", exc_info=True)
        return None


async def generate_social_network_card(
    user_id: str,
    user_name: str,
    avatar_url: str,
    network_data: List[Dict[str, Any]],
    user_title: Optional[str] = None
) -> Optional[str]:
    """
    生成关系网络卡片
   
    Args:
        user_id: 用户ID
        user_name: 用户名称
        avatar_url: 用户头像URL
        network_data: 关系网络数据
        user_title: 用户称号
       
    Returns:
        生成的图片路径，失败则返回None
    """
    try:
        # --- 1. 布局和样式常量 ---
        WIDTH, HEIGHT = 1280, 720

        # --- 2. 初始化画布 ---
        card, draw = utils.create_base_card(WIDTH, HEIGHT, add_decorations=True)
        if card is None:
            return None

        # --- 3. 加载字体 ---
        title_font = utils.get_font(60)
        subtitle_font = utils.get_font(40)
        normal_font = utils.get_font(32)
        small_font = utils.get_font(24)

        # --- 4. 绘制标题 ---
        title_text = "我的关系网"
        w, _ = utils.get_text_dimensions(title_text, title_font)
        utils.text_with_outline(draw, ((WIDTH - w) / 2, 35), title_text, title_font, (255, 215, 0), (0, 0, 0))

        # --- 5. 绘制用户信息 ---
        # 绘制左侧的用户基本信息
        await utils.draw_user_profile(card, draw, avatar_url, user_name, user_title)

        # --- 6. 绘制关系网络 ---
        network_title = "好感度排行"
        w, _ = utils.get_text_dimensions(network_title, subtitle_font)
        draw.text((WIDTH // 2 + (WIDTH // 4 - w // 2), 150), network_title, font=subtitle_font, fill=(255, 255, 255))

        # 绘制分隔线
        draw.line([(WIDTH // 2, 100), (WIDTH // 2, HEIGHT - 100)], fill=(150, 150, 150), width=2)

        # 如果没有关系数据
        if not network_data:
            empty_text = "暂无关系数据"
            w, _ = utils.get_text_dimensions(empty_text, normal_font)
            draw.text((WIDTH // 2 + (WIDTH // 4 - w // 2), 300), empty_text, font=normal_font, fill=(200, 200, 200))
        else:
            # 绘制关系列表
            for i, relation in enumerate(network_data):
                if i >= 5:  # 最多显示5个关系
                    break

                y_pos = 220 + i * 90

                # 获取关系数据
                target_id = relation.get("user_id", "")
                target_name = relation.get("name", f"用户{target_id}")
                favorability = relation.get("favorability", 0)
                level = relation.get("level", "陌生人")
                special_relation = relation.get("special_relation")

                # 绘制排名
                rank_text = f"{i + 1}."
                draw.text((WIDTH // 2 + 50, y_pos), rank_text, font=normal_font, fill=(255, 255, 255))

                # 绘制目标用户名
                draw.text((WIDTH // 2 + 100, y_pos), target_name, font=normal_font, fill=(255, 255, 255))

                # 绘制好感度和关系等级
                fav_text = f"好感度: {favorability}"
                draw.text((WIDTH // 2 + 100, y_pos + 40), fav_text, font=small_font, fill=(220, 220, 220))

                level_text = f"关系: {level}"
                draw.text((WIDTH // 2 + 280, y_pos + 40), level_text, font=small_font, fill=(220, 220, 220))

                # 如果有特殊关系，显示出来
                if special_relation:
                    special_text = f"♥ {special_relation} ♥"
                    w, _ = utils.get_text_dimensions(special_text, small_font)
                    draw.text((WIDTH - 50 - w, y_pos + 20), special_text, font=small_font, fill=(255, 105, 180))

        # --- 7. 添加时间戳 ---
        timestamp_text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        timestamp_font = utils.get_font(22)
        draw.text((WIDTH - 20, HEIGHT - 20), timestamp_text, font=timestamp_font, fill=(180, 180, 180), anchor="rs")

        # --- 8. 保存图片 ---
        output_dir = os.path.join(utils.BASE_DIR, "data/social_network")
        os.makedirs(output_dir, exist_ok=True)
        file_name = f"network_{user_id}_{int(datetime.now().timestamp())}.png"
        output_path = os.path.join(output_dir, file_name)

        card.convert("RGB").save(output_path, "PNG", quality=95)
        return output_path

    except Exception as e:
        logger.error(f"生成关系网络卡片失败: {e}", exc_info=True)
        return None
