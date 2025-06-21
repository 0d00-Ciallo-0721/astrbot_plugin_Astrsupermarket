import os
import textwrap
from datetime import datetime
from typing import Dict, Optional, Any
from PIL import ImageDraw, Image as PILImage
from astrbot.api import logger

# 导入绘图工具箱
from . import drawing_utils as utils
from .shop_items import SHOP_DATA

# --- 商店卡片生成函数 ---
async def generate_shop_card(category: str, user_points: int, user_avatar_url: str = None) -> Optional[str]:
    """
    生成指定类别的商店卡片。
    """
    try:
        # --- 1. 布局和样式常量 ---
        WIDTH, HEIGHT = 1280, 720
        items_in_category = SHOP_DATA.get(category, {})
        
        # --- 2. 初始化画布 ---
        card, draw = utils.create_base_card(WIDTH, HEIGHT, add_decorations=False)
        if card is None: return None

        # --- 3. 加载字体 ---
        title_font = utils.get_font(60)
        points_font = utils.get_font(28)
        item_name_font = utils.get_font(32)
        item_price_font = utils.get_font(30)
        item_desc_font = utils.get_font(24)
        timestamp_font = utils.get_font(22)

        # --- 4. 获取并绘制头像 ---
        avatar_size = 80
        avatar_padding = 40
        avatar_position = (avatar_padding, avatar_padding)
        
        # 添加头像（圆形）
        try:
            if user_avatar_url:
                avatar_img = await utils.get_avatar_image(user_avatar_url, size=avatar_size)
                if avatar_img:
                    # 创建圆形遮罩
                    mask = PILImage.new('L', (avatar_size, avatar_size), 0)
                    mask_draw = ImageDraw.Draw(mask)
                    mask_draw.ellipse((0, 0, avatar_size, avatar_size), fill=255)
                    
                    # 应用遮罩并粘贴到卡片上
                    card.paste(avatar_img, avatar_position, mask)
        except Exception as e:
            logger.error(f"获取或绘制头像失败: {e}")
        
        # --- 5. 绘制顶部信息 ---
        # 右侧显示Astr币（与标题对齐）
        points_text = f"我的Astr币: {user_points}"
        title_text = f"Astr商店 - {category}"
        w, _ = utils.get_text_dimensions(title_text, title_font)
        title_position = ((WIDTH - w) / 2, 35)
        
        # 将Astr币放在标题右侧
        points_width, _ = utils.get_text_dimensions(points_text, points_font)
        points_position = (title_position[0] + w + 20, title_position[1] + 20)
        draw.text(points_position, points_text, font=points_font, fill=(255, 255, 255))
        
        # 绘制标题
        utils.text_with_outline(draw, title_position, title_text, title_font, (255, 215, 0), (0, 0, 0))

        # --- 6. 绘制商品展示区 ---
        if not items_in_category:
            no_item_text = "该分类下暂无商品"
            w, h = utils.get_text_dimensions(no_item_text, title_font)
            draw.text(((WIDTH - w) / 2, (HEIGHT - h) / 2), no_item_text, font=title_font, fill=(255,255,255))
        else:
            # 设定商品项布局
            cols = 2
            item_box_width, item_box_height = 580, 120
            gap_x, gap_y = 40, 30
            start_x = 50
            start_y = 130

            for i, (item_id, item_data) in enumerate(items_in_category.items()):
                row, col = i // cols, i % cols
                box_x = start_x + col * (item_box_width + gap_x)
                box_y = start_y + row * (item_box_height + gap_y)
                
                # 绘制每个商品的小圆角矩形背景
                draw.rounded_rectangle([(box_x, box_y), (box_x + item_box_width, box_y + item_box_height)], radius=15, fill=(40, 40, 40, 180))
                
                # 绘制商品信息
                text_start_x = box_x + 20
                
                # 第一行：商品名（左）和价格（右）
                draw.text((text_start_x, box_y + 15), item_data['name'], font=item_name_font, fill=(255, 255, 255))
                price_text = f"{item_data['price']} Astr币"
                w, _ = utils.get_text_dimensions(price_text, item_price_font)
                draw.text((box_x + item_box_width - w - 20, box_y + 18), price_text, font=item_price_font, fill=(255, 215, 0))
                
                # 添加物品ID（小字显示在名称下方）
                id_text = f"ID: {item_id}"
                draw.text((text_start_x, box_y + 50), id_text, font=item_desc_font, fill=(150, 150, 150))
                
                # 第二行：商品描述（自动换行）
                wrapped_desc = textwrap.wrap(item_data['description'], width=45)
                for j, line in enumerate(wrapped_desc[:2]): # 最多显示2行
                    draw.text((text_start_x, box_y + 75 + j * 28), line, font=item_desc_font, fill=(200, 200, 200))

        # --- 7. 添加时间戳 ---
        timestamp_text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        draw.text((WIDTH - 20, HEIGHT - 20), timestamp_text, font=timestamp_font, fill=(180, 180, 180), anchor="rs")

        # --- 8. 保存图片 ---
        output_dir = os.path.join(utils.BASE_DIR, "data/shop_cards")
        os.makedirs(output_dir, exist_ok=True)
        file_name = f"shop_{category}_{int(datetime.now().timestamp())}.png"
        output_path = os.path.join(output_dir, file_name)
        card.save(output_path, "PNG")
        return output_path

    except Exception as e:
        logger.error(f"Pillow生成商店卡片失败: {e}", exc_info=True)
        return None

