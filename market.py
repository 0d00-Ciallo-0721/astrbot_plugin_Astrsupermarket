import os
import yaml
import random
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from astrbot.api.event import AstrMessageEvent
from astrbot.api.message_components import At
from astrbot.api import logger
from ._generate_market import generate_market_card_pillow  # 导入商城卡片生成函数
from .shop_manager import ShopManager


# --- 配置常量 ---
# 价格配置
HIRE_COST = 30  # 购买成本（无主人）
HIRE_COST_OWNED = 50  # 购买有主人的群友成本
SELL_PRICE = 20  # 出售价格
REDEEM_COST = 20  # 赎身成本
MAX_OWNED_MEMBERS = 3  # 最大拥有群友数量
MAX_DAILY_PURCHASES = 10  # 每日最大购买次数

# 工作列表配置
JOBS = {
    "搬砖": {
        "reward": (15.0, 20.0),      # 收益范围
        "success_rate": 1.0,
        "risk_cost": (0.0, 0.0),     # 失败惩罚范围
        "success_msg": "⛏️ {worker_name} 去工地搬了一天砖，累得筋疲力尽。你获得了 {reward:.2f} Astr币！",
        "failure_msg": ""
    },
    "送外卖": {
        "reward": (20.0, 25.0),
        "success_rate": 0.9,
        "risk_cost": (1.0, 3.0),
        "success_msg": "🚴 {worker_name} 一天骑车狂奔送外卖，终于赚到 {reward:.2f} Astr币！",
        "failure_msg": "🍔 {worker_name} 在送餐路上摔了一跤，赔了客户的订单，损失 {risk_cost:.2f} Astr币。"
    },
    "送快递": {
        "reward": (25.0, 30.0),
        "success_rate": 0.8,
        "risk_cost": (3.0, 6.0),
        "success_msg": "📦 {worker_name} 风里雨里送快递，终于赚到了 {reward:.2f} Astr币。",
        "failure_msg": "📭 {worker_name} 快递丢件，被客户投诉，赔了 {risk_cost:.2f} Astr币。"
    },
    "家教": {
        "reward": (30.0, 35.0),
        "success_rate": 0.7,
        "risk_cost": (6.0, 9.0),
        "success_msg": "📚 {worker_name} 耐心辅导学生，家长满意，赚得 {reward:.2f} Astr币。",
        "failure_msg": "😵 {worker_name} 学生成绩没提高，被辞退，损失 {risk_cost:.2f} Astr币。"
    },
    "挖矿": {
        "reward": (35.0, 40.0),
        "success_rate": 0.6,
        "risk_cost": (9.0, 12.0),
        "success_msg": "⛏️ {worker_name} 在地下挖矿一整天，挖到了珍贵矿石，获得 {reward:.2f} Astr币！",
        "failure_msg": "💥 {worker_name} 不小心引发了塌方事故，受伤并损失 {risk_cost:.2f} Astr币。"
    },
    "代写作业": {
        "reward": (40.0, 45.0),
        "success_rate": 0.5,
        "risk_cost": (12.0, 15.0),
        "success_msg": "📘 {worker_name} 偷偷帮人代写作业，轻松赚到 {reward:.2f} Astr币。",
        "failure_msg": "📚 {worker_name} 被老师发现代写，被罚 {risk_cost:.2f} Astr币。"
    },
    "奶茶店": {
        "reward": (45.0, 50.0),
        "success_rate": 0.4,
        "risk_cost": (15.0, 18.0),
        "success_msg": "🧋 {worker_name} 在奶茶店忙了一天，挣了 {reward:.2f} Astr币。",
        "failure_msg": "🥤 {worker_name} 手滑打翻整桶奶茶，赔了 {risk_cost:.2f} Astr币。"
    },
    "偷窃苏特尔的宝库": {
        "reward": 500.0,          # 固定奖励
        "success_rate": 0.02,      # 5%的成功率
        "risk_cost": 10.0,         # 固定惩罚
        "success_msg": "🌟 {worker_name} 偷窃成功，从苏特尔的钱包中获得了难以置信的 {reward:.2f} Astr币！",
        "failure_msg": "💫 {worker_name} 偷窃失败，被苏特尔当场抓获，幕后黑手的你赔付了{risk_cost:.2f} Astr币了。"
    }
}

