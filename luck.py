import os
import random
from datetime import datetime
from astrbot.api import logger
import traceback
from astrbot.api.event import MessageChain
from astrbot.api.message_components import At, Image, Plain

# 抽奖等级配置
LOTTERY_LEVELS = {
    "6星": range(1, 11),       # 1-10
    "5星": range(11, 31),      # 11-30
    "4星": range(31, 51),      # 31-50
    "3星": range(51, 71),      # 51-70
    "2星": range(71, 91),      # 71-90
    "1星": range(91, 111),     # 91-110, 扩大范围以包含111
    "隐藏": [111]              # 隐藏大奖
}

# 奖励配置
LOTTERY_REWARDS = {
    "6星": (20, 25),          # 随机20-25Astr币
    "5星": (15, 20),          # 随机15-20Astr币
    "4星": (10, 15),          # 随机10-15Astr币
    "3星": (5, 10),           # 随机5-10Astr币
    "2星": (1, 5),            # 随机1-5Astr币
    "1星": (0, 0),            # 不获得Astr币
    "隐藏": (50, 50)          # 固定50Astr币
}

# 等级描述
LEVEL_DESCRIPTIONS = {
    "6星": "你的气运达到了6星，极为罕见，今日宜大展宏图。",
    "5星": "5星气运，运势上佳，可把握当下机遇。",
    "4星": "4星气运，今日整体顺利，适合稳中求进。",
    "3星": "3星气运，状态平稳，保持常态即可。",
    "2星": "2星气运，略有波折，建议保持冷静应对。",
    "1星": "1星气运，今日多有不顺，宜低调行事，避免冒进。",
    "隐藏": "你触发了隐藏气运，超低概率事件！今天或有意外惊喜降临。"
}

