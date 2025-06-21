# feifeisupermarket/drawing_utils.py

"""
AstrAstr超级市场 - Pillow 绘图工具箱

该文件包含了所有用于生成图片卡片的通用、可复用的函数。
主要功能包括：
- 资源加载（字体、背景图、装饰图、网络图片）
- 图像处理（圆形裁剪）
- 文本绘制（尺寸计算、带轮廓文本）
- 复合组件绘制（基础卡片、用户头像区域）
"""

import os
import random
import aiohttp
from io import BytesIO
from typing import Optional, Tuple
from PIL import Image, ImageDraw, ImageFont

from astrbot.api import logger

# --- 全局常量 ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_PATH = os.path.join(BASE_DIR, "可爱字体.ttf")

# --- 1. 资源加载函数 ---

def get_font(size: int) -> Optional[ImageFont.FreeTypeFont]:
    """
    获取指定大小的字体。
    所有作图函数统一调用此函数以保证字体一致。
    """
    try:
        if not os.path.exists(FONT_PATH):
            logger.error(f"核心字体文件丢失: {FONT_PATH}，尝试使用备用字体。")
            return ImageFont.truetype("arial.ttf", size)
        return ImageFont.truetype(FONT_PATH, size)
    except Exception as e:
        logger.error(f"加载字体 '{FONT_PATH}' 失败: {e}，尝试使用备用字体。")
        try:
            return ImageFont.truetype("arial.ttf", size)
        except IOError:
            logger.error("备用字体 'arial.ttf' 也加载失败。")
            return None

def get_random_background() -> Optional[Image.Image]:
    """
    从 backgrounds 文件夹中随机获取一张背景图片。
    """
    try:
        backgrounds_dir = os.path.join(BASE_DIR, "backgrounds")
        valid_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif']
        
        bg_files = [f for f in os.listdir(backgrounds_dir) 
                   if os.path.isfile(os.path.join(backgrounds_dir, f))
                   and os.path.splitext(f.lower())[1] in valid_extensions]
        
        if not bg_files:
            logger.error(f"背景图片文件夹 '{backgrounds_dir}' 为空或没有有效图片。")
            return None
        
        random_bg_path = os.path.join(backgrounds_dir, random.choice(bg_files))
        return Image.open(random_bg_path).convert("RGBA")
    except Exception as e:
        logger.error(f"获取背景图片失败: {e}")
        return None

def get_decoration_images() -> Tuple[Optional[Image.Image], Optional[Image.Image], Optional[Image.Image]]:
    """
    从 dec 文件夹获取三张固定的装饰图片。
    """
    try:
        dec_dir = os.path.join(BASE_DIR, "dec")
        catch01_path = os.path.join(dec_dir, "catch01.png")
        catch02_path = os.path.join(dec_dir, "catch02.png")
        catch03_path = os.path.join(dec_dir, "catch03.png")
        
        catch01 = Image.open(catch01_path).convert("RGBA") if os.path.exists(catch01_path) else None
        catch02 = Image.open(catch02_path).convert("RGBA") if os.path.exists(catch02_path) else None
        catch03 = Image.open(catch03_path).convert("RGBA") if os.path.exists(catch03_path) else None
        
        return catch01, catch02, catch03
    except Exception as e:
        logger.error(f"获取装饰图片失败: {e}")
        return None, None, None

async def download_image(url: str) -> Optional[Image.Image]:
    """
    从 URL 异步下载图片并返回 PIL Image 对象。
    """
    if not url or not url.startswith("http"):
        return None
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    image_data = await response.read()
                    return Image.open(BytesIO(image_data)).convert("RGBA")
                else:
                    logger.error(f"下载图片失败: {url}, 状态码: {response.status}")
                    return None
    except Exception as e:
        logger.error(f"下载图片 '{url}' 出错: {e}")
        return None

def get_default_avatar() -> Optional[Image.Image]:
    """
    当用户头像获取失败时，提供一张默认头像。
    """
    try:
        resource_dir = os.path.join(BASE_DIR, "resource")
        if os.path.exists(resource_dir):
            avatar_files = [f for f in os.listdir(resource_dir) if os.path.isfile(os.path.join(resource_dir, f))]
            if avatar_files:
                default_avatar_path = os.path.join(resource_dir, random.choice(avatar_files))
                return Image.open(default_avatar_path).convert("RGBA")
    except Exception as e:
         logger.error(f"获取默认头像失败: {e}")

    # 如果上述失败，则动态创建一个灰色圆形作为最终备用方案
    avatar_img = Image.new("RGBA", (200, 200), (0, 0, 0, 0))
    draw = ImageDraw.Draw(avatar_img)
    draw.ellipse((0, 0, 200, 200), fill=(200, 200, 200, 255))
    return avatar_img


# --- 2. 图像处理函数 ---

def crop_to_circle(im: Image.Image) -> Image.Image:
    """
    将一个 PIL Image 对象裁剪为圆形。
    """
    # 放大遮罩以获得更平滑的边缘
    bigsize = (im.size[0] * 3, im.size[1] * 3)
    mask = Image.new('L', bigsize, 0)
    draw = ImageDraw.Draw(mask) 
    draw.ellipse((0, 0) + bigsize, fill=255)
    
    # 缩小遮罩以匹配原图尺寸
    mask = mask.resize(im.size, Image.LANCZOS)
    
    # 将遮罩应用为 alpha 通道
    result = im.copy()
    result.putalpha(mask)
    return result

