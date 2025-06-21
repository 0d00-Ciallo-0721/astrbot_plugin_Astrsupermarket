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

async def process_sign_in(plugin_instance, event: AstrMessageEvent):
    """
    处理签到逻辑，包括检测昨天是否签到及交互式补签
    """
    # 获取用户信息
    group_id = event.get_group_id()
    user_id = event.get_sender_id()
    user_name = event.get_sender_name() or f"用户{user_id}"
    
    # 获取用户头像
    avatar_url = ""
    if event.get_platform_name() == "aiocqhttp":
        avatar_url = f"http://q1.qlogo.cn/g?b=qq&nk={user_id}&s=640"
    
    # 获取当前日期和相关日期
    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M:%S")
    yesterday = (now - timedelta(days=1)).strftime("%Y-%m-%d")
    day_before_yesterday = (now - timedelta(days=2)).strftime("%Y-%m-%d")
        
    # 获取用户数据
    user = plugin_instance._get_user_in_group(group_id, user_id)
    
    # 检查今天是否已经签到
    if user["last_sign"] == today:
        yield event.plain_result(f"{user_name}，你今天已经签到过了，明天再来吧！")
        return
    
    # 检查是否满足交互式补签条件：
    # 1. 昨天没有签到（last_sign不等于yesterday）
    # 2. 前天签到了（last_sign等于day_before_yesterday）
    # 这意味着用户的连续签到会中断，我们可以给他一个补签的机会
    if user["last_sign"] == day_before_yesterday:
        # 提示用户是否需要补签
        yield event.plain_result(
            f"{user_name}，检测到您昨日未签到，是否花费50Astr币进行补签？\n"
            f"回复【补签】以补签并继续今日签到，或回复【跳过】直接完成今日签到（将中断连续天数）。"
        )
        
        # 使用会话控制器等待用户回复
        try:
            @session_waiter(timeout=60)
            async def wait_for_decision(controller: SessionController, wait_event: AstrMessageEvent):
                reply = wait_event.message_str.strip()
                
                # 重新获取用户数据
                current_user = plugin_instance._get_user_in_group(group_id, user_id)
                
                if reply == "补签":
                    # 检查用户余额是否足够
                    if current_user["points"] < 50:
                        await wait_event.send(event.plain_result(f"补签失败，您的Astr币不足50，当前余额：{current_user['points']}"))
                        controller.stop()
                        return
                    
                    # 执行补签
                    success, result = await perform_re_sign(
                        plugin_instance,
                        wait_event, 
                        group_id,
                        user_id, 
                        user_name, 
                        avatar_url
                    )
                    
                    if success:
                        # 解锁"后悔药"成就
                        await plugin_instance.unlock_specific_achievement(wait_event, user_id, 'signin_4')
                        
                        # 重新获取用户数据，因为补签可能已更新
                        user = plugin_instance._get_user_in_group(group_id, user_id)
                        
                        # 发送补签结果
                        if result.startswith("http") or os.path.exists(result):
                            await wait_event.send(event.image_result(result))
                        else:
                            await wait_event.send(event.plain_result(result))
                        
                        # 继续执行今日签到
                        await wait_event.send(event.plain_result(f"补签完成，现在为您进行今日签到..."))
                    else:
                        # 补签失败
                        await wait_event.send(event.plain_result(result))
                        controller.stop()
                        return
                    
                elif reply == "跳过":
                    # 告知用户即将执行常规签到
                    await wait_event.send(event.plain_result(f"已跳过补签，为您直接签到（连续签到将重置为1天）..."))
                    
                    # 不执行补签，连续签到会在后续代码中重置为1
                    
                else:
                    # 无效回复
                    await wait_event.send(event.plain_result(f"指令无效，操作已取消"))
                    controller.stop()
                    return
                
                # 会话完成，结束控制器
                controller.stop()
            
            # 启动会话控制器
            await wait_for_decision(event)
            
        except TimeoutError:
            # 用户超时未回复
            yield event.plain_result(f"{user_name}，您没有及时回复，操作已取消")
            return
        
    # 执行常规签到逻辑
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
    
    # 连续签到奖励
    if user["streak_days"] >= 7:
        streak_bonus = 50
    elif user["streak_days"] >= 3:
        streak_bonus = 20
        
    # 更新Astr币
    user["points"] += (daily_reward + streak_bonus)
    
    # 保存用户数据
    plugin_instance._save_user_data()

    # --- 调用成就检查 ---
    await plugin_instance.check_and_unlock_achievements(event, user_id)
    # --------------------------
    
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
            logger.info("HTML渲染失败，尝试使用Pillow生成签到卡片")
            card_url = await generate_sign_card_pillow(
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

        if card_url:
            yield event.image_result(card_url)
        else:
            # 两种方式都失败，降级为文本消息
            msg = (f"✅ 签到成功！\n"
                  f"用户: {user_name}\n"
                  f"签到时间: {today} {current_time}\n"
                  f"累计签到: {user['total_days']}天\n"
                  f"连续签到: {user['streak_days']}天\n"
                  f"今日奖励: +{daily_reward}Astr币\n")
                  
            if streak_bonus > 0:
                msg += f"连续签到奖励: +{streak_bonus}Astr币\n"
                
            msg += f"当前Astr币: {user['points']}"
            yield event.plain_result(msg)
            
    except Exception as e:
        logger.error(f"生成签到卡片失败: {str(e)}")
        yield event.plain_result(f"签到成功，但生成卡片时出现错误。当前Astr币{user['points']:.2f}")
