import os
import yaml
import random
import time
import asyncio
from datetime import datetime, timedelta

from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from astrbot.api.all import *
import astrbot.api.message_components as Comp

from ._generate_card import generate_sign_card, generate_sign_card_pillow 
from .re_sign import perform_re_sign
from .qsin import process_sign_in 
from .market import MarketManager, JOBS  # 导入商城管理器
from .shop_manager import ShopManager
from ._generate_leaderboard import generate_leaderboard_image
from ._generate_achievements import generate_achievements_image
from ._generate_shop import generate_backpack_card
from .achievements import ACHIEVEMENTS
from ._generate_shop import generate_shop_card
from .shop_items import SHOP_DATA
from .adventure import AdventureManager
from .social import SocialManager
from .social_events import SPECIAL_RELATION_ITEMS, SPECIAL_RELATION_TYPES
from ._command_card import generate_command_card

# 清理任务的执行周期（单位：小时），例如每小时检查一次
CLEANUP_INTERVAL_HOURS = 1 
# 图片文件的最大保留时间（单位：天），例如只保留最近1天的图片
MAX_FILE_AGE_DAYS = 1

@register("astrbot_plugin_Astrsupermarket", "和泉智宏", "Astr超级市场", "1.0", "https://github.com/0d00-Ciallo-0721/astrbot_plugin_Astrsupermarket")
class SignPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        # 确保必要的目录存在
        self.plugin_dir = os.path.dirname(os.path.abspath(__file__))
        self.data_dir = os.path.join(self.plugin_dir, "data/feifeiQsign")
        os.makedirs(self.data_dir, exist_ok=True)
        
        # 用户数据文件路径
        self.user_data_file = os.path.join(self.data_dir, "user_data.yaml")
        
        # 初始化用户数据
        self.user_data = self._load_user_data()
        
        # 初始化商城管理器
        self.market = MarketManager(self.data_dir)
        
        # 初始化商店管理器（新增）
        self.shop_manager = ShopManager(self.data_dir)
        
        # 初始化大冒险管理器（新增）
        self.adventure_manager = AdventureManager()
        
        # 初始化社交管理器
        self.social_manager = SocialManager(self.data_dir)        
        
        # 启动后台清理任务
        self.cleanup_task = asyncio.create_task(self._periodic_cleanup_task())

        logger.info("Astr签到插件已初始化")

    def _load_user_data(self) -> dict:
        """加载用户数据"""
        if os.path.exists(self.user_data_file):
            try:
                with open(self.user_data_file, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f) or {}
            except Exception as e:
                logger.error(f"加载用户数据失败: {str(e)}")
                return {}
        return {}

    def _save_user_data(self):
        """保存用户数据"""
        try:
            with open(self.user_data_file, 'w', encoding='utf-8') as f:
                yaml.dump(self.user_data, f, allow_unicode=True)
        except Exception as e:
            logger.error(f"保存用户数据失败: {str(e)}")
    
    def is_bot_mentioned(self, event: AstrMessageEvent) -> bool:
        """检查消息中是否@了机器人"""
        messages = event.get_messages()
        self_id = event.get_self_id()
        
        for seg in messages:
            if isinstance(seg, Comp.At) and str(seg.qq) == self_id:
                return True
        return False

    def get_target_user_id(self, event: AstrMessageEvent) -> str:
        """获取被@的用户ID（排除机器人自身）"""
        messages = event.get_messages()
        self_id = event.get_self_id()
        
        # 查找消息中的At对象，排除机器人自身
        for seg in messages:
            if isinstance(seg, Comp.At) and str(seg.qq) != self_id:
                return str(seg.qq)
        return None

    async def _periodic_cleanup_task(self):
        """定时的后台清理任务，周期性执行清理操作。"""
        interval_seconds = CLEANUP_INTERVAL_HOURS * 3600
        age_threshold_seconds = MAX_FILE_AGE_DAYS * 24 * 3600

        while True:
            try:
                await asyncio.sleep(interval_seconds)
                logger.info("开始执行例行图片清理...")

                base_data_path = os.path.join(self.plugin_dir, "data") 
                
                directories_to_clean = [
                    # 原有的目录
                    os.path.join(base_data_path, "market_cards"),
                    os.path.join(base_data_path, "sign_cards"),
                    os.path.join(base_data_path, "leaderboards"),
                    os.path.join(base_data_path, "achievements"),
                    os.path.join(base_data_path, "shop_cards"),
                    os.path.join(base_data_path, "backpack_cards"),
                    os.path.join(base_data_path, "adventure_reports"),
                    os.path.join(base_data_path, "social_cards"),     
                    os.path.join(base_data_path, "date_reports"),    
                    os.path.join(base_data_path, "social_network"),   
                    os.path.join(base_data_path, "command_cards")     
                ]

                for directory in directories_to_clean:
                    self._cleanup_directory(directory, age_threshold_seconds)
                
                logger.info("本轮图片清理完成。")

            except asyncio.CancelledError:
                logger.info("后台清理任务已正常取消。")
                break
            except Exception as e:
                logger.error(f"后台清理任务发生未知错误: {e}")
                await asyncio.sleep(60)

    
    def _cleanup_directory(self, directory_path: str, age_threshold_seconds: float):
        """清理指定目录下的过期文件。"""
        if not os.path.isdir(directory_path):
            return
            
        logger.info(f"正在扫描目录: {directory_path}")
        current_time = time.time()
        files_deleted_count = 0

        for filename in os.listdir(directory_path):
            file_path = os.path.join(directory_path, filename)
            try:
                if os.path.isfile(file_path):
                    file_mod_time = os.path.getmtime(file_path)
                    if (current_time - file_mod_time) > age_threshold_seconds:
                        os.remove(file_path)
                        files_deleted_count += 1
                        logger.debug(f"已删除过期图片: {filename}")
            except Exception as e:
                logger.error(f"删除文件 {file_path} 时出错: {e}")

        if files_deleted_count > 0:
            logger.info(f"在 {directory_path} 中成功删除了 {files_deleted_count} 个过期文件。")

    def _get_group_user_data(self, group_id: str) -> dict:
        """获取指定群聊的所有用户数据，如果群聊不存在则创建。"""
        if not group_id:
            # 为私聊或无法识别群聊ID的情况提供默认值
            return self.user_data.setdefault("private_chat", {})
        return self.user_data.setdefault(str(group_id), {})

    def _get_user_in_group(self, group_id: str, user_id: str) -> dict:
        """获取指定群聊中特定用户的数据，如不存在则初始化"""
        group_data = self._get_group_user_data(group_id)
        if user_id not in group_data:
            group_data[user_id] = {
                "total_days": 0,      # 总签到天数
                "streak_days": 0,     # 连续签到天数
                "last_sign": "",      # 上次签到日期
                "points": 0,          # Astr币数量
                "lottery_date": "",   # 上次抽奖日期
                "lottery_count": 0,   # 当日抽奖次数
                "achievements": [],         # 已解锁的成就ID列表
                "current_title": "",        # 当前佩戴的称号
                "high_tier_wins": 0,        # 欧皇榜：6星或隐藏奖励次数
                "consecutive_1star": 0,     # 非酋成就：连续抽到1星的次数            
                "total_gifted": 0,          # 用于记录累计赠送金额
                "gift_count": 0,            # 用于记录赠送次数
                "last_gift_date": "",       # 用于记录上次赠送日期
                "consecutive_gift_days": 0, # 用于记录连续赠送天数
                "stamina": 100,             # [新增] 当前体力值
                "max_stamina": 160,         # [新增] 最大体力值
                "adventure_count": 0,       # [新增] 冒险次数统计
                "last_adventure_date": ""   # [新增] 上次冒险日期
            }
        
        # 兼容旧数据：如果存在旧的数据但没有新字段，进行迁移
        user_data = group_data[user_id]
        
        # 迁移旧的抽奖数据
        if "last_lottery" in user_data and "lottery_date" not in user_data:
            user_data["lottery_date"] = user_data["last_lottery"]
            user_data["lottery_count"] = 1 if user_data["last_lottery"] == datetime.now().strftime("%Y-%m-%d") else 0
        
        # [新增] 添加体力系统相关字段
        if "stamina" not in user_data:
            user_data["stamina"] = 160
        if "max_stamina" not in user_data:
            user_data["max_stamina"] = 160
        if "adventure_count" not in user_data:
            user_data["adventure_count"] = 0
        if "last_adventure_date" not in user_data:
            user_data["last_adventure_date"] = ""
            
        return group_data[user_id]



    # 修改后的签到命令
    @filter.command("签到", alias={"每日签到", "daily"})
    async def sign_in(self, event: AstrMessageEvent):
        """每日签到指令"""
        # 检查是否@了机器人
        if not self.is_bot_mentioned(event):
            return
        
        # 调用qsin.py中的签到处理函数
        async for result in process_sign_in(self, event):
            yield result


    @filter.command("补签", alias={"buqian", "makeup"})
    @filter.event_message_type(filter.EventMessageType.GROUP_MESSAGE)
    async def re_sign(self, event: AstrMessageEvent):
        """补签指令，用于补签昨天的签到"""
        # 检查是否@了机器人
        if not self.is_bot_mentioned(event):
            return
            
        # 获取群聊ID和用户信息
        group_id = event.get_group_id()
        user_id = event.get_sender_id()
        user_name = event.get_sender_name() or f"用户{user_id}"
        
        # 获取用户头像
        avatar_url = ""
        if event.get_platform_name() == "aiocqhttp":
            avatar_url = f"http://q1.qlogo.cn/g?b=qq&nk={user_id}&s=640"
        
        # 执行补签操作，传递group_id
        success, result = await perform_re_sign(
            self, 
            event, 
            group_id,  # 传递群组ID
            user_id, 
            user_name, 
            avatar_url
        )
        
        
        if success: 
             # --- [集成] 在补签成功后，解锁“后悔药”并进行通用检查 ---
            await self.unlock_specific_achievement(event, user_id, 'signin_4')
            await self.check_and_unlock_achievements(event, user_id)     
            # 如果结果是URL，发送图片
            if result.startswith("http") or os.path.exists(result):
                yield event.image_result(result)
            else:
                # 否则发送文本
                yield event.plain_result(result)
        else:
            # 补签失败，发送失败原因
            yield event.plain_result(result)

    # main.py 的 buy_member 函数修改

    @filter.command("购买")
    @filter.event_message_type(filter.EventMessageType.GROUP_MESSAGE)
    async def buy_member(self, event: AstrMessageEvent):
        """购买群友指令"""
        # 检查是否@了机器人
        if not self.is_bot_mentioned(event):
            return
            
        # 获取群聊ID和用户信息
        group_id = event.get_group_id()
        buyer_id = event.get_sender_id()
        buyer_name = event.get_sender_name() or f"用户{buyer_id}"
        
        # 初始化用户数据
        user_data = self._get_user_in_group(group_id, buyer_id)

        # 解析@的用户（排除机器人自身的@）
        target_id = self.get_target_user_id(event)

        if not target_id:
            yield event.plain_result("请@要购买的群友~")
            return
        
        # 处理购买逻辑，传递group_id
        success, result, is_special_case = await self.market.process_buy_member(
            event, group_id, buyer_id, target_id, user_data
        )
        
        # 直接检查是否尝试购买机器人并触发成就
        if target_id == event.get_self_id():
            yield event.plain_result("妹妹是天，不能对妹妹操作")
            return
            
        # 检查是否尝试购买自己并触发成就
        if buyer_id == target_id:
            await self.unlock_specific_achievement(event, buyer_id, 'fun_2')
            yield event.plain_result("不能购买自己哦~")
            return
        
        # 保存用户数据（如果有变动）
        if success:
            self._save_user_data()
            await self.check_and_unlock_achievements(event, buyer_id)
            
        # 返回结果
        yield event.plain_result(result)


    @filter.command("强制购买")
    @filter.event_message_type(filter.EventMessageType.GROUP_MESSAGE)
    async def confirm_buy_member(self, event: AstrMessageEvent):
        """确认购买已有主人的群友"""
        # 检查是否@了机器人
        if not self.is_bot_mentioned(event):
            return
            
        # 获取群聊ID和用户信息
        group_id = event.get_group_id()
        buyer_id = event.get_sender_id()
        
        # 初始化用户数据
        user_data = self._get_user_in_group(group_id, buyer_id)
        
        # 解析@的用户（排除机器人自身的@）
        target_id = self.get_target_user_id(event)
                
        if not target_id:
            yield event.plain_result("请@要购买的群友~")
            return
        
        # 处理购买逻辑（确认模式）并传递群聊ID
        success, result, is_special_case = await self.market.process_buy_member(
            event, group_id, buyer_id, target_id, user_data, confirm=True
        )
        
        # 如果是特殊情况，解锁相关成就
        if not success and is_special_case:
            if buyer_id == target_id:
                await self.unlock_specific_achievement(event, buyer_id, 'fun_2')
        
        # 保存用户数据（如果有变动）
        if success:
            self._save_user_data()
            
        # 检查结果是否为图片路径
        yield event.plain_result(result)

    # 修改主文件中的打工指令
    @filter.command("打工")
    @filter.event_message_type(filter.EventMessageType.GROUP_MESSAGE)
    async def work_command(self, event: AstrMessageEvent):
        """让群友打工指令"""
        # 检查是否@了机器人
        if not self.is_bot_mentioned(event):
            return
            
        # 获取群聊ID和用户信息
        group_id = event.get_group_id()
        owner_id = event.get_sender_id()
        
        # 初始化用户数据
        user_data = self._get_user_in_group(group_id, owner_id)
        
        # 解析@的用户
        worker_id = self.get_target_user_id(event)
                
        if not worker_id:
            yield event.plain_result("请@要让其打工的群友~")
            return
        
        # 检查目标是否为机器人
        if worker_id == event.get_self_id():
            yield event.plain_result("妹妹是天，不能对妹妹操作")
            return
            
        # 处理新的返回值
        success, text_message, image_path = await self.market.init_work_command(event, group_id, owner_id, worker_id)
        
        # 发送引导文本
        yield event.plain_result(text_message)

        # 如果成功且有图片路径，则发送图片
        if success and image_path:
            yield event.image_result(image_path)
        # 如果成功但图片生成失败，可以给一个提示
        elif success and not image_path:
            # 图片生成失败，回退到文本方式
            job_list = self.market.get_sorted_jobs()
            job_text = "\n".join([f"{i+1}. {job} - 收益:{JOBS[job]['reward']}Astr币 成功率:{int(JOBS[job]['success_rate']*100)}%" 
                                for i, job in enumerate(job_list)])
            yield event.plain_result(job_text)

    

    @filter.event_message_type(filter.EventMessageType.GROUP_MESSAGE)
    async def handle_work_job_selection(self, event: AstrMessageEvent):
        """处理用户选择的工作"""
        # 获取会话信息
        session = self.market.get_work_session(event.unified_msg_origin)
        if not session:
            return  # 不是打工会话，忽略
                
        # 检查发送者是否是会话中的主人
        if event.get_sender_id() != session['owner_id']:
            return  # 不是会话中的主人，忽略
        
        # 检查消息中是否包含@或"打工"指令，是则忽略
        if "[At:" in event.message_str or "打工" in event.message_str:
            return
        
        # 确保原始消息包含纯文本内容
        message = event.message_str.strip()
        
        # 如果消息为空，直接返回
        if not message:
            return
        
        # 处理数字选择
        job_name = None
        try:
            if message.isdigit():
                job_index = int(message) - 1
                job_list = self.market.get_sorted_jobs()
                if 0 <= job_index < len(job_list):
                    job_name = job_list[job_index]
            else:
                # 直接输入工作名
                job_list = self.market.get_sorted_jobs()
                if message in job_list:
                    job_name = message
        except Exception as e:
            logger.error(f"处理工作选择时出错: {str(e)}")
                
        if not job_name:
            yield event.plain_result("无效的选择，请输入正确的工作编号或名称~")
            return
        
        # 获取会话相关信息
        owner_id = session['owner_id']
        
        # 获取正确的群组ID，确保数据隔离
        group_id = session['group_id']
        owner_user_data = self._get_user_in_group(group_id, owner_id)
        
        # 处理工作执行
        success, result_message, work_profit = await self.market.process_work_job(
            event, job_name, owner_user_data
        )

        # 保存用户数据
        self._save_user_data()

        # 检查是否应该解锁"赌神"成就 - 只有在成功执行偷窃苏特尔的宝库时才解锁
        if success and job_name == "偷窃苏特尔的宝库":
            await self.unlock_specific_achievement(event, owner_id, 'work_1')

        # 进行其他通用成就检查
        await self.check_and_unlock_achievements(event, owner_id)

        # 直接发送文本结果
        yield event.plain_result(result_message)

        # 结束会话
        self.market.end_work_session(event.unified_msg_origin)

    @filter.command("出售")
    @filter.event_message_type(filter.EventMessageType.GROUP_MESSAGE)
    async def sell_member(self, event: AstrMessageEvent):
        """出售群友指令"""
        # 检查是否@了机器人
        if not self.is_bot_mentioned(event):
            return
            
        # 获取群聊ID和用户信息
        group_id = event.get_group_id()
        seller_id = event.get_sender_id()
        
        # 初始化用户数据
        user_data = self._get_user_in_group(group_id, seller_id)
        
        # 解析@的用户（排除机器人自身的@）
        target_id = self.get_target_user_id(event)
                
        if not target_id:
            yield event.plain_result("请@要出售的群友~")
            return
        
        # 检查目标是否为机器人
        if target_id == event.get_self_id():
            yield event.plain_result("妹妹是天，不能对妹妹操作")
            return
            
        # 处理出售逻辑并传递群聊ID
        success, message = await self.market.process_sell_member(
            event, group_id, seller_id, target_id, user_data
        )
        
        # 保存用户数据（如果有变动）
        if success:
            self._save_user_data()
            
        # 检查结果是否为图片路径
        if success and os.path.exists(message):
            yield event.image_result(message)
        else:
            yield event.plain_result(message)

    
    @filter.command("赎身")
    @filter.event_message_type(filter.EventMessageType.GROUP_MESSAGE)
    async def redeem_self(self, event: AstrMessageEvent):
        """赎身指令"""
        # 检查是否@了机器人
        if not self.is_bot_mentioned(event):
            return
            
        # 获取群聊ID和用户信息
        group_id = event.get_group_id()
        user_id = event.get_sender_id()
        
        # 初始化用户数据
        user_data = self._get_user_in_group(group_id, user_id)
        
        # 处理赎身逻辑并传递群聊ID
        success, message = await self.market.process_redeem(
            event, group_id, user_id, user_data
        )
        
        # 保存用户数据（如果有变动）
        if success:
            self._save_user_data()
          # --- [集成] 解锁“自由的代价”并进行通用检查 ---
            await self.unlock_specific_achievement(event, user_id, 'market_2')
            await self.check_and_unlock_achievements(event, user_id)
        # 检查结果是否为图片路径
        if success:
            yield event.plain_result(message)
        else:
            yield event.plain_result(message)


    @filter.command("强制赎身")
    @filter.event_message_type(filter.EventMessageType.GROUP_MESSAGE)
    async def confirm_redeem_self(self, event: AstrMessageEvent):
        """确认不打工直接赎身指令"""
        # 检查是否@了机器人
        if not self.is_bot_mentioned(event):
            return
            
        # 获取群聊ID和用户信息
        group_id = event.get_group_id()
        user_id = event.get_sender_id()
        
        # 初始化用户数据
        user_data = self._get_user_in_group(group_id, user_id)
        
        # 处理赎身逻辑（确认模式）并传递群聊ID
        success, message = await self.market.process_redeem(
            event, group_id, user_id, user_data, confirm=True
        )
        
        # 保存用户数据（如果有变动）
        if success:
            self._save_user_data()
            
        if success:
            yield event.plain_result(message)
        else:
            yield event.plain_result(message)

    @filter.command("一键打工")
    @filter.event_message_type(filter.EventMessageType.GROUP_MESSAGE)
    async def one_click_work(self, event: AstrMessageEvent):
        """
        集成了购买、打工、出售的一体化指令。
        用法: @机器人 一键打工 @目标用户 <工作名称或编号>
        """
        if not self.is_bot_mentioned(event):
            return

        # 1. 解析参数和前置检查
        owner_id = event.get_sender_id()
        owner_name = event.get_sender_name()
        group_id = event.get_group_id()
        target_id = self.get_target_user_id(event)
        
        # 提取消息中的工作选项（数字或名称）
        job_choice = None
        message_parts = event.message_str.strip().split()
        for part in message_parts:
            # 跳过at标记和命令本身
            if part.startswith("[At:") or part == "一键打工":
                continue
            # 找到第一个非at的部分作为工作选项
            job_choice = part
            break

        if not target_id:
            yield event.plain_result("请@一位你要购买的用户。")
            return
            
        if not job_choice:
            yield event.plain_result("指令格式错误！\n正确格式: @机器人 一键打工 @目标用户 <工作名称或编号>")
            return

        job_list = self.market.get_sorted_jobs()
        job_name = None
        if job_choice.isdigit() and 0 < int(job_choice) <= len(job_list):
            job_name = job_list[int(job_choice) - 1]
        elif job_choice in job_list:
            job_name = job_choice

        if not job_name:
            yield event.plain_result(f"无效的工作选项: '{job_choice}'")
            return

        owner_data = self._get_user_in_group(group_id, owner_id)
        initial_points = owner_data['points']
        target_name = await self.market.get_user_name(event, target_id)

        # 初始化变量，防止异常时未定义
        work_msg = "打工失败"
        work_profit = 0
        work_success = False  # 初始化工作成功状态

        try:
            # 2. 购买阶段 (使用强制购买逻辑)
            buy_success, buy_msg, _ = await self.market.process_buy_member(
                event, group_id, owner_id, target_id, owner_data, confirm=True
            )
            if not buy_success:
                yield event.plain_result(buy_msg)
                return
            # 3. 打工阶段
            # 模拟一个临时的打工会话
            self.market.start_work_session(event.unified_msg_origin, group_id, owner_id, worker_id=target_id)
            work_success, work_msg, work_profit = await self.market.process_work_job(event, job_name, owner_data)
            # process_work_job 会自动结束会话

        except Exception as e:
            # 捕获所有异常，确保能够执行出售逻辑
            logger.error(f"一键打工过程中出错: {str(e)}")
            work_msg = f"打工过程中出错: {str(e)}"
            
        finally:
            # 4. 出售阶段 (无论打工成功与否都执行)
            try:
                sell_success, sell_msg = await self.market.process_sell_member(event, group_id, owner_id, target_id, owner_data)
                if not sell_success:
                    logger.warning(f"一键打工中出售失败: {sell_msg}")
            except Exception as e:
                logger.error(f"一键打工出售过程中出错: {str(e)}")
            
            # 5. 数据保存与成就检查
            self._save_user_data()
            
            # 检查是否应该解锁"赌神"成就
            if work_success and job_name == "偷窃苏特尔的宝库":
                # 仅在成功执行"偷窃苏特尔的宝库"时解锁"赌神"成就
                await self.unlock_specific_achievement(event, owner_id, 'work_1')
            
            # 进行其他通用成就检查
            await self.check_and_unlock_achievements(event, owner_id)

            # 6. 最终总结 - 简化格式
            net_profit = owner_data['points'] - initial_points
            final_message = f"@{owner_name}\n打工[{job_name}]: {work_msg}\n✨ 本次总净收益: {net_profit:+.1f} Astr币"
            
        yield event.plain_result(final_message)

    
    @filter.command("商城状态", alias={"Astr商城"})
    @filter.event_message_type(filter.EventMessageType.GROUP_MESSAGE)
    async def check_market_status(self, event: AstrMessageEvent):
        """查看商城状态指令"""
        # 检查是否@了机器人
        if not self.is_bot_mentioned(event):
            return
            
        # 获取群聊ID和用户信息
        group_id = event.get_group_id()
        user_id = event.get_sender_id()
        user_name = event.get_sender_name() or f"用户{user_id}"

        # --- [核心修改] 重构逻辑 ---
        # 1. 获取商城状态数据
        status_data = await self.market.get_market_status(event, group_id, user_id)
        if "error" in status_data:
            yield event.plain_result(status_data["error"])
            return

        # 2. 获取用户数据以读取称号
        user_data = self._get_user_in_group(group_id, user_id)
        current_title = user_data.get("current_title")

        # 3. 调用绘图函数
        avatar_url = f"http://q1.qlogo.cn/g?b=qq&nk={user_id}&s=640" if event.get_platform_name() == "aiocqhttp" else ""
        from ._generate_market import generate_market_card_pillow
        
        card_path = await generate_market_card_pillow(
            user_id=user_id,
            user_name=user_name,
            avatar_url=avatar_url,
            card_type='status',
            card_data=status_data,
            title=current_title # 传入称号
        )
        
        if card_path and os.path.exists(card_path):
            yield event.image_result(card_path)
        else:
            yield event.plain_result("状态卡片生成失败，请联系管理员。")
    
    @filter.command("抽奖")
    @filter.event_message_type(filter.EventMessageType.GROUP_MESSAGE)
    async def lottery(self, event: AstrMessageEvent):
        """抽奖指令（最终修正版）"""
        if not self.is_bot_mentioned(event):
            return
            
        group_id = event.get_group_id()
        user_id = event.get_sender_id()
        user_name = event.get_sender_name() or f"用户{user_id}"
        user_data = self._get_user_in_group(group_id, user_id)
        try:
            from .luck import process_lottery
            
            # --- [修改] 在调用process_lottery时传入shop_manager ---
            result_tuple = await process_lottery(
                event, group_id, user_id, user_name, user_data, self.shop_manager
            )
            
            # 1. 安全性检查：确保返回的是一个有效的元组
            if not isinstance(result_tuple, tuple) or len(result_tuple) != 3:
                logger.error(f"lottery: process_lottery返回了无效的格式: {result_tuple}")
                yield event.plain_result("抽奖功能出现了一点小问题，请稍后再试~")
                return

            # 2. 安全地解包
            message_list, updated_user_data, level = result_tuple

            if message_list:
                if updated_user_data:
                    self.user_data[str(group_id)][user_id] = updated_user_data
                    self._save_user_data()
                    
                    if level == '隐藏':
                        await self.unlock_specific_achievement(event, user_id, 'luck_2')
                    await self.check_and_unlock_achievements(event, user_id)
                
                # event.chain_result 期望一个列表，message_list现在是列表，所以这里是正确的
                yield event.chain_result(message_list)
            else:
                # 当process_lottery返回(None, None, None)时，说明有内部错误
                yield event.plain_result(f"抽奖失败，请稍后再试~")

        except Exception as e:
            # 捕获在 lottery 函数自身中可能发生的任何其他意外错误
            logger.error(f"lottery 指令处理器发生严重错误: {e}", exc_info=True)
            yield event.plain_result(f"抽奖功能出现严重错误，请联系管理员。")

    
    # 文件: main.py (修正 check_and_unlock_achievements 函数)

    async def check_and_unlock_achievements(self, event: AstrMessageEvent, user_id: str):
        """
        检查并解锁指定用户的所有可用成就。
        """
        group_id = event.get_group_id()
        if not group_id: return

        user_data = self._get_user_in_group(group_id, user_id)
        market_data = self.market._get_user_market_data(group_id, user_id)
        
        # --- [核心修改] 使用 setdefault 确保 'achievements' 键存在 ---
        unlocked_ids = user_data.setdefault("achievements", [])
        
        newly_unlocked = []

        for ach_id, ach_data in ACHIEVEMENTS.items():
            if ach_id in unlocked_ids or ach_id in newly_unlocked:
                continue

            try:
                if ach_data['unlock_condition'](u_data=user_data, m_data=market_data):
                    logger.info(f"用户 {user_id} 解锁成就: {ach_data['name']}")
                    
                    unlocked_ids.append(ach_id) # 直接向获取到的列表中添加
                    newly_unlocked.append(ach_id)

                    reward_points = ach_data.get('reward_points', 0)
                    reward_title = ach_data.get('reward_title', "")
                    user_data["points"] += reward_points

                    congrats_msg_list = [
                        At(qq=user_id),
                        Plain(f"\n🎉 成就解锁！🎉\n\n"),
                        Plain(f"【{ach_data['name']}】\n"),
                        Plain(f"“{ach_data['description']}”\n\n")
                    ]
                    if reward_points > 0:
                        congrats_msg_list.append(Plain(f"✨ 奖励: {reward_points} Astr币\n"))
                    if reward_title:
                        congrats_msg_list.append(Plain(f"👑 获得称号: 「{reward_title}」\n"))
                    
                    await event.send(MessageChain(congrats_msg_list))

            except Exception as e:
                logger.error(f"检查成就 {ach_id} 时出错: {e}", exc_info=True)

        if newly_unlocked:
            self._save_user_data()

    # 我们还需要一个解锁特定成就的辅助函数，用于彩蛋
    async def unlock_specific_achievement(self, event: AstrMessageEvent, user_id: str, ach_id: str):
        """直接解锁一个特定成就，用于事件触发型成就（如彩蛋）"""
        group_id = event.get_group_id()
        user_data = self._get_user_in_group(group_id, user_id)
        unlocked_ids = user_data.setdefault("achievements", [])
        if ach_id in user_data.get("achievements", []):
            return # 已解锁，无需操作

        ach_data = ACHIEVEMENTS.get(ach_id)
        if not ach_data:
            return
            
        logger.info(f"用户 {user_id} 解锁特定成就: {ach_data['name']}")
        unlocked_ids.append(ach_id) # [修正] 向获取到的安全列表添加成就
        user_data["points"] += ach_data.get('reward_points', 0)
        self._save_user_data()

        congrats_msg = [
            At(qq=user_id),
            Plain(f"\n🎉 成就解锁！🎉\n\n【{ach_data['name']}】\n“{ach_data['description']}”")
        ]
        if ach_data.get('reward_points', 0) > 0:
            congrats_msg.append(Plain(f"\n✨ 奖励: {ach_data['reward_points']} Astr币"))
        if ach_data.get('reward_title'):
            congrats_msg.append(Plain(f"\n👑 获得称号: 「{ach_data['reward_title']}」"))
            
        await event.send(MessageChain(congrats_msg))



    @filter.command("排行榜", alias={"ranking"})
    async def show_leaderboard(self, event: AstrMessageEvent, board_type: str = "财富"):
        """显示排行榜，支持'财富', '签到', '欧皇'三种类型"""
        # 1. 验证 board_type 是否有效
        allowed_types = ["财富", "签到", "欧皇"]
        if board_type not in allowed_types:
            yield event.plain_result(f"无效的排行榜类型！请输入: {', '.join(allowed_types)}")
            return

        # 2. 获取当前群聊的所有用户数据
        group_id = event.get_group_id()
        group_user_data = self._get_group_user_data(group_id)

        # 3. 根据 board_type 对用户列表进行排序
        sort_key_map = {
            "财富": "points",
            "签到": "streak_days",
            "欧皇": "high_tier_wins",
        }
        key_to_sort = sort_key_map[board_type]

        # 过滤掉没有相关数据的用户，并创建排序列表
        user_list_to_sort = [
            (uid, udata.get(key_to_sort, 0))
            for uid, udata in group_user_data.items()
            if udata.get(key_to_sort, 0) > 0 # 只排行有数据的用户
        ]
        
        sorted_users = sorted(user_list_to_sort, key=lambda item: item[1], reverse=True)

        # 4. 提取前10名和当前请求者的信息
        top_10_raw = sorted_users[:10]
        
        # 提取请求者信息
        requester_id = event.get_sender_id()
        requester_rank = -1
        requester_value = group_user_data.get(requester_id, {}).get(key_to_sort, 0)
        
        for i, (uid, val) in enumerate(sorted_users):
            if uid == requester_id:
                requester_rank = i + 1
                break
        
        # 准备传递给图片生成器的数据
        top_users_data = []
        for user_id, value in top_10_raw:
            user_name = await self.market.get_user_name(event, user_id)
            top_users_data.append({'id': user_id, 'name': user_name, 'value': value})
            
        requester_data_for_img = {
            'rank': requester_rank if requester_rank != -1 else 'N/A',
            'name': event.get_sender_name() or f"用户{requester_id}",
            'value': requester_value
        }

        # 5. 调用 _generate_leaderboard.generate_leaderboard_image 生成图片
        try:
            image_path = await generate_leaderboard_image(
                board_type=board_type,
                top_users=top_users_data,
                requester_data=requester_data_for_img
            )
            
            # 6. 使用 yield event.image_result(image_path) 发送图片
            if image_path and os.path.exists(image_path):
                yield event.image_result(image_path)
            else:
                yield event.plain_result(f"{board_type}榜生成失败，请稍后再试。")
        except Exception as e:
            logger.error(f"生成排行榜时出现严重错误: {e}", exc_info=True)
            yield event.plain_result("生成排行榜时出现内部错误，请联系管理员。")


    @filter.command("我的成就", alias={"achievements"})
    async def show_my_achievements(self, event: AstrMessageEvent):
        """显示用户的个人成就墙"""
        # 1. 获取当前用户的 user_id 和 user_data
        group_id = event.get_group_id()
        user_id = event.get_sender_id()
        user_name = event.get_sender_name() or f"用户{user_id}"
        user_data = self._get_user_in_group(group_id, user_id)

        # 2. 从 achievements.py 中导入所有成就定义 (已在文件顶部导入)
        unlocked_ids = user_data.get("achievements", [])

        # 3. 调用 _generate_achievements.generate_achievements_image 生成图片
        try:
            image_path = await generate_achievements_image(
                user_name=user_name,
                unlocked_ids=unlocked_ids,
                all_achievements=ACHIEVEMENTS
            )
            
            # 4. 使用 yield event.image_result(image_path) 发送图片
            if image_path and os.path.exists(image_path):
                yield event.image_result(image_path)
            else:
                yield event.plain_result("成就墙生成失败，请稍后再试。")
        except Exception as e:
            logger.error(f"生成成就墙时出现严重错误: {e}", exc_info=True)
   
    # 文件: feifeisupermarket/main.py (新增函数)

    @filter.command("我的称号")
    @filter.event_message_type(filter.EventMessageType.GROUP_MESSAGE)
    async def list_my_titles(self, event: AstrMessageEvent):
        """列出用户已获得的所有称号"""
        if not self.is_bot_mentioned(event): return
        
        group_id = event.get_group_id()
        user_id = event.get_sender_id()
        user_data = self._get_user_in_group(group_id, user_id)
        
        unlocked_ids = user_data.get("achievements", [])
        current_title = user_data.get("current_title", "")
        
        available_titles = []
        for ach_id in unlocked_ids:
            title = ACHIEVEMENTS.get(ach_id, {}).get('reward_title')
            if title and title not in available_titles:
                available_titles.append(title)
        
        if not available_titles:
            yield event.plain_result("你尚未获得任何称号。")
            return
            
        msg = f"@{event.get_sender_name()} 你拥有的称号列表：\n" + "-"*20 + "\n"
        for title in available_titles:
            if title == current_title:
                msg += f"▶ 「{title}」(已佩戴)\n"
            else:
                msg += f"▷ 「{title}」\n"
        
        msg += "-"*20 + "\n使用指令“@机器人 佩戴称号 <称号名>”来装备你的称号吧！"
        yield event.plain_result(msg)

    @filter.command("佩戴称号")
    @filter.event_message_type(filter.EventMessageType.GROUP_MESSAGE)
    async def equip_title(self, event: AstrMessageEvent, *, title_to_equip: str):
        """佩戴一个已获得的称号"""
        if not self.is_bot_mentioned(event): return

        title_to_equip = title_to_equip.strip()
        if not title_to_equip:
            yield event.plain_result("请在指令后输入要佩戴的称号名称。")
            return

        group_id = event.get_group_id()
        user_id = event.get_sender_id()
        user_data = self._get_user_in_group(group_id, user_id)
        
        unlocked_ids = user_data.get("achievements", [])
        available_titles = [ACHIEVEMENTS.get(ach_id, {}).get('reward_title') for ach_id in unlocked_ids if ACHIEVEMENTS.get(ach_id, {}).get('reward_title')]

        if title_to_equip in available_titles:
            user_data["current_title"] = title_to_equip
            self._save_user_data()
            yield event.plain_result(f"称号已成功更换为「{title_to_equip}」！")
        else:
            yield event.plain_result("你尚未获得该称号或称号不存在。")

    @filter.command("卸下称号")
    @filter.event_message_type(filter.EventMessageType.GROUP_MESSAGE)
    async def unequip_title(self, event: AstrMessageEvent):
        """卸下当前佩戴的称号"""
        if not self.is_bot_mentioned(event): return

        group_id = event.get_group_id()
        user_id = event.get_sender_id()
        user_data = self._get_user_in_group(group_id, user_id)
        
        if user_data.get("current_title"):
            user_data["current_title"] = ""
            self._save_user_data()
            yield event.plain_result("已成功卸下称号。")
        else:
            yield event.plain_result("你当前没有佩戴任何称号。")    


    @filter.command("赠送", alias={"转账", "送"})
    @filter.event_message_type(filter.EventMessageType.GROUP_MESSAGE)
    async def gift_points(self, event: AstrMessageEvent):
        """赠送Astr币给其他用户"""
        if not self.is_bot_mentioned(event):
            return

        # 1. 解析指令
        sender_id = event.get_sender_id()
        sender_name = event.get_sender_name() or f"用户{sender_id}"
        group_id = event.get_group_id()

        target_id = self.get_target_user_id(event)
        
        # 提取消息中的数字作为金额
        amount = None
        for part in event.message_str.strip().split():
            if part.isdigit():
                amount = int(part)
                break
        
        # 2. 条件验证
        if not target_id:
            yield event.plain_result(f"{sender_name}，请@一位你要赠送的群友。")
            return

        if amount is None:
            yield event.plain_result(f"{sender_name}，请输入要赠送的金额。")
            return

        if amount <= 0:
            yield event.plain_result(f"{sender_name}，赠送金额必须是大于0的整数。")
            return
            
        if sender_id == target_id:
            yield event.plain_result("不能给自己赠送Astr币哦~")
            return

        # 获取用户数据
        sender_data = self._get_user_in_group(group_id, sender_id)
        if sender_data["points"] < amount:
            yield event.plain_result(f"{sender_name}，你的Astr币不足，当前余额: {sender_data['points']:.2f}。")
            return

        # 3. 执行交易
        target_data = self._get_user_in_group(group_id, target_id)
        target_name = await self.market.get_user_name(event, target_id)
        
        # 记录旧余额用于显示
        old_sender_balance = sender_data["points"]
        old_target_balance = target_data["points"]
        
        # 执行转账
        sender_data["points"] -= amount
        target_data["points"] += amount
        
        # 更新赠送统计数据
        from datetime import datetime
        today = datetime.now().strftime("%Y-%m-%d")
        
        # 更新累计赠送金额
        sender_data["total_gifted"] = sender_data.get("total_gifted", 0) + amount
        
        # 更新赠送次数
        sender_data["gift_count"] = sender_data.get("gift_count", 0) + 1
        
        # 更新连续赠送天数
        last_gift_date = sender_data.get("last_gift_date", "")
        if last_gift_date == "":
            # 首次赠送
            sender_data["consecutive_gift_days"] = 1
        elif last_gift_date != today:
            from datetime import datetime
            last_date = datetime.strptime(last_gift_date, "%Y-%m-%d")
            today_date = datetime.strptime(today, "%Y-%m-%d")
            day_diff = (today_date - last_date).days
            
            if day_diff == 1:
                # 连续赠送
                sender_data["consecutive_gift_days"] = sender_data.get("consecutive_gift_days", 0) + 1
            else:
                # 中断连续
                sender_data["consecutive_gift_days"] = 1
        
        # 更新最后赠送日期
        sender_data["last_gift_date"] = today
        
        # 4. 保存数据
        self._save_user_data()
        
        # 5. 检查成就
        # a. 对单次赠送成就进行事件触发
        if amount >= 100:
            await self.unlock_specific_achievement(event, sender_id, 'big_gift')
        
        # b. 对累计赠送成就进行通用检查
        await self.check_and_unlock_achievements(event, sender_id)
        
        # 6. 生成并发送成功反馈
        message = (
            f"✨ 赠送成功！\n"
            f"{sender_name} 向 {target_name} 赠送了 {amount} Astr币！\n"
        )
        
        yield event.plain_result(message)

    @filter.command("买入")
    async def buy_item(self, event: AstrMessageEvent, item_id: str = None, quantity: int = 1):
        """购买物品指令"""
        if not self.is_bot_mentioned(event):
            return
        
        # 检查 item_id 是否被提供
        if item_id is None:
            yield event.plain_result("请输入要购买的商品ID。用法: @机器人 买入 <商品ID> [数量]")
            return

        # 获取用户信息
        group_id = event.get_group_id()
        user_id = event.get_sender_id()
        user_data = self._get_user_in_group(group_id, user_id)
        
        # 检查物品ID是否存在
        item_exists = False
        item_category = None
        
        # 使用 self.shop_manager.items_definition 来进行查找
        if item_id in self.shop_manager.items_definition:
            item_exists = True
            item_category = self.shop_manager.items_definition[item_id]["category"]
        
        if not item_exists:
            yield event.plain_result(f"商品ID '{item_id}' 不存在，请查看商店后再购买。")
            return
        
        # 执行购买逻辑
        success, message = await self.shop_manager.buy_item(
            event, user_data, item_category, item_id, quantity
        )
        
        if success:
            self._save_user_data()  # 保存用户数据（更新Astr币）
            
        # 返回购买结果
        yield event.plain_result(message)

    @filter.command("使用")
    async def use_item(self, event: AstrMessageEvent, item_name: str, quantity: int = 1):
        """使用物品指令，支持批量使用"""
        if not self.is_bot_mentioned(event):
            return
            
        # 获取用户信息
        group_id = event.get_group_id()
        user_id = event.get_sender_id()
        user_data = self._get_user_in_group(group_id, user_id)
        
        # 查找与名称匹配的物品ID
        item_id = None
        item_category = None
        for category, items in SHOP_DATA.items():
            for id, data in items.items():
                if data['name'] == item_name:
                    item_id = id
                    item_category = category
                    break
            if item_id:
                break
        
        if not item_id:
            yield event.plain_result(f"物品 '{item_name}' 不存在，请检查物品名称是否正确。")
            return
        
        # 检查数量参数
        if quantity <= 0:
            yield event.plain_result("使用数量必须大于0。")
            return
        
        # --- [修改] 优化批量使用和消息返回的逻辑 ---
        total_success = 0
        failure_messages = []
        last_success_message = "" # 用于存储最后一次成功的详细消息

        for i in range(quantity):
            success, message = await self.shop_manager.use_item(
                event, user_data, item_id
            )
            
            if success:
                total_success += 1
                last_success_message = message # 捕获并覆盖为最新的成功消息
            else:
                # 如果失败（比如物品不足），停止继续使用
                failure_messages.append(f"第{i+1}次使用失败：{message}")
                break
        
        if total_success > 0:
            self._save_user_data()  # 保存用户数据（更新buff和体力状态）
            
            # 如果只使用了一个，直接显示该次的详细结果
            if total_success == 1:
                yield event.plain_result(last_success_message)
            else:
                # 如果使用了多个，显示一个总结，并附上最后一次的详细结果
                # last_success_message 中已经包含了最终的体力值，所以这是准确的
                final_message = f"✅ 连续成功使用了 {total_success} 个 {item_name}！\n\n" + \
                                f"最后一次效果：\n{last_success_message.split('✅ ')[-1]}" # 去掉重复的成功提示
                yield event.plain_result(final_message)
        else:
            # 如果一次都未成功
            error_reason = failure_messages[0] if failure_messages else "未知错误"
            yield event.plain_result(f"使用 {item_name} 失败：\n{error_reason}")

    @filter.command("一键使用")
    async def batch_use_item(self, event: AstrMessageEvent, item_name: str, quantity: int = 1):
        """一键使用指令：购买并使用物品（支持道具和食物）"""
        if not self.is_bot_mentioned(event):
            return
            
        logger.info(f"一键使用命令被调用: 物品={item_name}, 数量={quantity}")
        
        # ... [前面的查找物品和购买逻辑保持不变] ...
        group_id = event.get_group_id()
        user_id = event.get_sender_id()
        user_data = self._get_user_in_group(group_id, user_id)
        
        item_id = None
        item_category = None
        
        for cat, items in SHOP_DATA.items():
            if cat in ['道具', '食物']:
                for id, data in items.items():
                    if data['name'] == item_name:
                        item_id, item_category = id, cat
                        break
            if item_id: break
        
        if not item_id:
             if item_name in SHOP_DATA.get('道具', {}):
                item_id, item_category = item_name, '道具'
                item_name = SHOP_DATA['道具'][item_id]['name']
             elif item_name in SHOP_DATA.get('食物', {}):
                item_id, item_category = item_name, '食物'
                item_name = SHOP_DATA['食物'][item_id]['name']

        if not item_id or not item_category:
            yield event.plain_result(f"物品 '{item_name}' 不存在或不支持一键使用。")
            return

        if quantity <= 0:
            yield event.plain_result("使用数量必须大于0。")
            return
            
        user_bag = self.shop_manager.get_user_bag(group_id, user_id)
        if item_category not in user_bag: user_bag[item_category] = {}
        current_quantity = user_bag[item_category].get(item_id, 0)
        need_to_buy = max(0, quantity - current_quantity)
        
        logger.info(f"用户当前拥有 {current_quantity} 个 {item_name}，需要购买 {need_to_buy} 个")

        if need_to_buy > 0:
            total_items_in_bag = sum(sum(c.values()) for c in user_bag.values())
            if total_items_in_bag + need_to_buy > 100:
                yield event.plain_result(f"背包容量不足！")
                return
            if user_bag[item_category].get(item_id, 0) + need_to_buy > 10:
                yield event.plain_result(f"购买失败！【{item_name}】最多只能拥有10个。")
                return
            
            buy_success, buy_message = await self.shop_manager.buy_item(
                event, user_data, item_category, item_id, need_to_buy
            )
            if not buy_success:
                yield event.plain_result(f"购买失败：{buy_message}")
                return
            else:
                logger.info(f"成功购买了 {need_to_buy} 个 {item_name}")

        # --- [修改] 优化批量使用和消息返回的逻辑 ---
        total_success = 0
        failure_messages = []
        last_success_message = ""

        for i in range(quantity):
            success, message = await self.shop_manager.use_item(
                event, user_data, item_id
            )
            
            if success:
                total_success += 1
                last_success_message = message
                logger.info(f"第 {i+1} 次使用 {item_name} 成功")
            else:
                failure_messages.append(message)
                logger.info(f"第 {i+1} 次使用 {item_name} 失败: {message}")
                break
        
        if total_success > 0:
            self._save_user_data()  # 保存用户数据
            
            purchase_info = ""
            if need_to_buy > 0:
                purchase_info = f"成功购买 {need_to_buy} 个 {item_name}，"

            # 构造包含详细信息的最终消息
            if total_success == 1:
                final_message = f"{purchase_info}并成功使用！\n\n{last_success_message}"
            else:
                final_message = f"{purchase_info}并连续成功使用了 {total_success} 个！\n\n" + \
                                f"最后一次效果：\n{last_success_message.split('✅ ')[-1]}"

            yield event.plain_result(final_message.strip())
        else:
            error_reason = failure_messages[0] if failure_messages else "未知错误"
            yield event.plain_result(f"使用 {item_name} 失败：\n{error_reason}")

    @filter.command("我的状态")
    @filter.event_message_type(filter.EventMessageType.GROUP_MESSAGE)
    async def check_buffs(self, event: AstrMessageEvent):
        """查询用户当前的buff状态"""
        if not self.is_bot_mentioned(event):
            return
            
        # 获取用户信息
        group_id = event.get_group_id()
        user_id = event.get_sender_id()
        user_name = event.get_sender_name() or f"用户{user_id}"
        
        # 获取用户数据
        user_data = self._get_user_in_group(group_id, user_id)
        buffs = user_data.get("buffs", {})
        
        # 获取buff描述 - 添加新的冒险系统道具效果
        buff_descriptions = {
            "work_guarantee_success": "打工必定成功",
            "work_no_penalty": "打工失败不扣币",
            "work_reward_boost": "打工奖励提升",
            "lottery_min_3star": "抽奖至少3星",
            "lottery_double_reward": "抽奖奖励翻倍",
            "lottery_best_of_two": "抽奖双抽取最佳",
            "adventure_negate_crisis": "冒险危机保护",
            "adventure_rare_boost": "稀有奇遇提升"
        }
        
        # 构建消息
        active_buffs = []
        for buff_name, count in buffs.items():
            if count > 0:
                desc = buff_descriptions.get(buff_name, buff_name)
                active_buffs.append(f"【{desc}】× {count}")
        
        if active_buffs:
            buffs_text = "\n".join(active_buffs)
            yield event.plain_result(f"{user_name} 当前激活的效果：\n{buffs_text}")
        else:
            yield event.plain_result(f"{user_name} 当前没有激活的道具效果。")


    @filter.command("我的背包")
    async def show_backpack(self, event: AstrMessageEvent):
        """查看自己的背包物品"""
        if not self.is_bot_mentioned(event):
            return
            
        group_id = event.get_group_id()
        user_id = event.get_sender_id()
        
        user_data = self._get_user_in_group(group_id, user_id)
        user_bag = self.shop_manager.get_user_bag(group_id, user_id)
        
        try:
            # 修改为传递体力值参数
            image_path = await generate_backpack_card(
                user_bag, 
                user_data['points'], 
                stamina=user_data.get('stamina', 0),
                max_stamina=user_data.get('max_stamina', 100)
            )
            if image_path:
                yield event.image_result(image_path)
            else:
                raise ValueError("Image path was None")
        except Exception as e:
            # 图片失败后，回退为纯文本
            logger.error(f"生成背包卡片失败，回退到文本模式: {e}")
            
            backpack_text = f"我的背包:\n----------------\n"
            backpack_text += f"💰 Astr币: {user_data['points']}\n"
            backpack_text += f"⚡ 体力值: {user_data.get('stamina', 0)}/{user_data.get('max_stamina', 100)}\n\n"
            
            total_items = 0
            for category, items in user_bag.items():
                if items:
                    backpack_text += f"【{category}】\n"
                    for item_id, quantity in items.items():
                        if quantity <= 0:
                            continue
                        item_info = SHOP_DATA.get(category, {}).get(item_id)
                        if item_info:
                            item_name = item_info.get('name', '未知物品')
                            backpack_text += f"- {item_name} x{quantity}\n"
                            total_items += quantity
            
            if total_items == 0:
                backpack_text += "背包空空如也~\n"

            yield event.plain_result(backpack_text)

    @filter.command("商店")
    async def show_shop(self, event: AstrMessageEvent, category: str = "道具"):
        """显示指定类别的商店物品，默认显示道具类别"""
        if not self.is_bot_mentioned(event):
            return
        
        # 验证类别是否有效
        if category not in SHOP_DATA:
            yield event.plain_result("无效的商店类别！请选择：道具、食物、礼物")
            return
        
        # 获取用户数据（用于显示Astr币数量）
        group_id = event.get_group_id()
        user_id = event.get_sender_id()
        user_data = self._get_user_in_group(group_id, user_id)
        
        try:
            # 调用商店卡片生成函数但不传递头像URL
            image_path = await generate_shop_card(category, user_data['points'])
            if image_path:
                yield event.image_result(image_path)
            else:
                raise ValueError("Image path was None")
        except Exception as e:
            logger.error(f"生成商店卡片指令失败: {e}")
            yield event.plain_result(f"商店'{category}'分类卡片生成失败，请联系管理员。")

    # 添加冒险指令
    @filter.command("冒险")
    async def adventure(self, event: AstrMessageEvent, times: int = 1):
        """冒险指令，每次消耗20体力"""
        if not self.is_bot_mentioned(event):
            return
            
        # 获取用户信息
        group_id = event.get_group_id()
        user_id = event.get_sender_id()
        user_data = self._get_user_in_group(group_id, user_id)
        
        # 检查参数
        if times <= 0:
            yield event.plain_result("冒险次数必须大于0。")
            return
        
        if times > 10:
            yield event.plain_result("一次最多只能进行10次冒险，以免疲劳过度哦~")
            return
        
        # 注意：不再预先检查体力是否足够，而是在run_adventures中处理
        
        # 执行冒险
        results = await self.adventure_manager.run_adventures(
            event=event,
            user_data=user_data,
            shop_manager=self.shop_manager,
            times=times
        )
        
        if not results["success"]:
            yield event.plain_result(results["message"])
            return
        
        if "achievements_to_unlock" in results:
            for ach_id in results["achievements_to_unlock"]:
                await self.unlock_specific_achievement(event, user_id, ach_id)        
        
        # 保存用户数据
        self._save_user_data()
        
        try:
            # 生成冒险报告卡片
            from ._generate_adventure import generate_adventure_report_card
            image_path = await generate_adventure_report_card(results)
            
            if image_path:
                yield event.image_result(image_path)
            else:
                raise ValueError("Failed to generate adventure report card")
        except Exception as e:
            logger.error(f"生成冒险报告卡片失败，回退到文本模式: {e}", exc_info=True)
            
            # 回退到文本模式
            report_text = "【冒险报告】\n"
            report_text += f"冒险次数: {results['adventure_times']}次\n"
            report_text += f"体力消耗: {results['stamina_cost']} ({results['stamina_before']} → {results['stamina_after']})\n"
            
            points_change = results['total_points_gain']
            if points_change > 0:
                report_text += f"Astr币: +{points_change} ({results['points_before']} → {results['points_after']})\n"
            elif points_change < 0:
                report_text += f"Astr币: {points_change} ({results['points_before']} → {results['points_after']})\n"
            else:
                report_text += f"Astr币: 无变化 ({results['points_before']})\n"
            
            if results["items_gained"]:
                report_text += "获得物品:\n"
                for item in results["items_gained"]:
                    report_text += f"- {item['name']} ({item['category']})\n"

            if "auto_used_items" in results and results["auto_used_items"]:
                report_text += "\n自动使用物品(超出上限):\n"
                for item in results["auto_used_items"]:
                    report_text += f"- {item['name']}: {item['message']}\n"

            report_text += "\n【冒险事件】\n"
            for i, event in enumerate(results["events"]):
                report_text += f"{i+1}. {event['name']}: {event['description']}\n"
                
                effects = []
                for effect_type, effect_desc in event.get("effects", {}).items():
                    # 扩展排除的字段列表
                    if effect_type not in ["item_id", "return", "achievement", "title"] and effect_desc:
                        effects.append(effect_desc)

                if effects:
                    report_text += f"   效果: {', '.join(effects)}\n"
            
            if "new_achievement" in results:
                report_text += f"\n🏆 新成就解锁: {results['new_achievement']}"
            
            yield event.plain_result(report_text)

    @filter.command("超级冒险")
    async def super_adventure(self, event: AstrMessageEvent):
        """超级冒险指令，使用所有体力进行冒险"""
        if not self.is_bot_mentioned(event):
            return
            
        # 获取用户信息
        group_id = event.get_group_id()
        user_id = event.get_sender_id()
        user_data = self._get_user_in_group(group_id, user_id)
        
        # 检查体力值
        stamina = user_data.get("stamina", 0)
        if stamina < 20:
            yield event.plain_result("体力不足，无法进行冒险。")
            return
        
        # 计算最大冒险次数（不再一次性扣除体力）
        max_times = min(stamina // 20, 10)  # 最多10次
        
        yield event.plain_result(f"将消耗{max_times * 20}点体力进行{max_times}次冒险。")
        
        # 执行冒险
        results = await self.adventure_manager.run_adventures(
            event=event,
            user_data=user_data,
            shop_manager=self.shop_manager,
            times=max_times
        )
        
        if not results["success"]:
            yield event.plain_result(results["message"])
            return
        
        if "achievements_to_unlock" in results:
            for ach_id in results["achievements_to_unlock"]:
                await self.unlock_specific_achievement(event, user_id, ach_id)        
        # 保存用户数据
        self._save_user_data()
        
        try:
            # 生成冒险报告卡片
            from ._generate_adventure import generate_adventure_report_card
            image_path = await generate_adventure_report_card(results)
            
            if image_path:
                yield event.image_result(image_path)
            else:
                raise ValueError("Failed to generate adventure report card")
        except Exception as e:
            logger.error(f"生成冒险报告卡片失败，回退到文本模式: {e}", exc_info=True)
            
            # 回退到文本模式
            report_text = "【超级冒险报告】\n"
            report_text += f"冒险次数: {results['adventure_times']}次\n"
            report_text += f"体力消耗: {results['stamina_cost']} ({results['stamina_before']} → {results['stamina_after']})\n"
            
            points_change = results['total_points_gain']
            if points_change > 0:
                report_text += f"Astr币: +{points_change} ({results['points_before']} → {results['points_after']})\n"
            elif points_change < 0:
                report_text += f"Astr币: {points_change} ({results['points_before']} → {results['points_after']})\n"
            else:
                report_text += f"Astr币: 无变化 ({results['points_before']})\n"
            
            if results["items_gained"]:
                report_text += "获得物品:\n"
                for item in results["items_gained"]:
                    report_text += f"- {item['name']} ({item['category']})\n"
            # 在"获得物品"部分之后添加自动使用物品的显示
            if "auto_used_items" in results and results["auto_used_items"]:
                report_text += "\n自动使用物品(超出上限):\n"
                for item in results["auto_used_items"]:
                    report_text += f"- {item['name']}: {item['message']}\n"

            report_text += "\n【冒险事件】\n"
            for i, event in enumerate(results["events"]):
                report_text += f"{i+1}. {event['name']}: {event['description']}\n"
                
                effects = []
                for effect_type, effect_desc in event.get("effects", {}).items():
                    # 扩展排除的字段列表
                    if effect_type not in ["item_id", "return", "achievement", "title"] and effect_desc:
                        effects.append(effect_desc)

                if effects:
                    report_text += f"   效果: {', '.join(effects)}\n"
            
            if "new_achievement" in results:
                report_text += f"\n🏆 新成就解锁: {results['new_achievement']}"
            
            if "message" in results and "中断" in results["message"]:
                report_text += f"\n\n⚠️ {results['message']}"
            
            yield event.plain_result(report_text)

    @filter.command("赠礼")
    @filter.event_message_type(filter.EventMessageType.GROUP_MESSAGE)
    async def gift_item(self, event: AstrMessageEvent, *, text: str = ""):
        """赠送礼物给其他用户，提升对方对你的好感度"""
        if not self.is_bot_mentioned(event):
            return

        # 1. 简化的参数解析逻辑 - 只接受礼物名称，不处理数量
        args = text.strip().split()
        if not args:
            yield event.plain_result("请指定礼物名称。用法：赠礼 <礼物名> @用户")
            return
            
        # 所有文本内容都视为物品名称
        item_name = text.strip()
        quantity = 1  # 固定为1，不再接受数量参数
        
        sender_id = event.get_sender_id()
        sender_name = event.get_sender_name() or f"用户{sender_id}"
        group_id = event.get_group_id()
        
        target_id = self.get_target_user_id(event)
        if not target_id:
            yield event.plain_result(f"{sender_name}，请@一位你要赠送礼物的用户。")
            return
        
        # 2. 查找礼物ID
        item_id = None
        item_category = None
        favorability_gain = 0
        
        # 在礼物类别中查找
        for id, data in SHOP_DATA.get("礼物", {}).items():
            if data["name"] == item_name:
                item_id = id
                item_category = "礼物"
                favorability_gain = data.get("effect", {}).get("favorability_gain", 0)
                break
        
        if not item_id:
            yield event.plain_result(f"物品 '{item_name}' 不存在或不是礼物，请检查名称是否正确。")
            return
        
        # 3. 检查是否为特殊关系礼物
        for relation, relation_item in SPECIAL_RELATION_ITEMS.items():
            if relation_item == item_name:
                yield event.plain_result(f"'{item_name}' 是特殊关系礼物，请使用 '缔结 {relation} @用户' 来赠送。")
                return
        
        # 4. 检查背包中是否有足够的物品
        user_bag = self.shop_manager.get_user_bag(group_id, sender_id)
        if item_category not in user_bag or item_id not in user_bag[item_category] or user_bag[item_category][item_id] < quantity:
            current_count = user_bag.get(item_category, {}).get(item_id, 0)
            yield event.plain_result(f"{sender_name}，你的背包中没有足够的 '{item_name}'。需要{quantity}个，拥有{current_count}个。")
            return
        
        # 5. 获取目标用户名称
        target_name = await self.market.get_user_name(event, target_id) or f"用户{target_id}"
        
        # 6. 消耗物品
        success, consume_msg = await self.shop_manager.consume_item(group_id, sender_id, item_id, quantity)
        if not success:
            yield event.plain_result(f"赠送失败：{consume_msg}")
            return
        
        # 7. 处理好感度增加
        old_favorability = self.social_manager.get_favorability(group_id, target_id, sender_id)
        
        success, gift_msg = await self.social_manager.process_gift(
            event, group_id, sender_id, target_id, item_id, favorability_gain
        )
        
        new_favorability = self.social_manager.get_favorability(group_id, target_id, sender_id)
        actual_gain = new_favorability - old_favorability
        
        # 8. 检查社交达人成就
        if success and actual_gain > 0:
            if hasattr(self.social_manager, 'check_social_master_achievement'):
                if self.social_manager.check_social_master_achievement(group_id, target_id):
                    await self.unlock_specific_achievement(event, target_id, 'social_master')
        
        # 9. 返回结果
        result_text = f"{sender_name} 将 '{item_name}' 送给了 {target_name}！"
        
        if actual_gain > 0:
            old_level = self.social_manager._get_relation_level(old_favorability)
            new_level = self.social_manager._get_relation_level(new_favorability)
            
            if old_level != new_level:
                result_text += f"\n好感度 +{actual_gain} ({old_favorability} → {new_favorability})，关系升级为【{new_level}】！"
            else:
                result_text += f"\n好感度 +{actual_gain} ({old_favorability} → {new_favorability})，当前关系：【{new_level}】"
        else:
            result_text += "\n对方的好感度已达上限，无法继续提升。"
        
        yield event.plain_result(result_text)


    # 修复约会指令的图片发送问题
    @filter.command("约会")
    @filter.event_message_type(filter.EventMessageType.GROUP_MESSAGE)
    async def start_date(self, event: AstrMessageEvent):
        """邀请另一位用户进行约会，影响双方好感度"""
        # 检查是否@了机器人
        if not self.is_bot_mentioned(event):
            return
            
        # 1. 解析指令
        initiator_id = event.get_sender_id()
        initiator_name = event.get_sender_name() or f"用户{initiator_id}"
        group_id = event.get_group_id()
        
        target_id = self.get_target_user_id(event)
        if not target_id:
            yield event.plain_result(f"{initiator_name}，请@一位你要邀请约会的用户。")
            return
        
        # 2. 获取目标用户名称
        target_name = await self.market.get_user_name(event, target_id) or f"用户{target_id}"
        
        # 3. 发起约会邀请
        success, msg = await self.social_manager.initiate_date(
            event, group_id, initiator_id, target_id
        )
        
        if not success:
            yield event.plain_result(msg)
            return
        
        # 4. 等待对方回应
        yield event.plain_result(f"{initiator_name} 向 {target_name} 发出了约会邀请！\n{target_name}，请在60秒内回复‘同意’接受邀请。")
        
        # 设置会话控制器
        try:
            from astrbot.core.utils.session_waiter import session_waiter, SessionController
            
            @session_waiter(timeout=60, record_history_chains=False)
            async def date_invitation_waiter(controller: SessionController, response_event: AstrMessageEvent):
                # 检查回复者是否为目标用户
                if response_event.get_sender_id() != target_id:
                    return
                    
                # 检查回复内容是否为"同意"
                response_msg = response_event.message_str.strip()
                if response_msg == "同意":
                    # 获取头像URL
                    initiator_avatar = f"http://q1.qlogo.cn/g?b=qq&nk={initiator_id}&s=640"
                    target_avatar = f"http://q1.qlogo.cn/g?b=qq&nk={target_id}&s=640"
                    
                    # 执行约会流程
                    date_results = await self.social_manager.run_date(
                        group_id, initiator_id, target_id, initiator_name, target_name
                    )
                    
                    # 生成约会报告卡片
                    from ._generate_social import generate_date_report_card
                    card_path = await generate_date_report_card(
                        initiator_id, initiator_name, initiator_avatar,
                        target_id, target_name, target_avatar,
                        date_results
                    )
                    
                    # 创建一个空的结果对象
                    result = response_event.make_result()

                    if card_path and os.path.exists(card_path):
                        # 正确的发送图片方式：构建一个包含Image组件的chain
                        import astrbot.api.message_components as Comp
                        result.chain = [Comp.Image.fromFileSystem(card_path)]
                    else:
                        # 图片生成失败，回退到文本模式
                        logger.warning("约会报告卡片生成失败或路径不存在，回退到文本模式。")
                        a_fav_change = date_results["user_a"]["favorability_change"]
                        b_fav_change = date_results["user_b"]["favorability_change"]
                        
                        events_text = "\n".join([f"· {event['description']}" for event in date_results.get("events", [])])
                        
                        report_text = (
                            f"📝 约会报告 📝\n\n"
                            f"约会时间: {date_results['date_time']}\n"
                            f"你们一起经历了：\n{events_text}\n\n"
                            f"最终好感度变化：\n"
                            f"· {initiator_name} 对 {target_name}: {a_fav_change:+d}\n"
                            f"· {target_name} 对 {initiator_name}: {b_fav_change:+d}"
                        )
                        
                        # 正确的发送纯文本方式：构建一个包含Plain组件的chain
                        import astrbot.api.message_components as Comp
                        result.chain = [Comp.Plain(report_text)]
                    
                    # 使用 event.send() 发送构建好的消息结果
                    await response_event.send(result)

                else:
                    # 拒绝约会
                    reject_result = response_event.make_result()
                    import astrbot.api.message_components as Comp
                    reject_result.chain = [Comp.Plain(f"{target_name} 拒绝了 {initiator_name} 的约会邀请。")]
                    await response_event.send(reject_result)
                    
                # 无论同意或拒绝，都结束会话
                self.social_manager.end_date_session(event.unified_msg_origin)

                    
                # 检查约会新手成就
                for user_id in [initiator_id, target_id]:
                    # 获取用户数据
                    user_data = self._get_user_in_group(group_id, user_id)
                    # 检查是否完成过约会
                    user_dates = user_data.get("date_count", 0)
                    if user_dates == 0:  # 首次约会
                        # 更新约会次数
                        user_data["date_count"] = 1
                        # 解锁成就
                        await self.unlock_specific_achievement(response_event, user_id, 'social_date_beginner')
                    else:
                        # 增加约会次数
                        user_data["date_count"] = user_dates + 1
                    
                    # 保存用户数据
                    self._save_user_data()
                        
                    # 检查社交达人成就
                    if self.social_manager.check_social_master_achievement(group_id, user_id):
                        await self.unlock_specific_achievement(response_event, user_id, 'social_master')                
                # 停止会话控制器
                controller.stop()
                
            try:
                await date_invitation_waiter(event)
            except TimeoutError:
                # 超时处理
                yield event.plain_result(f"{target_name} 没有回应约会邀请，邀请已过期。")
                
                # 结束约会会话
                self.social_manager.end_date_session(event.unified_msg_origin)
                
        except Exception as e:
            logger.error(f"约会邀请处理出错: {e}", exc_info=True)
            yield event.plain_result("约会邀请处理出现错误，请稍后再试。")



    # 添加关系指令
    @filter.command("关系")
    @filter.event_message_type(filter.EventMessageType.GROUP_MESSAGE)
    async def check_relationship(self, event: AstrMessageEvent):
        """查看与指定用户的关系"""
        # 检查是否@了机器人
        if not self.is_bot_mentioned(event):
            return

        # 1. 解析指令
        user_id = event.get_sender_id()
        user_name = event.get_sender_name() or f"用户{user_id}"
        group_id = event.get_group_id()

        target_id = self.get_target_user_id(event)
        if not target_id:
            yield event.plain_result(f"{user_name}，请@一位你要查看关系的用户。")
            return

        # 2. 获取目标用户名称
        target_name = await self.market.get_user_name(event, target_id) or f"用户{target_id}"

        # 3. 获取用户称号
        user_data = self._get_user_in_group(group_id, user_id)
        target_data = self._get_user_in_group(group_id, target_id)

        user_title = user_data.get("current_title", "")
        target_title = target_data.get("current_title", "")

        # 4. 获取两人之间的关系数据
        relationship_data = self.social_manager.get_relationship_data(group_id, user_id, target_id)

        # 5. 获取头像URL
        user_avatar = ""
        target_avatar = ""
        if event.get_platform_name() == "aiocqhttp":
            user_avatar = f"http://q1.qlogo.cn/g?b=qq&nk={user_id}&s=640"
            target_avatar = f"http://q1.qlogo.cn/g?b=qq&nk={target_id}&s=640"

        # 6. 生成关系卡片
        from ._generate_social import generate_relationship_card
        card_path = await generate_relationship_card(
            user_id, user_name, user_avatar,
            target_id, target_name, target_avatar,
            relationship_data,
            user_title, target_title
        )

        if card_path and os.path.exists(card_path):
            yield event.image_result(card_path)
        else:
            # 回退到文本模式
            a_to_b = relationship_data.get("user_a_to_b_favorability", 0)
            b_to_a = relationship_data.get("user_b_to_a_favorability", 0)
            a_to_b_level = relationship_data.get("user_a_to_b_level", "陌生人")
            b_to_a_level = relationship_data.get("user_b_to_a_level", "陌生人")
            special_relation = relationship_data.get("special_relation", "")

            if special_relation:
                relation_text = f"【特殊关系】：{special_relation}\n"
            else:
                relation_text = ""

            relationship_text = (
                f"{user_name} 与 {target_name} 的关系\n"
                f"{relation_text}"
                f"{user_name} → {target_name}: 好感度 {a_to_b}，关系等级【{a_to_b_level}】\n"
                f"{target_name} → {user_name}: 好感度 {b_to_a}，关系等级【{b_to_a_level}】"
            )

            yield event.plain_result(relationship_text)


    # 添加我的关系网指令
    @filter.command("我的关系网")
    @filter.event_message_type(filter.EventMessageType.GROUP_MESSAGE)
    async def show_relationship_network(self, event: AstrMessageEvent):
        """查看自己的关系网络"""
        # 检查是否@了机器人
        if not self.is_bot_mentioned(event):
            return

        # 1. 解析指令
        user_id = event.get_sender_id()
        user_name = event.get_sender_name() or f"用户{user_id}"
        group_id = event.get_group_id()

        # 2. 获取用户称号
        user_data = self._get_user_in_group(group_id, user_id)
        user_title = user_data.get("current_title", "")

        # 3. 获取关系网络数据
        network_data = self.social_manager.get_relationship_network(group_id, user_id)

        # 为每个关系添加用户名
        for relation in network_data:
            target_id = relation["user_id"]
            target_name = await self.market.get_user_name(event, target_id) or f"用户{target_id}"
            relation["name"] = target_name

        # 4. 获取头像URL
        user_avatar = ""
        if event.get_platform_name() == "aiocqhttp":
            user_avatar = f"http://q1.qlogo.cn/g?b=qq&nk={user_id}&s=640"

        # 5. 生成关系网络卡片
        from ._generate_social import generate_social_network_card
        card_path = await generate_social_network_card(
            user_id, user_name, user_avatar, network_data, user_title
        )

        if card_path and os.path.exists(card_path):
            yield event.image_result(card_path)
        else:
            # 回退到文本模式
            if not network_data:
                yield event.plain_result(f"{user_name}，你还没有建立任何关系。")
                return

            network_text = f"{user_name} 的关系网：\n\n"

            for i, relation in enumerate(network_data):
                target_id = relation["user_id"]
                favorability = relation["favorability"]
                level = relation["level"]
                special_relation = relation.get("special_relation", "")

                if special_relation:
                    special_text = f" ♥{special_relation}♥"
                else:
                    special_text = ""

                network_text += f"{i+1}. {relation['name']}{special_text}：好感度 {favorability}，关系【{level}】\n"

            yield event.plain_result(network_text)


    # 添加缔结指令
    @filter.command("缔结")
    @filter.event_message_type(filter.EventMessageType.GROUP_MESSAGE)
    async def form_special_relationship(self, event: AstrMessageEvent, relation_name: str = None):
        """缔结特殊关系"""
        # 检查是否@了机器人
        if not self.is_bot_mentioned(event):
            return
            
        # 检查关系名称是否被提供
        if relation_name is None:
            valid_relations = "、".join(SPECIAL_RELATION_ITEMS.keys())
            yield event.plain_result(f"请指定要缔结的关系类型。用法：缔结 <关系类型> @用户\n可用的关系类型：{valid_relations}")
            return

        # 1. 解析指令
        user_id = event.get_sender_id()
        user_name = event.get_sender_name() or f"用户{user_id}"
        group_id = event.get_group_id()

        target_id = self.get_target_user_id(event)
        if not target_id:
            yield event.plain_result(f"{user_name}，请@一位你要缔结关系的用户。")
            return

        # 2. 获取目标用户名称
        target_name = await self.market.get_user_name(event, target_id) or f"用户{target_id}"

        # 3. 检查关系名是否有效
        if relation_name not in SPECIAL_RELATION_ITEMS:
            valid_relations = "、".join(SPECIAL_RELATION_ITEMS.keys())
            yield event.plain_result(f"无效的关系名称！可用的关系类型：{valid_relations}")
            return

        # 4. 获取对应的内部类型
        relation_type = SPECIAL_RELATION_TYPES.get(relation_name)
        if not relation_type:
            yield event.plain_result(f"内部错误：无法识别的关系类型。")
            return

        # 5. 获取所需物品
        required_item = SPECIAL_RELATION_ITEMS[relation_name]

        # 6. 查找物品ID
        item_id = None
        for id, data in SHOP_DATA.get("礼物", {}).items():
            if data["name"] == required_item:
                item_id = id
                break

        if not item_id:
            yield event.plain_result(f"内部错误：找不到物品 '{required_item}'。")
            return

        # 7. 检查背包中是否有该物品
        user_bag = self.shop_manager.get_user_bag(group_id, user_id)
        if "礼物" not in user_bag or item_id not in user_bag["礼物"] or user_bag["礼物"][item_id] <= 0:
            yield event.plain_result(f"缔结【{relation_name}】关系需要【{required_item}】，请先前往商店购买。")
            return

        # 8. 尝试缔结关系
        success, msg, check_achievement = await self.social_manager.form_relationship(
            group_id, user_id, target_id, relation_type
        )

        # 9. 如果成功，消耗物品并检查成就
        if success:
            await self.shop_manager.consume_item(group_id, user_id, item_id)
            
            # 检查是否需要解锁成就
            if check_achievement == "social_patron":
                await self.unlock_specific_achievement(event, user_id, 'social_patron')
        
        # 10. 返回结果
        yield event.plain_result(msg)



    # 添加解除关系指令
    @filter.command("解除关系")
    @filter.event_message_type(filter.EventMessageType.GROUP_MESSAGE)
    async def break_special_relationship(self, event: AstrMessageEvent):
        """解除特殊关系"""
        # 检查是否@了机器人
        if not self.is_bot_mentioned(event):
            return

        # 1. 解析指令
        user_id = event.get_sender_id()
        user_name = event.get_sender_name() or f"用户{user_id}"
        group_id = event.get_group_id()

        target_id = self.get_target_user_id(event)
        if not target_id:
            yield event.plain_result(f"{user_name}，请@一位你要解除关系的用户。")
            return

        # 2. 获取目标用户名称
        target_name = await self.market.get_user_name(event, target_id) or f"用户{target_id}"

        # 3. 尝试解除关系
        success, msg, _ = await self.social_manager.break_relationship(
            group_id, user_id, target_id
        )

        # 4. 返回结果
        if success:
            yield event.plain_result(f"{user_name} 解除了与 {target_name} 的特殊关系。\n{msg}")
        else:
            yield event.plain_result(msg)

    @filter.command("命令")
    async def show_command_list(self, event: AstrMessageEvent):
        """显示所有可用命令的帮助卡片"""
        if not self.is_bot_mentioned(event):
            return

        try:
            # 调用作图函数
            image_path = await generate_command_card()

            if image_path and os.path.exists(image_path):
                yield event.image_result(image_path)
            else:
                # 作图失败的回退方案
                yield event.plain_result("命令帮助卡片生成失败，请联系管理员。")
        except Exception as e:
            logger.error(f"处理“命令”指令时出错: {e}", exc_info=True)
            yield event.plain_result("生成命令帮助时出现内部错误。")

    async def terminate(self):
        """插件终止时保存数据并安全停止后台任务"""
        # --- [修改] 优雅地停止后台任务 ---
        if self.cleanup_task and not self.cleanup_task.done():
            self.cleanup_task.cancel()
        # ----------------------------
        self._save_user_data()
        logger.info("Astr签到插件已终止，数据已保存，清理任务已安全停止。")