# --- 3. 文本绘制函数 ---

def get_text_dimensions(text: str, font: ImageFont.FreeTypeFont) -> Tuple[int, int]:
    """
    获取文本在指定字体下的渲染宽度和高度。
    兼容不同版本的Pillow。
    """
    if hasattr(font, 'getbbox'):
        bbox = font.getbbox(text)
        return bbox[2] - bbox[0], bbox[3] - bbox[1]
    elif hasattr(font, 'getsize'):
        return font.getsize(text)
    return 0, 0

def text_with_outline(draw, pos, text, font, text_color, outline_color, outline_width=2):
    """
    在指定位置绘制带有轮廓的文字。
    """
    x, y = pos
    # 绘制8个方向的轮廓以获得更平滑的效果
    for dx in range(-outline_width, outline_width + 1):
        for dy in range(-outline_width, outline_width + 1):
            if dx != 0 or dy != 0:
                draw.text((x + dx, y + dy), text, font=font, fill=outline_color)
    # 最后在顶部绘制原始文本
    draw.text(pos, text, font=font, fill=text_color)


# --- 4. 复合组件绘制函数 ---

def create_base_card(width: int, height: int, add_decorations: bool = False) -> Tuple[Optional[Image.Image], Optional[ImageDraw.Draw]]:
    """
    创建一个包含随机背景、半透明遮罩和可选装饰的基础卡片。
    返回卡片对象和绘图对象。
    """
    bg_img = get_random_background()
    if bg_img is None:
        return None, None
        
    bg_img = bg_img.resize((width, height), Image.LANCZOS)
    
    # 1. 创建主画布并粘贴背景
    card = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    card.paste(bg_img, (0, 0))
    
    # 2. 应用半透明的黑色遮罩层
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 180))
    card = Image.alpha_composite(card, overlay)

    # 3. 【修改】在遮罩层之上，统一绘制所有装饰
    if add_decorations:
        catch01, catch02, catch03 = get_decoration_images()
        
        # 绘制 catch01 (左上角)
        if catch01:
            catch01_resized = catch01.resize((150, 150), Image.LANCZOS)
            card.paste(catch01_resized, (40, 40), catch01_resized)
        
        # 绘制 catch02 (右下角)，并保持宽高比以防拉伸
        if catch02:
            original_w, original_h = catch02.size
            new_w = 300
            new_h = int(new_w * (original_h / original_w))
            
            catch02_resized = catch02.resize((new_w, new_h), Image.LANCZOS)
            pos_x = width - catch02_resized.width - 20
            pos_y = height - catch02_resized.height
            card.paste(catch02_resized, (pos_x, pos_y), catch02_resized)

        # 【修改】绘制 catch03 (左下角)，并缩小尺寸
        if catch03:
            # 轻微透明处理
            catch03_transparent = catch03.copy()
            alpha = catch03_transparent.getchannel('A')
            new_alpha = alpha.point(lambda i: i * 0.85)
            catch03_transparent.putalpha(new_alpha)

            catch03_resized = catch03_transparent.resize((220, 110), Image.LANCZOS)
            pos_x = 40
            pos_y = height - catch03_resized.height - 40
            card.paste(catch03_resized, (pos_x, pos_y), catch03_resized)
            
    # 4. 返回最终的卡片和可供后续绘制的 Draw 对象
    return card, ImageDraw.Draw(card)


async def draw_user_profile(
    card: Image.Image,
    draw: ImageDraw.Draw,
    avatar_url: str,
    user_name: str,
    title: Optional[str]
):
    """
    在卡片的左侧区域绘制用户头像、名称和称号。
    这是一个高度复用的组件，用于签到卡和商城卡。
    """
    WIDTH, HEIGHT = card.size
    
    # 1. 获取用户头像
    avatar_img = await download_image(avatar_url)
    if avatar_img is None:
        avatar_img = get_default_avatar()

    # 2. 处理头像（裁剪、加边框）
    avatar_size = 200
    avatar_img = avatar_img.resize((avatar_size, avatar_size), Image.LANCZOS)
    avatar_img = crop_to_circle(avatar_img)
    
    avatar_canvas = Image.new("RGBA", (avatar_size + 16, avatar_size + 16), (0, 0, 0, 0))
    draw_border = ImageDraw.Draw(avatar_canvas)
    draw_border.ellipse((0, 0, avatar_size + 15, avatar_size + 15), outline=(255, 255, 255, 230), width=8)
    avatar_canvas.paste(avatar_img, (8, 8), avatar_img)

    # 3. 绘制头像
    avatar_x = WIDTH // 4 - avatar_size // 2
    avatar_y = HEIGHT // 2 - avatar_size // 2 - 50
    card.paste(avatar_canvas, (avatar_x - 8, avatar_y - 8), avatar_canvas)
    
    # 4. 绘制用户名和称号
    username_font = get_font(50)
    user_name_width, user_name_height = get_text_dimensions(user_name, username_font)
    draw.text(
        (WIDTH // 4 - user_name_width // 2, avatar_y + avatar_size + 20),
        user_name,
        font=username_font,
        fill=(255, 255, 255, 255)
    )
    
    if title:
        title_font = get_font(32)
        title_text = f"「{title}」"
        title_width, _ = get_text_dimensions(title_text, title_font)
        title_y = avatar_y + avatar_size + 20 + user_name_height + 15
        text_with_outline(draw, (WIDTH // 4 - title_width // 2, title_y), title_text, title_font, (0, 229, 255), (0,0,0))