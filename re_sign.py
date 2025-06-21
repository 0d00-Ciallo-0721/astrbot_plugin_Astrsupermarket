import os
from datetime import datetime, timedelta
from astrbot.api import logger
from ._generate_card import generate_sign_card

async def perform_re_sign(plugin_instance, event, group_id: str, user_id: str, user_name: str, avatar_url=None):
    """
    执行补签功能
    
    Args:
        plugin_instance: 插件实例
        event: 消息事件
        user_id: 用户ID
        user_name: 用户名称
        avatar_url: 用户头像URL (可选)
    
    Returns:
        成功则返回(True, 结果)，失败则返回(False, 失败原因)
    """
    # 获取群聊数据
    group_data = plugin_instance._get_group_user_data(group_id)

    # 检查用户数据是否存在
    if user_id not in group_data:
        return False, f"{user_name}，你还没有签到记录，无法补签。请先进行一次签到。"
    
    user = group_data[user_id]
    
    # 检查Astr币是否足够
    re_sign_cost = 50  # 补签花费
    if user["points"] < re_sign_cost:
        return False, f"{user_name}，补签需要{re_sign_cost}Astr币，你当前只有{user['points']}Astr币，无法补签。"
    
    # 获取当前日期和昨天的日期
    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    yesterday = (now - timedelta(days=1)).strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M:%S")
    
    # 检查今天是否已经签到
    if user["last_sign"] == today:
        return False, f"{user_name}，你今天已经签到过了，不需要补签。"
    
    # 检查昨天是否已经签到（不能重复补签）
    if user["last_sign"] == yesterday:
        return False, f"{user_name}，你昨天已经签到过了，不需要补签。"
    
    # 获取用户最后签到日期，转换为datetime对象以便比较
    try:
        last_sign_date = datetime.strptime(user["last_sign"], "%Y-%m-%d")
        # 计算与最后签到日期的差距
        days_diff = (now - last_sign_date).days
        
        # 如果差距不等于2天，说明不是昨天漏签
        if days_diff != 2:
            return False, f"{user_name}，补签只能弥补昨天的签到。你上次签到是{user['last_sign']}，已经连续缺席签到{days_diff-1}天，无法进行补签。"
    except ValueError:
        # 日期格式错误时的处理
        return False, f"{user_name}，签到数据异常，请联系管理员。"
    
    # 执行补签操作
    # 扣除Astr币
    user["points"] -= re_sign_cost
    
    # 更新签到数据
    user["streak_days"] += 1  # 增加连续签到天数
    user["last_sign"] = yesterday  # 设置最后签到日期为昨天
    
    # 保存用户数据
    plugin_instance._save_user_data()
    
    # 生成补签卡片
    try:
        card_url = await generate_sign_card(
            star_instance=plugin_instance,
            user_id=user_id,
            user_name=user_name,
            avatar_url=avatar_url,
            total_days=user["total_days"],
            streak_days=user["streak_days"],
            daily_reward=0,  # 补签不提供奖励
            streak_bonus=0,  # 补签不提供连续签到奖励
            total_points=user["points"],
            sign_time=f"{yesterday} (补签)",
            is_resign=True  # 添加补签标记
        )
        
        if card_url:
            return True, card_url
        else:
            # 生成卡片失败，返回文本消息
            return True, f"✅ 补签成功！\n用户: {user_name}\n补签日期: {yesterday}\n消耗Astr币: {re_sign_cost}\n当前Astr币: {user['points']}\n连续签到天数: {user['streak_days']}天"
    except Exception as e:
        logger.error(f"生成补签卡片失败: {str(e)}")
        return True, f"补签成功，但生成卡片时出现错误。消耗{re_sign_cost}Astr币，当前Astr币{user['points']}，连续签到天数{user['streak_days']}天。"