async def process_lottery(event, group_id: str, user_id: str, user_name: str, user_data: dict, shop_manager=None) -> tuple:
    """
    处理抽奖逻辑, 返回 (消息组件列表, 更新后的用户数据, 中奖等级)
    现在支持道具效果
    
    Args:
        event: 消息事件
        group_id: 群组ID
        user_id: 用户ID
        user_name: 用户名称
        user_data: 用户数据
        shop_manager: 商店管理器实例，由main.py传入
    """
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        last_play_date = user_data.get("lottery_date", "")
        play_count = user_data.get("lottery_count", 0)
        
        if last_play_date != today:
            play_count = 0
            
        if play_count >= 3:
            msg = [At(qq=user_id), Plain(f" 你今天已经抽奖3次了，明天再来吧~")]
            return (msg, None, None)
        
        if user_data["points"] < 15:
            msg = [At(qq=user_id), Plain(f" 抽奖需要15Astr币，你只有{user_data['points']:.2f}Astr币~")]
            return (msg, None, None)
        
        # 扣除抽奖费用
        user_data["points"] -= 15
        user_data["lottery_date"] = today
        user_data["lottery_count"] = play_count + 1
        
        # --- [修改] 检查并应用道具效果 ---
        buffs = user_data.get('buffs', {})
        
        # 检查最低3星保障
        min_3star = False
        if shop_manager and buffs.get("lottery_min_3star", 0) > 0:
            min_3star = True
            buffs["lottery_min_3star"] -= 1
            logger.info(f"用户 {user_id} 使用了幸运药水效果，本次抽奖至少3星")
        
        # 检查奖励翻倍效果
        double_reward = False
        if shop_manager and buffs.get("lottery_double_reward", 0) > 0:
            double_reward = True
            buffs["lottery_double_reward"] -= 1
            logger.info(f"用户 {user_id} 使用了幸运四叶草效果，本次奖励翻倍")
        
        # 检查双抽取最佳效果
        best_of_two = False
        if shop_manager and buffs.get("lottery_best_of_two", 0) > 0:
            best_of_two = True
            buffs["lottery_best_of_two"] -= 1
            logger.info(f"用户 {user_id} 使用了双生星愿效果，本次抽两次取最佳")
        
        # 清理空的buff项
        user_data["buffs"] = {k: v for k, v in buffs.items() if v > 0}
        
        # --- [修改] 抽奖逻辑，考虑道具效果 ---
        results = []
        
        # 进行一次或两次抽奖
        for _ in range(2 if best_of_two else 1):
            lucky_number = random.randint(1, 111)
            temp_level = None
            
            # 找出对应等级
            for level_name, number_range in LOTTERY_LEVELS.items():
                if lucky_number in number_range:
                    temp_level = level_name
                    break
            
            # 应用最低3星保障
            if min_3star and temp_level in ["1星", "2星"]:
                # 随机选择一个3星及以上的等级
                better_levels = ["3星", "4星", "5星", "6星"]
                temp_level = random.choice(better_levels)
                # 重新选择一个对应等级的lucky_number
                lucky_number = random.choice(list(LOTTERY_LEVELS[temp_level]))
            
            results.append((lucky_number, temp_level))
        
        # 如果是双抽取最佳，选择星级最高的结果
        if best_of_two:
            # 按照星级排序（6星>5星>...>1星）
            star_rank = {"6星": 6, "5星": 5, "4星": 4, "3星": 3, "2星": 2, "1星": 1, "隐藏": 7}
            results.sort(key=lambda x: star_rank.get(x[1], 0), reverse=True)
            
        # 最终结果
        lucky_number, level = results[0]
            
        if not level:
            logger.error(f"抽奖数字 {lucky_number} 没有对应的等级")
            return (None, None, None)
            
        # 更新统计数据
        if level == "6星":
            user_data["high_tier_wins"] = user_data.get("high_tier_wins", 0) + 1
            user_data["consecutive_1star"] = 0
        elif level == "隐藏":
            user_data["high_tier_wins"] = user_data.get("high_tier_wins", 0) + 1
            user_data["consecutive_1star"] = 0
        elif level == "1星":
            user_data["consecutive_1star"] = user_data.get("consecutive_1star", 0) + 1
        else:
            user_data["consecutive_1star"] = 0

        # 计算奖励
        min_reward, max_reward = LOTTERY_REWARDS[level]
        reward = random.randint(min_reward, max_reward)
        
        # 应用奖励翻倍效果
        bonus_text = ""
        if double_reward and reward > 0:
            original_reward = reward
            reward *= 2
            bonus_text = f"[幸运四叶草效果] 奖励翻倍：{original_reward} → {reward}Astr币！\n"
        
        user_data["points"] += reward
        description = LEVEL_DESCRIPTIONS[level]
        
        # --- [修改] 根据幸运数字范围匹配图片 ---
        image_filename = ""
        if 1 <= lucky_number <= 10:
            image_filename = "a.jpg"
        elif 11 <= lucky_number <= 44:
            image_filename = "b.jpg"
        elif 45 <= lucky_number <= 80:
            image_filename = "c.jpg"
        elif 81 <= lucky_number <= 110:
            image_filename = "d.jpg"
        elif lucky_number == 111:
            image_filename = "e.jpg"

        image_path = None
        if image_filename:
            # 准备图片路径
            image_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "luck", image_filename)
            if not os.path.exists(image_path):
                logger.warning(f"抽奖图片不存在: {image_path}, 将只发送文本消息。")
                image_path = None
        # --- [修改结束] ---

        # 准备消息
        effect_prefix = ""
        if best_of_two:
            effect_prefix = "[双生星愿效果] 从两次抽奖中选择了最佳结果！\n"
        elif min_3star:
            effect_prefix = "[幸运药水效果] 保障了至少3星的结果！\n"
            
        message_chain_list = [
            At(qq=user_id),
            Plain(f" {effect_prefix}{bonus_text}你抽到了 {level} (幸运数字: {lucky_number})! 这是你今天的第 {user_data['lottery_count']} 次抽奖。\n{description}\n")
        ]
        
        if reward > 0:
            message_chain_list.append(Plain(f"获得奖励: {reward} Astr币\n"))
        else:
            message_chain_list.append(Plain("没有获得Astr币奖励。\n"))
        
        message_chain_list.append(Plain(f"当前Astr币: {user_data['points']:.2f}"))
        
        if image_path:
            message_chain_list.append(Image.fromFileSystem(image_path))
        
        return (message_chain_list, user_data, level)
        
    except Exception as e:
        logger.error(f"抽奖过程中出错: {str(e)}")
        traceback.print_exc()
        return (None, None, None)