class MarketManager:
    def __init__(self, data_dir: str):
        """初始化Astr币商城管理器"""
        self.data_dir = data_dir
        self.market_data_file = os.path.join(data_dir, "market_data.yaml")
        self.market_data = self._load_market_data()
        
        # 打工会话状态
        self.work_sessions = {}  # {session_id: {'owner_id': xx, 'worker_id': xx}}
        
    def _load_market_data(self) -> dict:
        """加载商城数据"""
        if os.path.exists(self.market_data_file):
            try:
                with open(self.market_data_file, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f) or {}
            except Exception as e:
                logger.error(f"加载商城数据失败: {str(e)}")
                return {}
        return {}
    
    def _save_market_data(self):
        """保存商城数据"""
        try:
            with open(self.market_data_file, 'w', encoding='utf-8') as f:
                yaml.dump(self.market_data, f, allow_unicode=True)
        except Exception as e:
            logger.error(f"保存商城数据失败: {str(e)}")
    
    def _get_group_market_data(self, group_id: str) -> dict:
        """获取指定群聊的商城数据，如果不存在则创建"""
        if not group_id:
            return self.market_data.setdefault("private_chat", {})
        return self.market_data.setdefault(str(group_id), {})

    def _get_user_market_data(self, group_id: str, user_id: str) -> dict:
        """获取指定群聊中用户的商城数据，如果不存在则创建"""
        group_market_data = self._get_group_market_data(group_id)
        
        if user_id not in group_market_data:
            group_market_data[user_id] = {
                "owned_members": [],  # 拥有的群友列表
                "owner": None,  # 被谁拥有
                "daily_purchases": 0,  # 今日购买次数
                "last_purchase_date": "",  # 上次购买日期
                "worked_for": [] , # 已经为谁打工过（重置条件：被重新购买）
                "total_work_revenue": 0.0,    # 无情资本家：打工总收入
                "total_work_failures": 0      # 黑心老板：名下奴隶打工失败次数            
            
            
            }
            
        # 步骤2：获取用户数据，并将日期检查逻辑移到if块之外，确保每次都执行
        user_market_info = group_market_data[user_id]
        today = datetime.now().strftime("%Y-%m-%d")

        # 步骤3：检查上次购买日期是否为今天，如果不是则重置购买次数
        if user_market_info.get("last_purchase_date", "") != today:
            user_market_info["daily_purchases"] = 0
            user_market_info["last_purchase_date"] = today
            self._save_market_data()
                
        return user_market_info

    
    async def get_user_name(self, event: AstrMessageEvent, user_id: str) -> str:
        """
        获取群内任意用户的名称（优先使用群名片）。
        这是实现名称替换的核心函数。
        """
        # 检查是否是机器人自己
        if user_id == event.get_self_id():
            return "妹妹"

        # 如果要获取的是当前事件发送者的名字，直接用 get_sender_name() 更高效
        if user_id == event.get_sender_id():
            sender_name = event.get_sender_name()
            if sender_name:
                return sender_name

        # 对于其他用户，或发送者名字获取失败时，调用API
        if event.get_platform_name() == "aiocqhttp":
            try:
                # 从 event 对象获取协议端客户端
                from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import AiocqhttpMessageEvent
                if isinstance(event, AiocqhttpMessageEvent):
                    client = event.bot
                    group_id = event.get_group_id()

                    if group_id:
                        # 调用 get_group_member_info API
                        user_info = await client.api.call_action(
                            'get_group_member_info', 
                            group_id=int(group_id), 
                            user_id=int(user_id)
                        )
                        
                        # 优先使用群名片(card)，其次是昵称(nickname)
                        if user_info:
                            if user_info.get('card'):
                                return user_info['card']
                            if user_info.get('nickname'):
                                return user_info['nickname']
            except Exception as e:
                # 如果API调用失败（如用户已退群），则记录日志并使用后备方案
                logger.warning(f"通过API获取用户({user_id})名称失败: {e}")
        
        # 所有方法都失败后的最终后备方案
        return f"用户{user_id}"
    
    @staticmethod
    def get_sorted_jobs() -> List[str]:
        """获取按收益排序的工作列表"""
        return sorted(JOBS.keys(), key=lambda job: JOBS[job]["reward"][0] if isinstance(JOBS[job]["reward"], tuple) else JOBS[job]["reward"])
    
    def start_work_session(self, session_id: str, group_id: str, owner_id: str, worker_id: str):
        """开始一个打工会话"""
        self.work_sessions[session_id] = {
            'group_id': group_id,  # 添加群聊ID
            'owner_id': owner_id,
            'worker_id': worker_id
        }
    
    def get_work_session(self, session_id: str) -> Optional[dict]:
        """获取打工会话"""
        return self.work_sessions.get(session_id)
    
    def end_work_session(self, session_id: str):
        """结束打工会话"""
        if session_id in self.work_sessions:
            del self.work_sessions[session_id]
    
    async def process_buy_member(self, event: AstrMessageEvent, group_id: str, buyer_id: str, target_id: str, 
                        user_data: dict, confirm: bool = False) -> Tuple[bool, str, bool]:
        """处理购买群友的逻辑
        
        Args:
            event: 消息事件
            buyer_id: 购买者ID
            target_id: 目标群友ID
            user_data: 用户数据（包含points字段）
            confirm: 是否确认购买有主人的群友
            
        Returns:
            (成功与否, 提示消息)
        """
        # 检查是否尝试购买机器人
        if target_id == event.get_self_id():
            return False, "妹妹是天，不能对妹妹操作", True  # 第三个值表示特殊情况

        # 检查是否自己购买自己
        if buyer_id == target_id:
            return False, "不能购买自己哦~", True  # 第三个值表示特殊情况
        
        buyer_market_data = self._get_user_market_data(group_id, buyer_id)
        target_market_data = self._get_user_market_data(group_id, target_id)
        
        # 检查每日购买次数限制
        if buyer_market_data["daily_purchases"] >= MAX_DAILY_PURCHASES:
            return False, f"今日购买次数已达上限({MAX_DAILY_PURCHASES}次)，明天再来吧~", False
        
        # 检查拥有群友数量上限
        if len(buyer_market_data["owned_members"]) >= MAX_OWNED_MEMBERS:
            return False, f"你已经拥有{MAX_OWNED_MEMBERS}个群友了，无法继续购买~", False
        
        # 检查目标是否已有主人
        has_owner = target_market_data["owner"] is not None
        cost = HIRE_COST_OWNED if has_owner else HIRE_COST
        
        # 如果目标有主人且未确认购买
        if has_owner and not confirm:
            target_name = await self.get_user_name(event, target_id)
            current_owner = await self.get_user_name(event, target_market_data["owner"])
            return False, f"{target_name}已经属于{current_owner}了，需要花费{HIRE_COST_OWNED}Astr币继续购买，请发送'强制购买 @{target_name}'确认", False
        
        # 检查Astr币是否足够
        if user_data["points"] < cost:
            return False, f"你的Astr币不足，需要{cost}Astr币才能购买~", False
        
        # 执行购买
        user_data["points"] -= cost
        
        # 如果目标已有主人，从原主人的拥有列表中移除
        if has_owner:
            original_owner = target_market_data["owner"]
            original_owner_data = self._get_user_market_data(group_id, original_owner)
            if target_id in original_owner_data["owned_members"]:
                original_owner_data["owned_members"].remove(target_id)
        
        
        # 更新购买者和目标的数据
        buyer_market_data["owned_members"].append(target_id)
        buyer_market_data["daily_purchases"] += 1
        target_market_data["owner"] = buyer_id
        target_market_data["worked_for"] = []  # 重置打工状态，被重新购买后可以再次打工
        
        self._save_market_data()
        
        target_name = await self.get_user_name(event, target_id)
        
        # 生成图片卡片
        buyer_name = await self.get_user_name(event, buyer_id)
        avatar_url = ""
        if event.get_platform_name() == "aiocqhttp":
            avatar_url = f"http://q1.qlogo.cn/g?b=qq&nk={buyer_id}&s=640"
            
        return True, f"✅ 购买成功！你已花费 {cost} Astr币购买了 {target_name}。", False

    async def init_work_command(self, event: AstrMessageEvent, group_id: str, owner_id: str, worker_id: str) -> Tuple[bool, str]:
        """初始化打工命令，返回工作列表
        
        Returns:
            (成功与否, 提示消息)
        """
        # 检查是否尝试让机器人打工
        if worker_id == event.get_self_id():
            return False, "妹妹是天，不能对妹妹操作"
        
            # 检查是否拥有该用户
        owner_market_data = self._get_user_market_data(group_id, owner_id)
        if worker_id not in owner_market_data["owned_members"]:
            return False, "对方不是你的群友，无法让其打工~", None

        # 检查该用户的商城数据
        worker_market_data = self._get_user_market_data(group_id, worker_id)
        if worker_market_data["owner"] != owner_id:
            return False, "对方不是你的群友，无法让其打工~", None
        if owner_id in worker_market_data["worked_for"]:
            return False, "Ta已经为你打工过了，需要重新购买后才能再次打工~", None

        # 创建打工会话
        self.start_work_session(event.unified_msg_origin, group_id, owner_id, worker_id)

        # 获取引导文本
        worker_name = await self.get_user_name(event, worker_id)
        message = f"请选择让 {worker_name} 做的工作："

        # 获取图片路径（利用缓存机制）
        image_path = await self.get_work_list_image_path()

        return True, message, image_path
    
    async def get_work_list_image_path(self) -> Optional[str]:
        """
        获取打工列表图片的路径。如果图片不存在，则生成它。
        """
        # 定义图片保存路径为插件根目录下的 work_list.png
        plugin_dir = os.path.dirname(__file__)
        image_path = os.path.join(plugin_dir, "work_list.png")

        # 如果文件已存在，直接返回路径
        if os.path.exists(image_path):
            return image_path
        
        # 如果文件不存在，调用生成函数
        from ._generate_work_list import generate_work_list_image
        success = await generate_work_list_image(image_path)
        if success:
            return image_path
        else:
            return None

    async def process_work_job(self, event: AstrMessageEvent, job_name: str, owner_user_data: dict) -> Tuple[bool, str, int]:
        """
        处理具体工作的逻辑, 同时支持道具效果和成就统计
        
        Args:
            owner_user_data (dict): 打工主人的核心用户数据 (user_data.yaml)
        
        Returns:
            (成功与否, 提示消息或图片路径, 收益变化)
        """
        session = self.get_work_session(event.unified_msg_origin)
        if not session:
            return False, "没有进行中的打工会话，请先使用'打工 @群友'命令~", 0
        
        group_id = session['group_id']
        owner_id = session['owner_id']
        worker_id = session['worker_id']

        if job_name not in JOBS:
            return False, f"没有找到'{job_name}'这项工作，请重新选择~", 0
        
        # --- [核心修改] 在函数内部获取市场数据 ---
        owner_market_data = self._get_user_market_data(group_id, owner_id)
        worker_market_data = self._get_user_market_data(group_id, worker_id)
        # ------------------------------------

        worker_name = await self.get_user_name(event, worker_id)
        
        job = JOBS[job_name]
        
        # --- [修正] 检查是否为"打工8"，并应用道具效果 ---
        is_high_risk_job = (job_name == "偷窃苏特尔的宝库")
        buffs = owner_user_data.get('buffs', {})
        
        # 1. 判定成功率
        is_success = False
        if not is_high_risk_job and buffs.get("work_guarantee_success", 0) > 0:
            is_success = True
            buffs["work_guarantee_success"] -= 1
        else:
            is_success = random.random() < job["success_rate"]
        
        # 2. 计算收益或损失
        result = 0
        message = ""
        
        if is_success:
            reward_val = job["reward"]
            reward = random.uniform(reward_val[0], reward_val[1]) if isinstance(reward_val, (list, tuple)) else reward_val
            
            # 应用奖励提升效果（对高风险工作无效）
            if not is_high_risk_job and buffs.get("work_reward_boost", 0) > 0:
                boost_percentage = random.uniform(0.01, 0.5)  # 1%-50%的随机提升
                original_reward = reward
                reward *= (1 + boost_percentage)
                message = f"[能量饮料效果] 奖励提升了{int(boost_percentage*100)}%！\n"
                buffs["work_reward_boost"] -= 1
            
            reward = round(reward, 2)
            owner_user_data["points"] += reward
            
            # 更新主人总收入
            owner_market_data["total_work_revenue"] = owner_market_data.get("total_work_revenue", 0.0) + reward
            
            message += job["success_msg"].format(worker_name=worker_name, reward=reward)
            result = reward
        else:
            if not is_high_risk_job and buffs.get("work_no_penalty", 0) > 0:
                message = f"[守护符效果] 虽然打工失败，但不会扣除Astr币！\n"
                message += job["failure_msg"].format(worker_name=worker_name, risk_cost=0)
                result = 0
                buffs["work_no_penalty"] -= 1
            else:
                cost_val = job["risk_cost"]
                risk_cost = random.uniform(cost_val[0], cost_val[1]) if isinstance(cost_val, (list, tuple)) else cost_val
                risk_cost = round(risk_cost, 2)
                owner_user_data["points"] -= risk_cost
                
                # 更新主人名下失败次数
                owner_market_data["total_work_failures"] = owner_market_data.get("total_work_failures", 0) + 1

                message = job["failure_msg"].format(worker_name=worker_name, risk_cost=risk_cost)
                result = -risk_cost
        
        # 清理空的buff项
        owner_user_data["buffs"] = {k: v for k, v in buffs.items() if v > 0}
        
        # 无论成功与否，都要记录本次打工
        worker_market_data["worked_for"].append(owner_id)
        
        self.end_work_session(event.unified_msg_origin)
        self._save_market_data()  # 保存市场数据的更改
        
        return is_success, message, result


    
    async def process_sell_member(self, event: AstrMessageEvent, group_id: str, seller_id: str, 
                                target_id: str, user_data: dict) -> Tuple[bool, str]:
        """处理出售群友的逻辑"""
        # 检查是否尝试出售机器人
        if target_id == event.get_self_id():
            return False, "妹妹是天，不能对妹妹操作"       
        
        seller_market_data = self._get_user_market_data(group_id, seller_id)
        target_market_data = self._get_user_market_data(group_id, target_id)
        
        # 检查是否拥有该群友
        if target_id not in seller_market_data["owned_members"]:
            return False, "对方不是你的群友，无法出售~"
        
        # 执行出售
        user_data["points"] += SELL_PRICE
        seller_market_data["owned_members"].remove(target_id)
        target_market_data["owner"] = None
        
        self._save_market_data()
        
        target_name = await self.get_user_name(event, target_id)
        
        return True, f"✅ 出售成功！你已出售 {target_name}，获得 {SELL_PRICE} Astr币。"
    
    async def process_redeem(self, event: AstrMessageEvent, group_id: str, user_id: str, 
                       user_data: dict, confirm: bool = False) -> Tuple[bool, str]:
        """处理自我赎身的逻辑"""
        # 如果是机器人，拒绝操作
        if user_id == event.get_self_id():
            return False, "妹妹是天，不需要赎身~"
            
        market_data = self._get_user_market_data(group_id, user_id)

        # 检查是否被购买
        if market_data["owner"] is None:
            return False, "你是自由身，无需赎身~"
        
        # 检查是否为主人工作过，如果没有打工且没有确认，提示继续赎身
        if market_data["owner"] not in market_data["worked_for"] and not confirm:
            # 获取当前的主人名称
            owner_name = await self.get_user_name(event, market_data["owner"])
            return False, f"你还没有为{owner_name}打工，如果不想打工直接赎身需要花费30Astr币，请发送'@机器人 强制赎身'确认"
        
        # 确定赎身费用
        cost = 30 if not market_data["owner"] in market_data["worked_for"] else REDEEM_COST
        
        # 检查Astr币是否足够
        if user_data["points"] < cost:
            return False, f"你的Astr币不足，需要{cost}Astr币才能赎身~"
        
        # 执行赎身
        owner_id = market_data["owner"]
        owner_market_data = self._get_user_market_data(group_id, owner_id)
        
        user_data["points"] -= cost
        market_data["owner"] = None
        
        if user_id in owner_market_data["owned_members"]:
            owner_market_data["owned_members"].remove(user_id)
        
        self._save_market_data()
   
        return True, f"✅ 赎身成功！你已花费 {cost} Astr币赎回自由身。"
    
    async def get_market_status(self, event: AstrMessageEvent, group_id: str, user_id: str) -> Dict:
        """获取用户在商城中的状态数据字典"""
        if user_id == event.get_self_id():
            return {"error": "妹妹是天，不参与商城系统~"}

        market_data = self._get_user_market_data(group_id, user_id)
        
        status_data = {}
        # 1. 主人信息
        if market_data.get("owner"):
            owner_id = market_data["owner"]
            status_data["owner_id"] = owner_id
            status_data["owner_name"] = await self.get_user_name(event, owner_id)
            status_data["has_worked_for_owner"] = owner_id in market_data.get("worked_for", [])
        
        # 2. 拥有的群友列表信息
        owned_members_list = []
        if market_data.get("owned_members"):
            for member_id in market_data["owned_members"]:
                member_market_data = self._get_user_market_data(group_id, member_id)
                owned_members_list.append({
                    "id": member_id,
                    "name": await self.get_user_name(event, member_id),
                    "has_worked": user_id in member_market_data.get("worked_for", [])
                })
        status_data["owned_members"] = owned_members_list
        status_data["daily_purchases"] = market_data.get("daily_purchases", 0)
        status_data["max_purchases"] = MAX_DAILY_PURCHASES

        return status_data