async def generate_backpack_card(user_bag: Dict[str, Dict[str, int]], user_points: int, 
                               stamina: int = 0, max_stamina: int = 100, 
                               user_avatar_url: str = None) -> Optional[str]:
    """
    生成用户的背包卡片，显示所有物品、Astr币和体力值。
    
    Args:
        user_bag: 用户背包数据
        user_points: 用户Astr币
        stamina: 当前体力值
        max_stamina: 最大体力值
        user_avatar_url: 用户头像URL (不再使用)
    """
    try:
        # --- 1. 布局和样式常量 ---
        WIDTH, HEIGHT = 1280, 720
        all_items = []
        
        # 从用户背包中提取所有物品信息（不按类别分组）
        for category, items in user_bag.items():
            for item_id, quantity in items.items():
                if quantity <= 0:
                    continue  # 跳过数量为0的物品
                    
                item_info = SHOP_DATA.get(category, {}).get(item_id)
                if item_info:
                    all_items.append({
                        "id": item_id,
                        "name": item_info["name"],
                        "description": item_info["description"],
                        "category": category,
                        "quantity": quantity
                    })

        # 按物品名称排序
        all_items.sort(key=lambda x: x["name"])

        # --- 2. 初始化画布 ---
        card, draw = utils.create_base_card(WIDTH, HEIGHT, add_decorations=False)
        if card is None: return None
        
        # --- 3. 加载字体 ---
        title_font = utils.get_font(60)
        info_font = utils.get_font(32)
        item_name_font = utils.get_font(32)
        item_quantity_font = utils.get_font(30)
        item_desc_font = utils.get_font(24)
        timestamp_font = utils.get_font(22)

        # --- 4. [移除] 不再绘制头像 ---
        
        # --- 5. 绘制顶部信息 ---
        # 绘制标题
        title_text = "我的背包"
        w, _ = utils.get_text_dimensions(title_text, title_font)
        title_position = ((WIDTH - w) / 2, 35)
        utils.text_with_outline(draw, title_position, title_text, title_font, (255, 215, 0), (0, 0, 0))
        
        # [修改] 左上角显示Astr币
        points_text = f"💰 Astr币: {user_points}"
        draw.text((50, 40), points_text, font=info_font, fill=(255, 215, 0))
        
        # [新增] 右上角显示体力值
        stamina_text = f"⚡ 体力: {stamina}/{max_stamina}"
        stamina_width, _ = utils.get_text_dimensions(stamina_text, info_font)
        draw.text((WIDTH - stamina_width - 50, 40), stamina_text, font=info_font, fill=(64, 224, 208))
        
        # [新增] 绘制体力条
        bar_width = 200
        bar_height = 20
        bar_x = WIDTH - bar_width - 50
        bar_y = 80
        
        # 绘制体力条背景
        draw.rounded_rectangle(
            [(bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height)],
            radius=5,
            fill=(50, 50, 50)
        )
        
        # 绘制体力条填充部分
        fill_width = int(bar_width * (stamina / max_stamina))
        if fill_width > 0:
            # 根据体力百分比变色：低于30%红色，30%-70%黄色，高于70%绿色
            if stamina / max_stamina < 0.3:
                fill_color = (255, 50, 50)  # 红色
            elif stamina / max_stamina < 0.7:
                fill_color = (255, 215, 0)  # 黄色
            else:
                fill_color = (50, 255, 50)  # 绿色
                
            draw.rounded_rectangle(
                [(bar_x, bar_y), (bar_x + fill_width, bar_y + bar_height)],
                radius=5,
                fill=fill_color
            )

        # --- 6. 绘制物品展示区（不显示分类标题）---
        if not all_items:
            no_item_text = "背包空空如也~"
            w, h = utils.get_text_dimensions(no_item_text, title_font)
            draw.text(((WIDTH - w) / 2, (HEIGHT - h) / 2), no_item_text, font=title_font, fill=(255, 255, 255))
        else:
            # 设定物品项布局
            cols = 2
            item_box_width, item_box_height = 580, 120
            gap_x, gap_y = 40, 30
            start_x = 50
            start_y = 130
            
            for i, item in enumerate(all_items):
                row, col = i // cols, i % cols
                box_x = start_x + col * (item_box_width + gap_x)
                box_y = start_y + row * (item_box_height + gap_y)
                
                # 绘制每个物品的小圆角矩形背景
                draw.rounded_rectangle([(box_x, box_y), (box_x + item_box_width, box_y + item_box_height)], radius=15, fill=(40, 40, 40, 180))
                
                # 绘制物品信息
                text_start_x = box_x + 20
                
                # 第一行：物品名（左）和数量（右）
                draw.text((text_start_x, box_y + 15), item["name"], font=item_name_font, fill=(255, 255, 255))
                quantity_text = f"数量: x{item['quantity']}"
                w, _ = utils.get_text_dimensions(quantity_text, item_quantity_font)
                draw.text((box_x + item_box_width - w - 20, box_y + 18), quantity_text, font=item_quantity_font, fill=(255, 215, 0))
                
                # 添加物品ID（小字显示在名称下方）
                id_text = f"ID: {item['id']} | 类别: {item['category']}"
                draw.text((text_start_x, box_y + 50), id_text, font=item_desc_font, fill=(150, 150, 150))
                
                # 第二行：物品描述（自动换行）
                wrapped_desc = textwrap.wrap(item["description"], width=45)
                for j, line in enumerate(wrapped_desc[:2]): # 最多显示2行
                    draw.text((text_start_x, box_y + 75 + j * 28), line, font=item_desc_font, fill=(200, 200, 200))

        # --- 7. 添加时间戳 ---
        timestamp_text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        draw.text((WIDTH - 20, HEIGHT - 20), timestamp_text, font=timestamp_font, fill=(180, 180, 180), anchor="rs")

        # --- 8. 保存图片 ---
        output_dir = os.path.join(utils.BASE_DIR, "data/backpack_cards")
        os.makedirs(output_dir, exist_ok=True)
        file_name = f"backpack_{int(datetime.now().timestamp())}.png"
        output_path = os.path.join(output_dir, file_name)
        card.save(output_path, "PNG")
        return output_path

    except Exception as e:
        logger.error(f"Pillow生成背包卡片失败: {e}", exc_info=True)
        return None
