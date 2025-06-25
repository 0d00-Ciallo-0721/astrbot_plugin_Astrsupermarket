# feifeisupermarket/qsin.py

import os
import random
from datetime import datetime, timedelta

from astrbot.api.event import AstrMessageEvent
from astrbot.api import logger
import astrbot.api.message_components as Comp
from astrbot.core.utils.session_waiter import session_waiter, SessionController

from ._generate_card import generate_sign_card, generate_sign_card_pillow
from .re_sign import perform_re_sign

# 新增一个内部函数，封装实际的签到逻辑
async def _perform_actual_sign_in(plugin_instance, event: AstrMessageEvent, group_id: str, user_id: str, user_name: str, avatar_url: str):
    """
    执行最终的签到操作并生成卡片。
    这是一个可被复用的内部函数。
    """
    user = plugin_instance._get_user_in_group(group_id, user_id)
    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    yesterday = (now - timedelta(days=1)).strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M:%S")

    # 检查今天是否已经签到（在补签后可能会再次检查）
    if user["last_sign"] == today:
        # 这种情况通常发生在补签流程后，直接返回即可，无需提示
        return

    # 计算连续签到天数
    if user["last_sign"] == yesterday:
        user["streak_days"] += 1
    else:
        user["streak_days"] = 1
        
    # 更新签到数据
    user["total_days"] += 1
    user["last_sign"] = today
    
    # 计算奖励
    daily_reward = random.randint(10, 30)
    streak_bonus = 0
    
    if user["streak_days"] >= 7:
        streak_bonus = 50
    elif user["streak_days"] >= 3:
        streak_bonus = 20
        
    user["points"] += (daily_reward + streak_bonus)
    plugin_instance._save_user_data()
    await plugin_instance.check_and_unlock_achievements(event, user_id)
    
    # 生成签到卡片
    try:
        card_url = await generate_sign_card(
            star_instance=plugin_instance,
            user_id=user_id,
            user_name=user_name,
            avatar_url=avatar_url,
            total_days=user["total_days"],
            streak_days=user["streak_days"],
            daily_reward=daily_reward,
            streak_bonus=streak_bonus,
            total_points=user["points"],
            sign_time=f"{today} {current_time}",
            title=user.get("current_title")
        )
        
        if not card_url:
            card_url = await generate_sign_card_pillow(
                user_id=user_id, user_name=user_name, avatar_url=avatar_url,
                total_days=user["total_days"], streak_days=user["streak_days"],
                daily_reward=daily_reward, streak_bonus=streak_bonus,
                total_points=user["points"], sign_time=f"{today} {current_time}",
                title=user.get("current_title")
            )

        if card_url:
            yield event.image_result(card_url)
        else:
            msg = (f"✅ 签到成功！\n"
                   f"用户: {user_name}\n签到时间: {today} {current_time}\n"
                   f"累计签到: {user['total_days']}天\n连续签到: {user['streak_days']}天\n"
                   f"今日奖励: +{daily_reward}妃爱币\n" +
                   (f"连续签到奖励: +{streak_bonus}妃爱币\n" if streak_bonus > 0 else "") +
                   f"当前妃爱币: {user['points']}")
            yield event.plain_result(msg)
            
    except Exception as e:
        logger.error(f"生成签到卡片失败: {str(e)}")
        yield event.plain_result(f"签到成功，但生成卡片时出现错误。当前妃爱币{user['points']:.2f}")

# 修改原有的process_sign_in函数
async def process_sign_in(plugin_instance, event: AstrMessageEvent):
    """
    处理签到逻辑，现在只负责检查和发起补签提示。
    """
    group_id = event.get_group_id()
    user_id = event.get_sender_id()
    user_name = event.get_sender_name() or f"用户{user_id}"
    
    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    day_before_yesterday = (now - timedelta(days=2)).strftime("%Y-%m-%d")
        
    user = plugin_instance._get_user_in_group(group_id, user_id)
    
    if user["last_sign"] == today:
        yield event.plain_result(f"{user_name}，你今天已经签到过了，明天再来吧！")
        return
    
    # 检查是否需要补签
    if user["last_sign"] == day_before_yesterday:
        # 注册一个待处理的决策
        if not hasattr(plugin_instance, 'pending_resign_decisions'):
            plugin_instance.pending_resign_decisions = {}
            
        decision_key = (group_id, user_id)
        plugin_instance.pending_resign_decisions[decision_key] = {"prompted_at": datetime.now()}

        # 发送提示后直接结束
        yield event.plain_result(
            f"{user_name}，检测到您昨日未签到，是否花费50妃爱币进行补签？\n"
            f"回复【补签】以补签并继续今日签到，或回复【跳过】直接完成今日签到（将中断连续天数）。"
        )
        return

    # 如果不需要补签，直接执行签到
    avatar_url = f"http://q1.qlogo.cn/g?b=qq&nk={user_id}&s=640" if event.get_platform_name() == "aiocqhttp" else ""
    async for result in _perform_actual_sign_in(plugin_instance, event, group_id, user_id, user_name, avatar_url):
        yield result
