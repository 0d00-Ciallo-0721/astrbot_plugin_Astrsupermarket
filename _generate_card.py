# feifeisupermarket/_generate_card.py

import os
import base64
import random
from datetime import datetime
from io import BytesIO
from typing import Optional

import aiohttp
from PIL import Image, ImageDraw

from astrbot.api import logger
from astrbot.api.star import Star

# 导入全新的绘图工具箱，Pillow绘图将通过它进行
from . import drawing_utils as utils

# HTML模板，使用Jinja2语法
SIGN_CARD_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        @font-face {
            font-family: 'CustomFont';
            src: url(data:font/truetype;base64,{{ font_base64 }});
        }
        body, html {
            margin: 0; 
            padding: 0; 
            font-family: 'CustomFont', sans-serif;
            width: 100%; 
            height: 100%; 
            overflow: hidden;
        }
        .card-container {
            position: relative; 
            width: 100vw; 
            height: 100vh; 
            overflow: hidden;
            background-image: url('data:image/jpeg;base64,{{ bg_base64 }}');
            background-size: cover; 
            background-position: center;
        }
        .overlay {
            position: absolute; 
            top: 0; 
            left: 0; 
            width: 100%; 
            height: 100%;
            background: rgba(0, 0, 0, 0.7);
            z-index: 1;
        }
        .decoration {
            position: absolute; 
            pointer-events: none;
            z-index: 2;
        }
        .card-content {
            position: relative;
            width: 100%; 
            height: 100%; 
            display: flex; 
            align-items: center;
            padding: 5%; 
            box-sizing: border-box; 
            color: white;
            z-index: 3;
        }
        
        .catch01 {
            top: 40px; 
            left: 40px; 
            width: 150px; 
            height: auto;
        }
        .catch02 {
            bottom: 0; 
            right: 20px; 
            width: 300px; 
            height: auto;
        }
        .catch03 {
            bottom: 40px;
            left: 40px;
            width: 220px;
            height: auto;
            opacity: 0.85;
        }

        .left-section {
            flex: 1;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 3vh;
            padding-right: 3%;
        }
        .right-section {
            flex: 2;
            display: flex;
            flex-direction: column;
            justify-content: center;
            gap: 3vh;
        }
        .avatar-container {
            width: 25vh;
            height: 25vh;
            position: relative;
        }
        .avatar {
            width: 100%;
            height: 100%;
            border-radius: 50%;
            object-fit: cover;
            border: 0.8vh solid rgba(255, 255, 255, 0.8);
            box-shadow: 0 0 3vh rgba(0, 0, 0, 0.5);
        }
        .user-name {
            font-size: 5vh;
            font-weight: bold;
            text-shadow: 0.3vh 0.3vh 0.6vh rgba(0, 0, 0, 0.7);
            margin-top: 2vh;
        }
        .user-title {
            font-size: 3.2vh;
            font-weight: bold;
            color: #00E5FF;
            margin-top: 1.5vh;
            text-shadow: 0 0 1vh #00E5FF, 0 0 1.5vh #FFFFFF;
        }
        .title {
            font-size: 7vh;
            font-weight: bold;
            margin-bottom: 3vh;
            text-shadow: 0.5vh 0.5vh 0.8vh rgba(0, 0, 0, 0.7);
            color: #FFD700;
        }
        .info-row {
            display: flex;
            align-items: center;
            gap: 2vh;
            font-size: 3.5vh;
            margin-bottom: 1vh;
        }
        .label {
            color: #E0E0E0;
            min-width: 18vh;
            font-weight: 600;
            text-shadow: 0.2vh 0.2vh 0.3vh rgba(0, 0, 0, 0.8);
        }
        .value {
            font-weight: bold;
            font-size: 4.2vh;
            color: #FFFFFF;
            text-shadow: 0.2vh 0.2vh 0.4vh rgba(0, 0, 0, 0.8);
        }
        .highlight {
            color: #FFD700;
            font-weight: bold;
            font-size: 4.5vh;
            text-shadow: 0.3vh 0.3vh 0.5vh rgba(0, 0, 0, 0.9);
        }
        .timestamp {
            position: absolute;
            bottom: 3vh;
            right: 4vh;
            font-size: 2.2vh;
            color: rgba(255, 255, 255, 0.7);
        }
        .streak-badge {
            position: absolute;
            top: -2vh;
            right: -2vh;
            background: linear-gradient(135deg, #FF6B6B, #FF8E53);
            border-radius: 50%;
            width: 8vh;
            height: 8vh;
            display: flex;
            justify-content: center;
            align-items: center;
            font-size: 3vh;
            font-weight: bold;
            box-shadow: 0 0.5vh 1.5vh rgba(0, 0, 0, 0.3);
            border: 0.3vh solid white;
        }
    </style>
</head>
<body>
    <div class="card-container">
        <div class="overlay"></div>
        
        {% if catch01_base64 %}
        <img class="decoration catch01" src="data:image/png;base64,{{ catch01_base64 }}" alt="Decoration 1">
        {% endif %}
        
        {% if catch02_base64 %}
        <img class="decoration catch02" src="data:image/png;base64,{{ catch02_base64 }}" alt="Decoration 2">
        {% endif %}
        
        {% if catch03_base64 %}
        <img class="decoration catch03" src="data:image/png;base64,{{ catch03_base64 }}" alt="Decoration 3">
        {% endif %}
        
        <div class="card-content">
            <div class="left-section">
                <div class="avatar-container">
                    <img class="avatar" src="data:image/jpeg;base64,{{ avatar_base64 }}" alt="User Avatar">
                    {% if is_streak %}
                    <div class="streak-badge">{{ streak_days }}天</div>
                    {% endif %}
                </div>
                <div class="user-name">{{ user_name }}</div>
                {% if title %}
                <div class="user-title">「{{ title }}」</div>
                {% endif %}
            </div>
            
            <div class="right-section">
                <div class="title">
                    {% if is_resign %}
                    ✅ 补签成功
                    {% else %}
                    ✅ 今日签到成功
                    {% endif %}
                </div>
                
                <div class="info-row">
                    <span class="label">签到时间:</span>
                    <span class="value">{{ sign_time }}</span>
                </div>
                
                <div class="info-row">
                    <span class="label">累计签到:</span>
                    <span class="value">{{ total_days }}天</span>
                </div>
                
                <div class="info-row">
                    <span class="label">连续签到:</span>
                    <span class="value">{{ streak_days }}天</span>
                </div>
                
                <div class="info-row">
                    <span class="label">今日奖励:</span>
                    <span class="value highlight">+{{ daily_reward }} Astr币</span>
                </div>
                
                {% if streak_bonus > 0 %}
                <div class="info-row">
                    <span class="label">连续签到奖励:</span>
                    <span class="value highlight">+{{ streak_bonus }} Astr币</span>
                </div>
                {% endif %}
                
                <div class="info-row">
                    <span class="label">当前Astr币:</span>
                    <span class="value highlight">{{ total_points }}</span>
                </div>
            </div>
            
            <div class="timestamp">{{ timestamp }}</div>
        </div>
    </div>
</body>
</html>
'''

async def get_file_as_base64(file_path: str, optimize=False) -> Optional[str]:
    """读取文件并转换为base64编码，可选择优化图片 (HTML渲染器专用)"""
    try:
        if optimize and file_path.lower().endswith(('.jpg', '.jpeg', '.png')):
            img = Image.open(file_path)

            # 针对装饰图片的特殊处理 (通常是PNG，保持原样)
            if "catch" in file_path.lower() and file_path.lower().endswith('.png'):
                output = BytesIO()
                img.save(output, format='PNG', optimize=True)
                return base64.b64encode(output.getvalue()).decode('utf-8')
            
            # 普通图片处理 (如背景图)
            max_size = (1200, 800)
            if img.width > max_size[0] or img.height > max_size[1]:
                img.thumbnail(max_size, Image.LANCZOS)
                
            output = BytesIO()
            
            # --- 核心修改 ---
            # 在保存为JPEG前，将图片转换为RGB模式
            if img.mode == 'RGBA':
                img = img.convert('RGB')
            # -----------------

            img.save(output, format='JPEG', quality=80, optimize=True)
            return base64.b64encode(output.getvalue()).decode('utf-8')
        else:
            # 非优化路径，直接读取
            with open(file_path, "rb") as file:
                return base64.b64encode(file.read()).decode('utf-8')
    except Exception as e:
        logger.error(f"读取文件失败: {file_path}, 错误: {str(e)}")
        return None


async def get_avatar(user_id: str) -> Optional[bytes]:
    """异步获取QQ用户头像 (HTML渲染器专用)"""
    avatar_url = f"https://q4.qlogo.cn/headimg_dl?dst_uin={user_id}&spec=640"
    try:
        async with aiohttp.ClientSession() as client:
            response = await client.get(avatar_url, timeout=10)
            response.raise_for_status()
            avatar_data = await response.read()
            
            img = Image.open(BytesIO(avatar_data))
            img.thumbnail((200, 200), Image.LANCZOS)
            output = BytesIO()
            img.save(output, format='JPEG', quality=85)
            return output.getvalue()
    except Exception as e:
        logger.error(f"下载头像失败: {e}")
        return None


async def generate_sign_card(
    star_instance: Star,
    user_id: str,
    user_name: str,
    avatar_url: str,
    total_days: int,
    streak_days: int,
    daily_reward: int,
    streak_bonus: int,
    total_points: int,
    sign_time: str,
    is_resign: bool = False,
    title: Optional[str] = None
) -> str:
    """生成签到卡片 (HTML优先)"""
    try:
        # 此处省略了原有的HTML渲染准备逻辑...
        # 我会为您补全这部分。
        font_path = os.path.join(os.path.dirname(__file__), "可爱字体.ttf")
        bg_dir = os.path.join(os.path.dirname(__file__), "backgrounds")
        dec_dir = os.path.join(os.path.dirname(__file__), "dec")

        bg_files = [f for f in os.listdir(bg_dir) if os.path.isfile(os.path.join(bg_dir, f))]
        random_bg_path = os.path.join(bg_dir, random.choice(bg_files))

        bg_base64 = await get_file_as_base64(random_bg_path, optimize=True)
        font_base64 = await get_file_as_base64(font_path)
        avatar_data = await get_avatar(user_id)
        avatar_base64 = base64.b64encode(avatar_data).decode('utf-8') if avatar_data else ""

        if not avatar_base64:
            resource_dir = os.path.join(os.path.dirname(__file__), "resource")
            default_avatar_path = os.path.join(resource_dir, random.choice(os.listdir(resource_dir)))
            avatar_base64 = await get_file_as_base64(default_avatar_path, optimize=True)
        
        template_data = {
            "bg_base64": bg_base64,
            "font_base64": font_base64,
            "avatar_base64": avatar_base64,
            "user_name": user_name,
            "total_days": total_days,
            "streak_days": streak_days,
            "daily_reward": daily_reward,
            "streak_bonus": streak_bonus,
            "total_points": f"{total_points:.2f}",
            "sign_time": sign_time,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "is_streak": streak_days > 1,
            "catch01_base64": await get_file_as_base64(os.path.join(dec_dir, "catch01.png"), True),
            "catch02_base64": await get_file_as_base64(os.path.join(dec_dir, "catch02.png"), True),
            "catch03_base64": await get_file_as_base64(os.path.join(dec_dir, "catch03.png"), True),
            "is_resign": is_resign,
            "title": title
        }
        
        render_options = {"width": 1280, "height": 720, "deviceScaleFactor": 1.5, "quality": 85, "omitBackground": True, "fullPage": True}
        
        return await star_instance.html_render(SIGN_CARD_TEMPLATE, template_data, render_options)
    except Exception as e:
        logger.error(f"渲染HTML签到卡片失败: {e}", exc_info=True)
        return ""


# ===================================================================
# ==             Pillow 绘图部分 (作为备用方案)                      ==
# ===================================================================

async def generate_sign_card_pillow(
    user_id: str,
    user_name: str,
    avatar_url: str,
    total_days: int,
    streak_days: int,
    daily_reward: int,
    streak_bonus: int,
    total_points: int,
    sign_time: str,
    is_resign: bool = False,
    title: Optional[str] = None
) -> Optional[str]:
    """
    使用Pillow和重构后的工具函数生成签到卡片。
    此函数仅在HTML渲染失败时作为备用。
    """
    try:
        # --- 1. 布局和样式常量 ---
        WIDTH, HEIGHT = 1280, 720
        TITLE_COLOR = (255, 215, 0)
        LABEL_COLOR = (224, 224, 224)
        VALUE_COLOR = (255, 255, 255)
        HIGHLIGHT_COLOR = (255, 215, 0)
        TIMESTAMP_COLOR = (180, 180, 180)

        # --- 2. 初始化画布和通用元素 ---
        # 使用工具函数创建带装饰的基础卡片
        card, draw = utils.create_base_card(WIDTH, HEIGHT, add_decorations=True)
        if card is None:
            return None
        
        # 使用工具函数绘制整个左侧的用户信息区域（头像、昵称、称号）
        await utils.draw_user_profile(card, draw, avatar_url, user_name, title)

        # --- 3. 绘制连续签到徽章 (签到卡片特有) ---
        if streak_days > 1:
            badge_size = 80
            badge = Image.new("RGBA", (badge_size, badge_size), (0, 0, 0, 0))
            badge_draw = ImageDraw.Draw(badge)
            badge_draw.ellipse((0, 0, badge_size, badge_size), fill=(255, 107, 107))
            badge_draw.ellipse((3, 3, badge_size - 3, badge_size - 3), outline=VALUE_COLOR, width=3)
            
            badge_font = utils.get_font(30)
            text = f"{streak_days}天"
            w, h = utils.get_text_dimensions(text, badge_font)
            badge_draw.text(((badge_size - w) / 2, (badge_size - h) / 2 - 2), text, font=badge_font, fill=VALUE_COLOR)
            
            avatar_base_x = WIDTH // 4 - 200 // 2
            avatar_base_y = HEIGHT // 2 - 200 // 2 - 50
            card.paste(badge, (avatar_base_x + 200 - badge_size // 2, avatar_base_y - badge_size // 2), badge)
        
        # --- 【新增】 3.5. 绘制右侧背景装饰 (catch03) ---
        _, _, catch03 = utils.get_decoration_images()
        if catch03:
            # 创建一个副本以修改透明度，而不影响原始图像
            catch03_transparent = catch03.copy()
            # 获取alpha通道并降低其值（例如，乘以0.3使其变为30%不透明度）
            alpha = catch03_transparent.getchannel('A')
            new_alpha = alpha.point(lambda i: i * 0.3)
            catch03_transparent.putalpha(new_alpha)

            # 调整尺寸并粘贴到右侧文本区域的背景位置
            catch03_resized = catch03_transparent.resize((600, 300), Image.LANCZOS)
            pos_x = WIDTH // 2 + 60
            pos_y = HEIGHT // 3
            card.paste(catch03_resized, (pos_x, pos_y), catch03_resized)

        # --- 4. 绘制右侧信息 ---
        title_font = utils.get_font(70)
        label_font = utils.get_font(35)
        value_font = utils.get_font(42)
        highlight_font = utils.get_font(45)
        
        title_text = "✅ 补签成功" if is_resign else "✅ 今日签到成功"
        w, _ = utils.get_text_dimensions(title_text, title_font)
        draw.text((WIDTH * 0.75 - w / 2, HEIGHT // 4 - 20), title_text, font=title_font, fill=TITLE_COLOR)
        
        info_items = [
            ("签到时间:", sign_time, False),
            ("累计签到:", f"{total_days}天", False),
            ("连续签到:", f"{streak_days}天", False),
            ("今日奖励:", f"+{daily_reward} Astr币", True),
        ]
        if streak_bonus > 0:
            info_items.append(("连续签到奖励:", f"+{streak_bonus} Astr币", True))
        info_items.append(("当前Astr币:", f"{total_points:.2f}", True))

        current_y = HEIGHT // 3 + 40
        for label, value, highlight in info_items:
            draw.text((WIDTH // 2 + 40, current_y), label, font=label_font, fill=LABEL_COLOR)
            
            font_to_use = highlight_font if highlight else value_font
            color_to_use = HIGHLIGHT_COLOR if highlight else VALUE_COLOR
            draw.text((WIDTH // 2 + 250, current_y - 3), value, font=font_to_use, fill=color_to_use)
            
            current_y += 70

        # --- 5. 添加时间戳 ---
        timestamp_text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        draw.text((WIDTH - 20, HEIGHT - 20), timestamp_text, font=utils.get_font(22), fill=TIMESTAMP_COLOR, anchor="rs")
        
        # --- 6. 保存图片 ---
        output_dir = os.path.join(utils.BASE_DIR, "data/sign_cards")
        os.makedirs(output_dir, exist_ok=True)
        file_name = f"sign_card_{user_id}_{int(datetime.now().timestamp())}.png"
        output_path = os.path.join(output_dir, file_name)
        
        card.convert("RGB").save(output_path, "PNG", quality=95)
        return output_path

    except Exception as e:
        logger.error(f"Pillow生成签到卡片失败: {e}", exc_info=True)
        return None