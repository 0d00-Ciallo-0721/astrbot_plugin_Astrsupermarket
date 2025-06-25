# feifeisupermarket/social.py

import os
import yaml
import random
from datetime import datetime, timedelta 
from typing import Dict, List, Tuple, Any, Optional

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent

from .social_events import DATE_EVENTS, RELATION_LEVELS, SPECIAL_RELATION_TYPES, RELATION_TYPE_NAMES

class SocialManager:
    """社会生活系统管理器"""
    
    def __init__(self, data_dir: str):
        """初始化社会生活管理器"""
        self.data_dir = data_dir
        self.social_data_file = os.path.join(data_dir, "social_data.yaml")
        self.social_data = self._load_data()
        self.active_invitations: Dict[str, Dict[str, Dict]] = {}
        
    def _load_data(self) -> dict:
        """加载社交数据"""
        if os.path.exists(self.social_data_file):
            try:
                with open(self.social_data_file, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f) or {}
            except Exception as e:
                logger.error(f"加载社交数据失败: {str(e)}")
                return {}
        return {}
    
    def cleanup_expired_invitations(self):
        """清理所有过期的约会邀请"""
        now = datetime.now()
        for group_id in list(self.active_invitations.keys()):
            for target_id in list(self.active_invitations[group_id].keys()):
                invitation = self.active_invitations[group_id][target_id]
                if now - invitation['created_at'] > timedelta(seconds=60):
                    self.remove_invitation(group_id, target_id) 

    def _save_data(self):
        """保存社交数据"""
        try:
            with open(self.social_data_file, 'w', encoding='utf-8') as f:
                yaml.dump(self.social_data, f, allow_unicode=True)
        except Exception as e:
            logger.error(f"保存社交数据失败: {str(e)}")
    
    def _get_group_social_data(self, group_id: str) -> dict:
        """获取群组的社交数据，不存在则创建"""
        if not group_id:
            return self.social_data.setdefault("private_chat", {})
        return self.social_data.setdefault(str(group_id), {})
    
    def _get_user_social_data(self, group_id: str, user_id: str) -> dict:
        """获取用户的社交数据，不存在则创建"""
        group_data = self._get_group_social_data(group_id)
        
        if user_id not in group_data:
            # 初始化用户社交数据
            group_data[user_id] = {
                "special_relations": {
                    "lover": None,
                    "brother": None,
                    "patron": None
                },
                "favorability": {},  # 对其他用户的好感度
                "daily_date_count": 0,  # 每日约会次数
                "last_date_date": ""  # 上次约会日期
            }
        
        # 兼容旧数据，确保所有字段都存在
        user_data = group_data[user_id]
        if "special_relations" not in user_data:
            user_data["special_relations"] = {"lover": None, "brother": None, "patron": None}
        if "favorability" not in user_data:
            user_data["favorability"] = {}
        if "daily_date_count" not in user_data:
            user_data["daily_date_count"] = 0
        if "last_date_date" not in user_data:
            user_data["last_date_date"] = ""
            
        return user_data
    
    def _get_relation_level(self, favorability: int) -> str:
        """根据好感度获取关系等级"""
        if favorability <= 19:
            return "陌生人"
        elif favorability <= 49:
            return "熟人"
        elif favorability <= 89:
            return "朋友"
        elif favorability <= 99:
            return "挚友"
        elif favorability == 100:
            return "唯一的你"
        else:
            return "灵魂伴侣"
    
    def get_favorability(self, group_id: str, user_a_id: str, user_b_id: str) -> int:
        """获取用户A对用户B的好感度"""
        user_a_data = self._get_user_social_data(group_id, user_a_id)
        return user_a_data["favorability"].get(user_b_id, 0)
    
    def _update_favorability(self, group_id: str, user_a_id: str, user_b_id: str, change: int) -> int:
        """
        更新好感度
        
        Args:
            group_id: 群组ID
            user_a_id: 用户A的ID
            user_b_id: 用户B的ID
            change: 好感度变化值
            
        Returns:
            更新后的好感度值
        """
        user_a_data = self._get_user_social_data(group_id, user_a_id)
        
        # 初始化好感度字典
        if "favorability" not in user_a_data:
            user_a_data["favorability"] = {}
        
        # 获取当前好感度
        current = user_a_data["favorability"].get(user_b_id, 0)
        
        # 确保好感度不会为负
        new_value = max(0, current + change)
        user_a_data["favorability"][user_b_id] = new_value
        
        return new_value

    
    async def process_gift(self, event, group_id: str, sender_id: str, 
                        target_id: str, item_id: str, favorability_gain: int) -> Tuple[bool, str]:
        """
        处理赠送礼物的好感度增加
        
        Args:
            event: 消息事件
            group_id: 群组ID
            sender_id: 发送者ID
            target_id: 接收者ID
            item_id: 礼物ID
            favorability_gain: 好感度增加值
            
        Returns:
            (成功与否, 消息)
        """
        # 不能给自己送礼
        if sender_id == target_id:
            return False, "不能给自己送礼哦~"
            
        # 获取当前好感度
        old_value = self.get_favorability(group_id, target_id, sender_id)
        
        # 检查是否已达到上限
        if old_value >= 100 and not self.get_special_relation(group_id, sender_id, target_id):
            return False, "对方对你的好感度已达到上限(100)，需要缔结特殊关系才能继续提升。"
        
        # 增加目标对发送者的好感度
        new_value = self._update_favorability(group_id, target_id, sender_id, favorability_gain)
        
        # 获取关系等级
        old_level = self._get_relation_level(old_value)
        new_level = self._get_relation_level(new_value)
        
        # 保存数据
        self._save_data()
        
        return True, f"赠送成功！对方好感度 +{favorability_gain} ({old_value} → {new_value})，当前关系：【{new_level}】"

    def create_invitation(self, group_id: str, initiator_id: str, target_id: str) -> Tuple[bool, str]:
        """创建一个约会邀请，取代 start_date_session"""
        group_id_str = str(group_id)
        if group_id_str not in self.active_invitations:
            self.active_invitations[group_id_str] = {}

        # 检查发起者或目标是否已在进行中的邀请中
        for inv_target_id, inv_data in self.active_invitations[group_id_str].items():
            if inv_data['initiator_id'] == initiator_id:
                return False, "你已经发出了一个约会邀请，请等待其结束。"
            if inv_target_id == target_id:
                return False, "对方正在被其他人邀请，请稍后再试。"

        # 注册一个新的邀请
        self.active_invitations[group_id_str][str(target_id)] = {
            "initiator_id": str(initiator_id),
            "created_at": datetime.now()
        }
        return True, "邀请已创建"

    def get_invitation(self, group_id: str, target_id: str) -> Optional[dict]:
        """获取一个待处理的约会邀请"""
        group_id_str = str(group_id)
        target_id_str = str(target_id)
        
        invitation = self.active_invitations.get(group_id_str, {}).get(target_id_str)
        
        if not invitation:
            return None
            
        # 检查邀请是否超时（60秒）
        if datetime.now() - invitation['created_at'] > timedelta(seconds=60):
            # 如果超时，清理掉
            self.remove_invitation(group_id, target_id)
            return None
            
        return invitation

    def remove_invitation(self, group_id: str, target_id: str):
        """结束/移除一个约会邀请"""
        group_id_str = str(group_id)
        target_id_str = str(target_id)
        
        if group_id_str in self.active_invitations and target_id_str in self.active_invitations[group_id_str]:
            del self.active_invitations[group_id_str][target_id_str]
    
    def check_social_master_achievement(self, group_id: str, user_id: str) -> bool:
        """检查是否满足'社交达人'成就条件：与5名不同用户的好感度在50以上"""
        try:
            user_data = self._get_user_social_data(group_id, user_id)
            favorability_data = user_data.get("favorability", {})
            
            # 计算好感度大于等于50的用户数量
            high_favorability_count = sum(1 for fav in favorability_data.values() if fav >= 50)
            
            return high_favorability_count >= 5
        except Exception as e:
            logger.error(f"检查社交达人成就时出错: {e}", exc_info=True)
            return False

    
    async def initiate_date(self, event: AstrMessageEvent, group_id: str, initiator_id: str, target_id: str) -> Tuple[bool, str]:
        """
        发起约会邀请
        
        Args:
            event: 消息事件
            group_id: 群聊ID
            initiator_id: 发起者ID
            target_id: 目标ID
            
        Returns:
            (成功与否, 消息)
        """
        # 检查是否是自己
        if initiator_id == target_id:
            return False, "不能和自己约会哦~"
        
        # 检查是否是机器人
        if target_id == event.get_self_id():
            return False, "抱歉，我现在很忙，没有时间约会~"
        
        # 检查每日约会次数
        initiator_data = self._get_user_social_data(group_id, initiator_id)
        today = datetime.now().strftime("%Y-%m-%d")
        
        # 如果是新的一天，重置计数
        if initiator_data["last_date_date"] != today:
            initiator_data["daily_date_count"] = 0
            initiator_data["last_date_date"] = today
        
        # 检查是否超过每日限制
        if initiator_data["daily_date_count"] >= 3:
            return False, "你今天已经约会3次了，请明天再来~"
        
        # 创建约会会话
        self.start_date_session(event.unified_msg_origin, group_id, initiator_id, target_id)
        
        # 增加约会计数
        initiator_data["daily_date_count"] += 1
        self._save_data()
        
        return True, f"已向对方发送约会邀请，等待回应..."
    
    async def run_date(self, group_id: str, user_a_id: str, user_b_id: str, user_a_name: str, user_b_name: str) -> dict:
        """
        执行约会流程
        
        Args:
            group_id: 群聊ID
            user_a_id: 用户A的ID
            user_b_id: 用户B的ID
            user_a_name: 用户A的名称
            user_b_name: 用户B的名称
            
        Returns:
            包含约会结果的字典
        """
        # 记录开始时的好感度
        a_to_b_before = self.get_favorability(group_id, user_a_id, user_b_id)
        b_to_a_before = self.get_favorability(group_id, user_b_id, user_a_id)
        
        # 随机选择3-5个事件
        event_count = random.randint(3, 5)
        selected_events = random.sample(DATE_EVENTS, min(event_count, len(DATE_EVENTS)))
        
        # 累计好感度变化
        a_to_b_change = 0
        b_to_a_change = 0
        
        # 处理每个事件
        events_result = []
        for event in selected_events:
            # 从范围中随机选择好感度变化值
            change_min, change_max = event["favorability_change"]
            change_a = random.randint(change_min, change_max)
            change_b = random.randint(change_min, change_max)
            
            # 累加变化值
            a_to_b_change += change_a
            b_to_a_change += change_b
            
            # 记录事件结果
            events_result.append({
                "id": event["id"],
                "name": event["name"],
                "description": event["description"],
                "a_to_b_change": change_a,
                "b_to_a_change": change_b
            })
        
        # 更新好感度
        a_to_b_after = self._update_favorability(group_id, user_a_id, user_b_id, a_to_b_change)
        b_to_a_after = self._update_favorability(group_id, user_b_id, user_a_id, b_to_a_change)
        
        # 保存数据
        self._save_data()
        
        # 检查关系变化
        a_to_b_level_before = self._get_relation_level(a_to_b_before)
        a_to_b_level_after = self._get_relation_level(a_to_b_after)
        b_to_a_level_before = self._get_relation_level(b_to_a_before)
        b_to_a_level_after = self._get_relation_level(b_to_a_after)
        
        # 组织返回结果
        result = {
            "success": True,
            "date_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "user_a": {
                "id": user_a_id,
                "name": user_a_name,
                "favorability_before": a_to_b_before,
                "favorability_after": a_to_b_after,
                "favorability_change": a_to_b_change,
                "level_before": a_to_b_level_before,
                "level_after": a_to_b_level_after,
                "level_up": a_to_b_level_before != a_to_b_level_after
            },
            "user_b": {
                "id": user_b_id,
                "name": user_b_name,
                "favorability_before": b_to_a_before,
                "favorability_after": b_to_a_after,
                "favorability_change": b_to_a_change,
                "level_before": b_to_a_level_before,
                "level_after": b_to_a_level_after,
                "level_up": b_to_a_level_before != b_to_a_level_after
            },
            "events": events_result,
            # 添加成就检查标志
            "check_achievements": {
                "date_beginner": {
                    "user_a_id": user_a_id,
                    "user_b_id": user_b_id
                }
            }
        }
        
        return result
    def get_special_relation(self, group_id: str, user_id: str, target_id: str) -> Optional[str]:
        """
        获取两个用户之间的特殊关系
        
        Args:
            group_id: 群聊ID
            user_id: 用户ID
            target_id: 目标用户ID
            
        Returns:
            关系类型名称，若无则返回None
        """
        user_data = self._get_user_social_data(group_id, user_id)
        
        # 遍历用户的特殊关系
        for relation_type, related_id in user_data["special_relations"].items():
            if related_id == target_id:
                return RELATION_TYPE_NAMES.get(relation_type, relation_type)
                
        return None
    
    async def form_relationship(self, group_id: str, user_id: str, target_id: str, 
                        relation_type: str) -> Tuple[bool, str, Optional[str]]:
        """
        缔结特殊关系
        """
        # 检查关系类型是否有效
        if relation_type not in ["lover", "brother", "patron"]:
            return False, f"无效的关系类型: {relation_type}", None  # 增加第三个返回值 None

        # 不能与自己缔结关系
        if user_id == target_id:
            return False, "不能与自己缔结特殊关系哦~", None  # 增加第三个返回值 None

        # 获取好感度
        user_to_target = self.get_favorability(group_id, user_id, target_id)
        
        # 对于包养关系，只需要对方好感度足够
        if relation_type == "patron":
            target_to_user = self.get_favorability(group_id, target_id, user_id)
            if target_to_user < 100:
                return False, f"对方对你的好感度不足，需要达到100点才能被包养。当前好感度: {target_to_user}", None  # 增加第三个返回值 None
        else:  # 恋人和兄弟关系需要双向好感度
            if user_to_target < 100:
                return False, f"你对对方的好感度不足，需要达到100点。当前好感度: {user_to_target}", None  # 增加第三个返回值 None
            target_to_user = self.get_favorability(group_id, target_id, user_id)
            if target_to_user < 100:
                return False, f"对方对你的好感度不足，需要达到100点。当前好感度: {target_to_user}", None  # 增加第三个返回值 None

        # 获取用户数据
        user_data = self._get_user_social_data(group_id, user_id)
        target_data = self._get_user_social_data(group_id, target_id)
        relation_name = RELATION_TYPE_NAMES.get(relation_type, relation_type)

        # 检查该类型关系是否已被占用
        if user_data["special_relations"][relation_type] is not None:
            return False, f"你已经有一个'{relation_name}'关系了，请先解除现有关系。", None  # 增加第三个返回值 None
            
        if target_data["special_relations"][relation_type] is not None:
            return False, f"对方已经有一个'{relation_name}'关系了，无法与你缔结。", None  # 增加第三个返回值 None
        
        # 检查两人之间是否已经有其他类型的特殊关系
        existing_relation = self.get_special_relation(group_id, user_id, target_id)
        if existing_relation:
            return False, f"你们之间已经有'{existing_relation}'关系了，不能再缔结其他特殊关系。", None  # 增加第三个返回值 None
        
        # --- 成功路径 ---
        # 缔结关系
        user_data["special_relations"][relation_type] = target_id
        target_data["special_relations"][relation_type] = user_id
        
        # 解锁好感度上限
        if self.get_favorability(group_id, user_id, target_id) == 100:
            self._update_favorability(group_id, user_id, target_id, 1)
        if self.get_favorability(group_id, target_id, user_id) == 100:
            self._update_favorability(group_id, target_id, user_id, 1)
            
        # 保存数据
        self._save_data()
        
        # 如果是包养关系，添加成就检查标志
        check_achievement = None
        if relation_type == "patron":
            check_achievement = "social_patron"
        
        # 成功时返回3个值
        return True, f"恭喜！你与对方成功缔结'{relation_name}'关系！", check_achievement


    async def break_relationship(self, group_id: str, user_id: str, 
                                target_id: str) -> Tuple[bool, str, Optional[str]]:
        """
        解除特殊关系
        
        Args:
            group_id: 群聊ID
            user_id: 用户ID
            target_id: 目标用户ID
            
        Returns:
            (成功与否, 消息, 解除的关系类型)
        """
        # 不能与自己解除关系
        if user_id == target_id:
            return False, "不能与自己解除关系哦~", None
            
        # 获取用户数据
        user_data = self._get_user_social_data(group_id, user_id)
        target_data = self._get_user_social_data(group_id, target_id)
        
        # 查找两人之间的关系
        relation_type = None
        relation_name = None
        
        for rel_type, rel_id in user_data["special_relations"].items():
            if rel_id == target_id:
                relation_type = rel_type
                relation_name = RELATION_TYPE_NAMES.get(rel_type, rel_type)
                break
                
        if not relation_type:
            return False, "你们之间没有特殊关系，无法解除。", None
        
        # 解除关系
        user_data["special_relations"][relation_type] = None
        
        # 找到对方对应的关系并解除
        if target_id in self.social_data.get(str(group_id), {}):
            for rel_type, rel_id in target_data["special_relations"].items():
                if rel_id == user_id:
                    target_data["special_relations"][rel_type] = None
                    break
        
        # 重置好感度为50（朋友关系）
        self._update_favorability(group_id, user_id, target_id, 50 - self.get_favorability(group_id, user_id, target_id))
        self._update_favorability(group_id, target_id, user_id, 50 - self.get_favorability(group_id, target_id, user_id))
        
        # 保存数据
        self._save_data()
        
        return True, f"已成功解除与对方的'{relation_name}'关系。双方好感度已重置为50（朋友关系）。", relation_type
    
    def get_relationship_data(self, group_id: str, user_id: str, target_id: str) -> Dict:
        """
        获取两个用户之间的关系数据，用于生成关系卡片
        
        Args:
            group_id: 群聊ID
            user_id: 用户ID
            target_id: 目标用户ID
            
        Returns:
            关系数据字典
        """
        # 获取相互好感度
        a_to_b = self.get_favorability(group_id, user_id, target_id)
        b_to_a = self.get_favorability(group_id, target_id, user_id)
        
        # 获取关系等级
        a_to_b_level = self._get_relation_level(a_to_b)
        b_to_a_level = self._get_relation_level(b_to_a)
        
        # 获取特殊关系
        special_relation = self.get_special_relation(group_id, user_id, target_id)
        
        return {
            "user_a_to_b_favorability": a_to_b,
            "user_b_to_a_favorability": b_to_a,
            "user_a_to_b_level": a_to_b_level,
            "user_b_to_a_level": b_to_a_level,
            "special_relation": special_relation
        }
    
    def get_relationship_network(self, group_id: str, user_id: str, limit: int = 5) -> List[Dict]:
        """
        获取用户的关系网络，按好感度降序排列
        
        Args:
            group_id: 群聊ID
            user_id: 用户ID
            limit: 返回数量限制
            
        Returns:
            关系列表
        """
        user_data = self._get_user_social_data(group_id, user_id)
        favorability_data = user_data["favorability"]
        
        # 按好感度排序
        sorted_relations = sorted(
            favorability_data.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        # 获取特殊关系
        special_relations = {}
        for rel_type, rel_id in user_data["special_relations"].items():
            if rel_id:
                special_relations[rel_id] = RELATION_TYPE_NAMES.get(rel_type, rel_type)
        
        # 构建结果
        result = []
        for target_id, favorability in sorted_relations[:limit]:
            # 过滤掉好感度为0的关系
            if favorability <= 0:
                continue
                
            level = self._get_relation_level(favorability)
            special_relation = special_relations.get(target_id)
            
            result.append({
                "user_id": target_id,
                "favorability": favorability,
                "level": level,
                "special_relation": special_relation
            })
            
        return result


