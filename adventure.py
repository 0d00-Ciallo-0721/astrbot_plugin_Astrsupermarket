# adventure.py

import random
# 确保这里有从 adventure_events 导入的语句
from .adventure_events import ADVENTURE_EVENTS
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional
from astrbot.api import logger


class AdventureManager:
    def __init__(self):
        """初始化冒险管理器"""
        self.events = ADVENTURE_EVENTS
        
    def _select_random_event(self, user_data: dict):
        # 确保user_data存在且包含buffs字段
        if user_data is None:
            user_data = {}
        
        buffs = user_data.get('buffs', {})
        
        # --- 奇遇信标buff处理 ---
        if buffs.get("adventure_rare_boost", 0) > 0:
            logger.info(f"用户 {user_data.get('name', '')} 使用了奇遇信标，提升稀有事件概率。")
            # 减少buff计数
            user_data['buffs']["adventure_rare_boost"] -= 1

            # 临时修改概率分布
            temp_events_prob = {k: v['probability'] for k, v in self.events.items()}

            # 将"无事件"的概率转移到"稀世奇遇"上
            if "无事件" in temp_events_prob and "稀世奇遇" in temp_events_prob:
                transfer_prob = temp_events_prob["无事件"]
                temp_events_prob["无事件"] = 0
                temp_events_prob["稀世奇遇"] += transfer_prob

            event_types = list(temp_events_prob.keys())
            event_probabilities = list(temp_events_prob.values())
        else:
            # 正常概率分布
            event_types = list(self.events.keys())
            event_probabilities = [data["probability"] for data in self.events.values()]

        # 确保概率总和为100
        total_probability = sum(event_probabilities)
        event_probabilities = [p / total_probability * 100 for p in event_probabilities]
        
        # 随机选择事件类型
        chosen_type = random.choices(event_types, weights=event_probabilities, k=1)[0]
        # 特殊处理抉择事件类型
        if chosen_type == "抉择时刻":
            # 从narratives中随机选择一个叙述
            narratives = self.events[chosen_type]["narratives"]
            narrative = random.choice(narratives)
            
            # 模拟一个"抉择"过程
            outcomes = self.events[chosen_type]["outcomes"]
            outcome_types = list(outcomes.keys())
            outcome_probs = [data["probability"] for data in outcomes.values()]
            
            # 确保概率总和为100
            total_outcome_prob = sum(outcome_probs)
            outcome_probs = [p / total_outcome_prob * 100 for p in outcome_probs]
            
            # 随机选择结果
            chosen_outcome = random.choices(outcome_types, weights=outcome_probs, k=1)[0]
            outcome_data = outcomes[chosen_outcome]
            
            # 构建事件数据 - 修复name键缺失问题
            event_data = {
                "id": narrative["id"],
                "name": narrative.get("name", "抉择时刻"),  # 使用get提供默认值
                "description": narrative["description"],
                "result_message": outcome_data["message"],
                "effects": outcome_data["effects"]
            }
            
            return event_data, chosen_type
        
        # 其他事件类型
        else:
            events = self.events[chosen_type]["events"]
            chosen_event = random.choice(events)
            
            # 确保事件数据包含effects键
            if "effects" not in chosen_event:
                chosen_event["effects"] = {}
                
            return chosen_event, chosen_type


    
    async def _apply_event_effects(self, user_data, event_data, shop_manager, event, results, event_type: str):
        """
        应用事件效果到用户数据
        
        Args:
            user_data: 用户数据
            event_data: 事件数据
            shop_manager: 商店管理器
            event: 事件对象
            results: 结果字典
            
        Returns:
            dict: 效果描述
        """
        effects = {}

        buffs = user_data.get('buffs', {})
        if event_type == "危机与挑战" and buffs.get("adventure_negate_crisis", 0) > 0:
            logger.info(f"用户 {user_data.get('name', '')} 的探险家护符生效，抵消了负面事件。")
            buffs["adventure_negate_crisis"] -= 1

            # 在结果中添加一条消息，告知用户
            if "messages" not in results:
                results["messages"] = []
            results["messages"].append("你的【探险家护符】发出了光芒，为你抵挡了一次危机！")

            # 直接返回，不执行任何负面效果
            return effects    
        # 确保event_data包含effects键
        if not event_data or "effects" not in event_data:
            logger.warning(f"事件数据缺少effects字段: {event_data}")
            return effects
        
        # 处理遣返事件
        if "return" in event_data["effects"] and event_data["effects"]["return"]:
            effects["return"] = "冒险被迫中断！"
            return effects
            
        # 处理Astr币变化
        if "points" in event_data["effects"]:
            points_effect = event_data["effects"]["points"]
            
            # 如果是范围，随机选择一个值
            if isinstance(points_effect, tuple) and len(points_effect) == 2:
                points_change = random.randint(points_effect[0], points_effect[1])
            else:
                points_change = points_effect
                
            # 应用Astr币变化
            user_data["points"] = user_data.get("points", 0) + points_change
            
            # 记录效果描述
            if points_change > 0:
                effects["points"] = f"+{points_change} Astr币"
            elif points_change < 0:
                effects["points"] = f"{points_change} Astr币"
        
        # 处理体力变化
        if "stamina" in event_data["effects"]:
            stamina_effect = event_data["effects"]["stamina"]
            
            # 如果是范围，随机选择一个值
            if isinstance(stamina_effect, tuple) and len(stamina_effect) == 2:
                stamina_change = random.randint(stamina_effect[0], stamina_effect[1])
            else:
                stamina_change = stamina_effect
                
            # 应用体力变化（允许负值）
            user_data["stamina"] = user_data.get("stamina", 0) + stamina_change
            
            # 记录效果描述
            if stamina_change > 0:
                effects["stamina"] = f"+{stamina_change} 体力"
            elif stamina_change < 0:
                effects["stamina"] = f"{stamina_change} 体力"
        
        # 处理随机物品
        if "random_item" in event_data["effects"]:
            item_options = event_data["effects"]["random_item"]
            item_ids = []
            item_probs = []
            
            for item in item_options:
                item_ids.append(item["item_id"])
                item_probs.append(item["probability"])
                
            # 确保概率总和为100
            total_item_prob = sum(item_probs)
            item_probs = [p / total_item_prob * 100 for p in item_probs]
            
            # 随机选择一个物品
            item_id = random.choices(item_ids, weights=item_probs, k=1)[0]
            
            # 获取物品描述 - 使用get方法提供默认值
            item_desc = ""
            for item in item_options:
                if item["item_id"] == item_id:
                    # 修改这一行，使用get方法并提供默认值
                    item_desc = item.get("description", f"获得物品：{item_id}")
                    break
                    
            # 添加物品到背包
            await self._add_item_to_bag(event, shop_manager, item_id, results)
            
            # 记录效果描述
            effects["item_id"] = item_id
            effects["item"] = item_desc

        
        # 处理固定物品
        if "item" in event_data["effects"]:
            item_effect = event_data["effects"]["item"]
            
            # 检查item是字典还是直接的物品ID字符串
            if isinstance(item_effect, dict) and "item_id" in item_effect:
                item_id = item_effect["item_id"]
                item_desc = item_effect.get("description", f"获得物品：{item_id}")
            else:
                # 如果直接是字符串ID
                item_id = item_effect
                item_desc = f"获得物品：{item_id}"
            
            # 添加物品到背包
            await self._add_item_to_bag(event, shop_manager, item_id, results)
            
            # 记录效果描述
            effects["item_id"] = item_id
            effects["item"] = item_desc
        
        # 处理随机奖励
        if "random_reward" in event_data["effects"]:
            reward_options = event_data["effects"]["random_reward"]
            chosen_reward = random.choice(reward_options)
            
            if chosen_reward["type"] == "points":
                points_range = chosen_reward["value"]
                points_change = random.randint(points_range[0], points_range[1])
                
                # 应用Astr币变化
                user_data["points"] = user_data.get("points", 0) + points_change
                
                # 记录效果描述
                effects["points"] = f"+{points_change} Astr币"
                
            elif chosen_reward["type"] == "stamina":
                stamina_range = chosen_reward["value"]
                stamina_change = random.randint(stamina_range[0], stamina_range[1])
                
                # 应用体力变化
                user_data["stamina"] = user_data.get("stamina", 0) + stamina_change
                
                # 记录效果描述
                effects["stamina"] = f"+{stamina_change} 体力"
                
            elif chosen_reward["type"] == "item":
                items = chosen_reward.get("items", [])
                
                # 检查items列表是否为空
                if not items:
                    # 空列表处理
                    logger.warning(f"随机奖励中的物品列表为空")
                    effects["item"] = "奖励物品列表为空"
                elif chosen_reward["type"] == "item":
                    items = chosen_reward.get("items", [])
                    
                    # 检查items列表是否为空
                    if not items:
                        # 空列表处理
                        logger.warning("随机奖励中的物品列表为空")
                        effects["item"] = "奖励物品列表为空"
                    else:
                        # 检查items是物品对象列表还是物品ID列表
                        if items and isinstance(items[0], dict):
                            # 随机选择一个物品对象
                            item = random.choice(items)
                            item_id = item["item_id"]
                            item_desc = item.get("description", f"获得物品：{item_id}")
                        else:
                            # 直接从ID列表中选择
                            item_id = random.choice(items)
                            item_desc = f"获得物品：{item_id}"
                        
                        # 添加物品到背包
                        await self._add_item_to_bag(event, shop_manager, item_id, results)
                        
                        # 记录效果描述
                        effects["item_id"] = item_id
                        effects["item"] = item_desc

        
        # 处理随机惩罚
        if "random_penalty" in event_data["effects"]:
            penalty_options = event_data["effects"]["random_penalty"]
            chosen_penalty = random.choice(penalty_options)
            
            if chosen_penalty["type"] == "points":
                points_range = chosen_penalty["value"]
                points_change = random.randint(points_range[0], points_range[1])
                
                # 应用Astr币变化
                user_data["points"] = user_data.get("points", 0) + points_change
                
                # 记录效果描述
                effects["points"] = f"{points_change} Astr币"
                
            elif chosen_penalty["type"] == "stamina":
                stamina_range = chosen_penalty["value"]
                stamina_change = random.randint(stamina_range[0], stamina_range[1])
                
                # 应用体力变化
                user_data["stamina"] = user_data.get("stamina", 0) + stamina_change
                
                # 记录效果描述
                effects["stamina"] = f"{stamina_change} 体力"
        
        # 处理成就
        if "achievement" in event_data["effects"]:
            achievement_name = event_data["effects"]["achievement"]

            # --- 核心修改点 ---
            # 初始化待解锁成就列表
            if "achievements_to_unlock" not in results:
                results["achievements_to_unlock"] = []

            # 将成就ID添加到待解锁列表中
            # 我们需要从 achievements.py 找到名字对应的ID
            from .achievements import ACHIEVEMENTS
            ach_id_to_unlock = None
            for ach_id, ach_data in ACHIEVEMENTS.items():
                if ach_data['name'] == achievement_name:
                    ach_id_to_unlock = ach_id
                    break

            if ach_id_to_unlock and ach_id_to_unlock not in user_data.get("achievements", []):
                results["achievements_to_unlock"].append(ach_id_to_unlock)
                results["new_achievement"] = f"解锁成就：{achievement_name}！" 
        
        # 处理称号
        if "title" in event_data["effects"]:
            title = event_data["effects"]["title"]
            if "titles" not in user_data:
                user_data["titles"] = []
                
            if title not in user_data["titles"]:
                user_data["titles"].append(title)
                effects["title"] = f"获得称号：{title}！"
        
        return effects


        
    async def _add_item_to_bag(self, event, shop_manager, item_id, results):
        """将物品添加到用户背包中，如果超过上限则自动使用"""
        try:
            # 获取物品分类
            item_category = None
            if item_id in shop_manager.items_definition:
                item_category = shop_manager.items_definition[item_id].get("category")
            
            if not item_category:
                logger.warning(f"物品 {item_id} 没有定义分类，无法添加到背包")
                return
                
            # 获取用户数据
            group_id = event.get_group_id()
            user_id = event.get_sender_id()
            
            # 直接从shop_manager获取数据，避免拷贝导致的修改丢失
            group_shop_data = shop_manager._get_group_shop_data(group_id)
            
            # 直接从shop_manager获取原始数据
            if str(user_id) not in group_shop_data:
                group_shop_data[str(user_id)] = {"inventory": {}}
                
            user_data = group_shop_data[str(user_id)]
            if "inventory" not in user_data:
                user_data["inventory"] = {}
                
            user_bag = user_data["inventory"]
            
            # 确保背包中有该分类
            if item_category not in user_bag:
                user_bag[item_category] = {}
                
            # 背包总容量检查
            total_items = 0
            for cat in user_bag.values():
                total_items += sum(cat.values())
                
            if total_items >= 100:
                logger.warning(f"用户 {user_id} 的背包已满(100)，无法添加更多物品")
                if "messages" not in results:
                    results["messages"] = []
                results["messages"].append("你的背包已满，无法获得更多物品！")
                return
            
            # 获取当前物品数量
            current_count = user_bag[item_category].get(item_id, 0)
            
            # 检查是否超过上限(10个)
            if current_count >= 10:
                # 初始化自动使用物品记录
                if "auto_used_items" not in results:
                    results["auto_used_items"] = []
                    
                # 获取用户数据 - 使用依赖注入而非硬编码插件名
                main_plugin = None
                for plugin_name, plugin in event.bot.plugins.items():
                    if hasattr(plugin, "_get_user_in_group"):
                        main_plugin = plugin
                        break
                        
                if main_plugin:
                    user_data = main_plugin._get_user_in_group(group_id, user_id)
                    # 使用物品
                    success, use_message = await shop_manager.use_item(event, user_data, item_id)
                    
                    if success:
                        # 记录自动使用的物品
                        results["auto_used_items"].append({
                            "id": item_id,
                            "name": shop_manager.items_definition[item_id].get("name", item_id),
                            "message": use_message
                        })
                else:
                    logger.error("找不到主插件，无法自动使用物品")
            else:
                # 未超过上限，正常添加物品
                user_bag[item_category][item_id] = current_count + 1
                
                # 记录获得的物品
                item_name = "未知物品"
                if item_id in shop_manager.items_definition:
                    item_name = shop_manager.items_definition[item_id].get("name", item_id)
                    
                if "items_gained" not in results:
                    results["items_gained"] = []
                    
                results["items_gained"].append({
                    "id": item_id,
                    "name": item_name,
                    "category": item_category
                })
                
                # 不需要额外同步，因为我们直接修改了shop_manager中的数据
        except Exception as e:
            logger.error(f"添加物品到背包失败: {e}", exc_info=True)


    
    async def run_adventures(self, event, user_data, shop_manager, times: int):
        """
        执行冒险
        
        Args:
            event: 事件对象
            user_data: 用户数据
            shop_manager: 商店管理器
            times: 冒险次数
                
        Returns:
            dict: 冒险结果
        """
        if user_data.get("stamina", 0) < times * 20:
            return {
                "success": False,
                "message": "体力不足，无法进行冒险。"
            }        
        # 检查参数
        if times <= 0:
            return {
                "success": False,
                "message": "冒险次数必须大于0。"
            }
        
        # 初始化结果
        results = {
            "success": True,
            "adventure_times": 0,
            "start_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "stamina_before": user_data.get("stamina", 0),
            "points_before": user_data.get("points", 0),
            "events": [],
            "items_gained": [],
            "stamina_after": 0,
            "points_after": 0,
            "total_points_gain": 0,
            "stamina_cost": 0,
            "message": "冒险成功完成！"
        }
        
        # 记录原始点数
        original_points = user_data.get("points", 0)
        original_stamina = user_data.get("stamina", 0)
        
        # 增加冒险计数
        if "adventure_count" not in user_data:
            user_data["adventure_count"] = 0
        
        # 执行冒险
        actual_times = 0
        for i in range(times):
            # 增加冒险次数计数
            user_data["adventure_count"] += 1
            actual_times += 1
            
            # 选择并执行事件
            event_data, event_type = self._select_random_event(user_data) 
            
            # 应用事件效果 - 改为await
            effects = await self._apply_event_effects(user_data, event_data, shop_manager, event, results, event_type) 
            
            # 存储事件结果
            if "result_message" in event_data:
                description = f"{event_data['description']} {event_data['result_message']}"
            else:
                description = event_data.get('description', '发生了一个事件')
                
            results["events"].append({
                "id": event_data.get("id", f"event_{i}"),
                "name": event_data.get("name", "未命名事件"),  # 使用get方法提供默认值
                "description": description,
                "effects": effects
            })

            
            # 处理遣返事件
            if "return" in effects:
                results["message"] = "冒险被意外中断！"
                break
        
        # 仅在所有冒险完成后一次性扣除体力
        stamina_cost = actual_times * 20
        user_data["stamina"] -= stamina_cost
        results["stamina_cost"] = stamina_cost
        
        # 更新结果
        results["adventure_times"] = actual_times
        results["stamina_after"] = user_data.get("stamina", 0)
        results["points_after"] = user_data.get("points", 0)
        results["total_points_gain"] = results["points_after"] - original_points
        
        # 保存背包变化
        shop_manager._save_shop_data()
        
        return results
