# feifeisupermarket/shop_manager.py
import os
import yaml
import random  
from typing import Dict, Optional, Tuple, Any, List
from datetime import datetime
from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent

from .shop_items import SHOP_DATA

class ShopManager:
    def __init__(self, data_dir: str):
        """初始化商店管理器"""
        self.data_dir = data_dir
        self.shop_data_file = os.path.join(data_dir, "shop_data.yaml")
        self.shop_data = self._load_shop_data()
        self.items_definition = self._flatten_items_definition()
        
    def _load_shop_data(self) -> dict:
        """加载商店数据"""
        if os.path.exists(self.shop_data_file):
            try:
                with open(self.shop_data_file, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f) or {}
            except Exception as e:
                logger.error(f"加载商店数据失败: {str(e)}")
                return {}
        return {}
    
    def _save_shop_data(self):
        """保存商店数据"""
        try:
            with open(self.shop_data_file, 'w', encoding='utf-8') as f:
                yaml.dump(self.shop_data, f, allow_unicode=True)
        except Exception as e:
            logger.error(f"保存商店数据失败: {str(e)}")
            
    def _flatten_items_definition(self) -> Dict[str, Dict]:
        """将多层级的物品定义展平成单层，方便查询物品信息"""
        result = {}
        for category, items in SHOP_DATA.items():
            for item_id, item_data in items.items():
                result[item_id] = {**item_data, "category": category}
        return result
    
    def _get_group_shop_data(self, group_id: str) -> dict:
        """获取指定群聊的商店数据，如果不存在则创建"""
        if not group_id:
            return self.shop_data.setdefault("private_chat", {})
        return self.shop_data.setdefault(str(group_id), {})
    
    def _get_user_shop_data(self, group_id: str, user_id: str) -> dict:
        """获取指定群聊中用户的商店数据，如果不存在则创建"""
        group_shop_data = self._get_group_shop_data(group_id)
        
        if user_id not in group_shop_data:
            group_shop_data[user_id] = {
                "inventory": {},  # 用户背包，格式: {category: {item_id: quantity}}
                "purchase_history": [],  # 购买历史
                "use_history": []  # 使用历史
            }
        
        # 确保每个分类都存在
        user_inventory = group_shop_data[user_id]["inventory"]
        for category in SHOP_DATA.keys():
            if category not in user_inventory:
                user_inventory[category] = {}
                
        return group_shop_data[user_id]
    
    def get_user_bag(self, group_id: str, user_id: str) -> Dict[str, Dict[str, int]]:
        """获取用户背包内容"""
        user_shop_data = self._get_user_shop_data(group_id, user_id)
        return user_shop_data["inventory"]
    
    async def buy_item(self, event: AstrMessageEvent, user_data: dict, 
                    category: str, item_id: str, quantity: int = 1) -> Tuple[bool, str]:
        """
        处理用户购买物品的逻辑
        """
        # 1. 检查物品是否存在
        if category not in SHOP_DATA or item_id not in SHOP_DATA[category]:
            return False, f"商品不存在，请确认类别和物品ID"
        
         # 2. [修改] 容量检查 - 背包总容量100，单个物品10个
        user_bag = self.get_user_bag(event.get_group_id(), event.get_sender_id())
        current_item_count = user_bag[category].get(item_id, 0)
        if current_item_count + quantity > 10:
            return False, f"购买失败！【{SHOP_DATA[category][item_id]['name']}】最多只能拥有10个。"

        total_items_in_bag = sum(sum(c.values()) for c in user_bag.values())
        if total_items_in_bag + quantity > 100:
            return False, "购买失败！背包满了，最多只能存放100件物品。"
        
        # 3. 获取物品信息和价格
        item_info = SHOP_DATA[category][item_id]
        total_price = item_info["price"] * quantity
        
        # 4. 检查用户Astr币是否足够
        if user_data.get("points", 0) < total_price:
            return False, f"Astr币不足，需要{total_price}Astr币"
        
        # 5. 执行购买
        user_data["points"] -= total_price
        
        # 6. 更新用户背包
        group_id = event.get_group_id()
        user_id = event.get_sender_id()
        user_shop_data = self._get_user_shop_data(group_id, user_id)
        
        # 确保物品分类存在
        if category not in user_shop_data["inventory"]:
            user_shop_data["inventory"][category] = {}
        
        # 增加物品数量
        user_shop_data["inventory"][category][item_id] = user_shop_data["inventory"][category].get(item_id, 0) + quantity
        
        # 7. 记录购买历史
        purchase_record = {
            "item_id": item_id,
            "category": category,
            "quantity": quantity,
            "price": total_price,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        user_shop_data["purchase_history"].append(purchase_record)
        
        # 8. 保存数据
        self._save_shop_data()
        
        return True, f"成功购买 {item_info['name']} x{quantity}，花费 {total_price} Astr币"

    async def use_item(self, event: AstrMessageEvent, user_data: dict, item_id: str) -> Tuple[bool, str]:
        """
        使用物品的逻辑
        
        Args:
            event: 消息事件
            user_data: 用户数据
            item_id: 物品ID
            
        Returns:
            (成功与否, 提示消息)
        """
        # 1. 检查物品是否存在
        if item_id not in self.items_definition:
            return False, "物品不存在，请确认物品ID"
        
        item_info = self.items_definition[item_id]
        category = item_info["category"]
                # 新增: 礼物类物品不能直接使用
        
        if category == "礼物":
            return False, f"【{item_info['name']}】是礼物，请使用 '赠礼 {item_info['name']} @目标用户' 来赠送给他人哦~"
        
        # 2. 检查用户是否拥有该物品
        group_id = event.get_group_id()
        user_id = event.get_sender_id()
        user_shop_data = self._get_user_shop_data(group_id, user_id)
        
        if (category not in user_shop_data["inventory"] or 
            item_id not in user_shop_data["inventory"][category] or
            user_shop_data["inventory"][category][item_id] <= 0):
            return False, f"你的背包中没有 {item_info['name']}"
        
        # 3. 应用物品效果
        effect_msg = "已使用"
        
        # 处理不同类别物品的效果
        if category == "道具":
            effect_buff = item_info.get("effect_buff")
            if effect_buff:
                if "buffs" not in user_data:
                    user_data["buffs"] = {}
                user_data["buffs"][effect_buff] = user_data["buffs"].get(effect_buff, 0) + 1
                effect_msg = f"生效了！下次{self._get_buff_description(effect_buff)}"
        
        # --- [重构] 统一处理食物类物品的体力变化和消息返回 ---
        elif category == "食物":
            # 确保user_data中有stamina和max_stamina字段
            if "stamina" not in user_data:
                user_data["stamina"] = 100
            if "max_stamina" not in user_data:
                user_data["max_stamina"] = 100
            
            old_stamina = user_data["stamina"]
            max_stamina = user_data["max_stamina"]
            
            # 计算体力变化量
            stamina_change = 0
            is_wallace = False # 标记是否为华莱士

            if item_id == "小饼干":
                stamina_change = 20
            elif item_id == "章鱼烧":
                stamina_change = 30
            elif item_id == "肉包":
                stamina_change = 40
            elif item_id == "KFC":
                stamina_change = 100
            elif item_id == "布丁":
                stamina_change = 160
            elif item_id == "拼好饭":
                stamina_change = random.randint(1, 60)
            elif item_id == "方便面":
                stamina_change = random.randint(1, 20)
            elif item_id == "华莱士":
                is_wallace = True
                if random.random() < 0.5:  # 50%概率
                    new_stamina = 0
                else:
                    new_stamina = old_stamina + 50
                stamina_change = new_stamina - old_stamina # 直接计算变化量
            else:
                # 未知食物或默认效果
                stamina_change = 10

            # 统一应用体力变化
            if not is_wallace:
                # 对普通食物，应用变化并确保不超过上限
                user_data["stamina"] = min(old_stamina + stamina_change, max_stamina)
            else:
                # 对华莱士，直接设置体力值（同样要检查上限）
                user_data["stamina"] = min(new_stamina, max_stamina)
            # 计算实际的体力变化值
            actual_change = user_data["stamina"] - old_stamina
            
            # 根据实际变化值构造统一的消息
            if actual_change > 0:
                change_desc = f"增加了 {actual_change}"
            elif actual_change < 0:
                change_desc = f"减少了 {abs(actual_change)}"
            else:
                change_desc = "没有变化"
            
            effect_msg = f"食用后，你的体力{change_desc}点！当前体力：{user_data['stamina']}/{max_stamina}"

        # 4. 减少物品数量
        user_shop_data["inventory"][category][item_id] -= 1
        
        # 5. 记录使用历史
        use_record = {
            "item_id": item_id,
            "category": category,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        user_shop_data["use_history"].append(use_record)
        
        # 6. 保存数据
        self._save_shop_data()
        
        return True, f"✅ {item_info['name']} 使用成功！\n{effect_msg}"


    # 新增方法: 用于社交系统消耗物品
    async def consume_item(self, group_id: str, user_id: str, item_id: str, quantity: int = 1) -> Tuple[bool, str]:
        """
        从用户背包中消耗指定物品（专用于社交系统等外部调用）
        
        Args:
            group_id: 群聊ID
            user_id: 用户ID
            item_id: 物品ID
            quantity: 消耗数量，默认为1
            
        Returns:
            (成功与否, 提示消息)
        """
        # 1. 确认物品是否存在
        if item_id not in self.items_definition:
            return False, f"物品 {item_id} 不存在"
            
        item_info = self.items_definition[item_id]
        category = item_info["category"]
        
        # 2. 检查用户是否拥有足够物品
        user_shop_data = self._get_user_shop_data(group_id, user_id)
        
        if (category not in user_shop_data["inventory"] or 
            item_id not in user_shop_data["inventory"][category] or
            user_shop_data["inventory"][category][item_id] < quantity):
            return False, f"背包中没有足够的 {item_info['name']}"
        
        # 3. 减少物品数量
        user_shop_data["inventory"][category][item_id] -= quantity
        
        # 4. 记录使用历史
        use_record = {
            "item_id": item_id,
            "category": category,
            "quantity": quantity,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "source": "social_system"  # 标记来源于社交系统
        }
        user_shop_data["use_history"].append(use_record)
        
        # 5. 保存数据
        self._save_shop_data()
        
        return True, f"成功消耗 {item_info['name']} x{quantity}"


    def _get_buff_description(self, buff_name: str) -> str:
        """根据buff名称返回用户友好的描述"""
        descriptions = {
            "work_guarantee_success": "打工必定成功",
            "work_no_penalty": "打工失败不扣币",
            "work_reward_boost": "打工奖励提升",
            "lottery_min_3star": "抽奖至少3星",
            "lottery_double_reward": "抽奖奖励翻倍",
            "lottery_best_of_two": "抽奖取最佳结果",
            "adventure_negate_crisis": "冒险危机保护",
            "adventure_rare_boost": "稀有奇遇提升"
        }
        return descriptions.get(buff_name, buff_name)

    def check_and_consume_buff(self, user_data: dict, buff_name: str) -> bool:
        """
        检查用户是否有指定buff，如果有则消耗一次并返回True
        
        Args:
            user_data: 用户数据
            buff_name: buff名称
            
        Returns:
            是否有此buff
        """
        if "buffs" not in user_data:
            return False
            
        buffs = user_data["buffs"]
        if buffs.get(buff_name, 0) > 0:
            buffs[buff_name] -= 1
            return True
                
        return False

    def get_user_status(self, user_data: dict) -> str:
        """
        获取用户当前的状态信息，包括激活的效果
        
        Args:
            user_data: 用户数据
            
        Returns:
            状态文本
        """
        status_text = f"{user_data.get('name', '用户')} 当前激活的效果："
        
        if "buffs" in user_data and user_data["buffs"]:
            for buff_name, count in user_data["buffs"].items():
                if count > 0:
                    buff_desc = self._get_buff_description(buff_name)
                    status_text += f"\n【{buff_desc}】× {count}"
        else:
            status_text += "\n无活跃效果"
            
        return status_text


    
    def list_categories(self) -> List[str]:
        """获取所有商品类别"""
        return list(SHOP_DATA.keys())
    
    def get_category_items(self, category: str) -> Dict[str, Dict]:
        """获取指定类别的所有商品"""
        return SHOP_DATA.get(category, {})
