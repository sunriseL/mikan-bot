
import httpx
from httpx import HTTPStatusError, RequestError
from nonebot import require, get_driver
require("nonebot_plugin_apscheduler")

from nonebot_plugin_apscheduler import scheduler
from nonebot.log import logger
from nonebot import on_command
from nonebot.adapters.onebot.v11 import MessageEvent, MessageSegment, Message
from nonebot.params import CommandArg
from nonebot.exception import FinishedException
import asyncio
import json
from datetime import datetime
from typing import Optional

# 激活驱动器
driver = get_driver()

from .config import FollowerConfig

# 加载配置
config = FollowerConfig()

# 创建 HTTP 客户端
http_client = httpx.AsyncClient(timeout=config.api_timeout)

@driver.on_startup
async def init():
    """初始化插件"""
    logger.info("Follower plugin initialized - using external API service")

@driver.on_shutdown
async def cleanup():
    """清理资源"""
    await http_client.aclose()

async def call_api(endpoint: str, method: str = "GET", data: Optional[dict] = None, return_json: bool = True) -> dict:
    """调用外部 API"""
    try:
        url = f"{config.api_base_url}{endpoint}"
        if method.upper() == "GET":
            response = await http_client.get(url)
        elif method.upper() == "POST":
            response = await http_client.post(url, json=data)
        elif method.upper() == "PUT":
            response = await http_client.put(url, json=data)
        elif method.upper() == "DELETE":
            response = await http_client.delete(url)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        response.raise_for_status()
        
        if return_json:
            return response.json()
        else:
            return {"content": response.content, "headers": dict(response.headers)}
    except httpx.HTTPStatusError as e:
        logger.error(f"API request failed with status {e.response.status_code}: {e.response.text}")
        raise
    except httpx.RequestError as e:
        logger.error(f"API request failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in API call: {e}")
        raise

# 注册指令：查询所有用户
list_users = on_command("list_users", aliases={"用户列表", "查看用户"}, priority=5)

@list_users.handle()
async def handle_list_users(event: MessageEvent):
    """处理用户列表查询"""
    try:
        logger.info("Fetching user list")
        
        users_data = await call_api("/api/users")
        
        if not users_data:
            await list_users.finish("没有找到任何用户")

        # 格式化输出
        message = "📋 跟踪用户列表\n"
        active_count = 0
        
        for user in users_data:
            status_icon = "✅" if user.get("is_active", False) else "❌"
            message += f"{status_icon} ID:{user.get('id')} {user.get('platform', '').upper()}: {user.get('username', '')}\n"
            if user.get("is_active", False):
                active_count += 1
        
        message += f"\n总计: {len(users_data)} 个用户 (活跃: {active_count})"
        
        await list_users.finish(message)
        
    except FinishedException:
        # 正常结束，不需要处理
        pass
    except Exception as e:
        logger.error(f"Unexpected error in list users handler: {e}")
        await list_users.finish(f"出错了：{str(e)}")

# 注册指令：添加用户
add_user = on_command("add_user", aliases={"添加用户"}, priority=5)

@add_user.handle()
async def handle_add_user(event: MessageEvent, args: Message = CommandArg()):
    """处理添加用户"""
    # 解析指令参数
    arg_list = args.extract_plain_text().strip().split()
    if len(arg_list) != 2:
        await add_user.finish(
            "用法：/添加用户 平台 用户名\n"
            "例如：/添加用户 twitter kohinatamika\n"
            "支持平台：twitter, instagram"
        )
    
    platform, username = arg_list

    try:
        # 调用外部 API 添加用户
        logger.info(f"Adding user {platform}/{username}")
        
        user_data = {
            "platform": platform,
            "username": username
        }
        
        result = await call_api("/api/users", method="POST", data=user_data)
        
        validation_result = result.get("validation_result", {})
        if validation_result.get("valid", False):
            message = f"✅ 成功添加用户\n"
            message += f"👤 平台: {platform.upper()}\n"
            message += f"📝 用户名: {username}\n"
            message += f"🆔 ID: {result.get('id')}\n"
            message += f"📊 当前粉丝数: {validation_result.get('follower_count', 'N/A')}"
            await add_user.finish(message)
        else:
            validation_msg = validation_result.get("message", "验证失败")
            await add_user.finish(f"❌ 添加用户失败：{validation_msg}")
        
    except FinishedException:
        # 正常结束，不需要处理
        pass
    except Exception as e:
        logger.error(f"Unexpected error in add user handler: {e}")
        await add_user.finish(f"出错了：{str(e)}")


# 注册指令：删除用户
delete_user = on_command("delete_user", aliases={"删除用户"}, priority=5)

@delete_user.handle()
async def handle_delete_user(event: MessageEvent, args: Message = CommandArg()):
    """处理删除用户"""
    # 解析指令参数
    arg_text = args.extract_plain_text().strip()
    if not arg_text or not arg_text.isdigit():
        await delete_user.finish(
            "用法：/删除用户 用户ID\n"
            "例如：/删除用户 1\n"
            "使用 /用户列表 查看用户ID"
        )
    
    user_id = int(arg_text)

    try:
        # 调用外部 API 删除用户
        logger.info(f"Deleting user ID: {user_id}")
        
        await call_api(f"/api/users/{user_id}", method="DELETE")
        
        message = f"✅ 成功删除用户 (ID: {user_id})"
        await delete_user.finish(message)
        
    except FinishedException:
        # 正常结束，不需要处理
        pass
    except Exception as e:
        logger.error(f"Unexpected error in delete user handler: {e}")
        await delete_user.finish(f"出错了：{str(e)}")


# 注册指令：激活用户
activate_user = on_command("activate_user", aliases={"激活用户"}, priority=5)

@activate_user.handle()
async def handle_activate_user(event: MessageEvent, args: Message = CommandArg()):
    """处理激活用户"""
    # 解析指令参数
    arg_text = args.extract_plain_text().strip()
    if not arg_text or not arg_text.isdigit():
        await activate_user.finish(
            "用法：/激活用户 用户ID\n"
            "例如：/激活用户 1\n"
            "使用 /用户列表 查看用户ID"
        )
    
    user_id = int(arg_text)

    try:
        # 调用外部 API 激活用户
        logger.info(f"Activating user ID: {user_id}")
        
        await call_api(f"/api/users/{user_id}/activate", method="PUT")
        
        message = f"✅ 成功激活用户 (ID: {user_id})"
        await activate_user.finish(message)

    except FinishedException:
        # 正常结束，不需要处理
        pass
    except Exception as e:
        logger.error(f"Unexpected error in activate user handler: {e}")
        await activate_user.finish(f"出错了：{str(e)}")

# 注册指令：查看粉丝数据
get_followers = on_command("get_followers", aliases={"粉丝数据"}, priority=5)

@get_followers.handle()
async def handle_get_followers(event: MessageEvent, args: Message = CommandArg()):
    """处理粉丝数据查询"""
    # 解析指令参数
    arg_list = args.extract_plain_text().strip().split()
    
    try:
        # 构建查询参数
        params = {}
        if len(arg_list) >= 1:
            params["platform"] = arg_list[0]
        if len(arg_list) >= 2:
            params["username"] = arg_list[1]
        if len(arg_list) >= 3:
            params["limit"] = int(arg_list[2])
        
        # 构建查询字符串
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        endpoint = f"/api/followers?{query_string}" if query_string else "/api/followers"
        
        logger.info(f"Fetching followers data: {endpoint}")
        
        followers_data = await call_api(endpoint)
        
        if not followers_data:
            await get_followers.finish("没有找到粉丝数据")

        # 格式化输出
        message = "📊 粉丝数据\n"
        
        for follower in followers_data[:10]:  # 只显示前10条
            platform = follower.get("platform", "")
            username = follower.get("username", "")
            count = follower.get("follower_count", 0)
            time = follower.get("time", "")
            
            message += f"👤 {platform.upper()}: {username}\n"
            message += f"👥 粉丝数: {count:,}\n"
            message += f"🕐 时间: {time}\n\n"
        
        if len(followers_data) > 10:
            message += f"... 还有 {len(followers_data) - 10} 条记录"
        
        await get_followers.finish(message)

    except FinishedException:
        # 正常结束，不需要处理
        pass
    except Exception as e:
        logger.error(f"Unexpected error in get followers handler: {e}")
        await get_followers.finish(f"出错了：{str(e)}")

# 注册指令：查看最新粉丝数据
get_latest_followers = on_command("latest_followers", aliases={"最新粉丝"}, priority=5)

@get_latest_followers.handle()
async def handle_latest_followers(event: MessageEvent):
    """处理最新粉丝数据查询"""
    try:
        logger.info("Fetching latest followers data")
        
        latest_data = await call_api("/api/followers/latest")
        
        if not latest_data:
            await get_latest_followers.finish("没有找到最新粉丝数据")

        # 格式化输出
        message = "📊 最新粉丝数据\n"
        
        for follower in latest_data:
            platform = follower.get("platform", "")
            username = follower.get("username", "")
            count = follower.get("follower_count", 0)
            time = follower.get("time", "")
            
            message += f"👤 {platform.upper()}: {username}\n"
            message += f"👥 粉丝数: {count:,}\n"
            message += f"🕐 时间: {time}\n\n"
        
        await get_latest_followers.finish(message)

    except FinishedException:
        # 正常结束，不需要处理
        pass
    except Exception as e:
        logger.error(f"Unexpected error in latest followers handler: {e}")
        await get_latest_followers.finish(f"出错了：{str(e)}")

# 注册指令：生成图表
generate_chart = on_command("generate_chart", aliases={"生成图表", "图表"}, priority=5)

@generate_chart.handle()
async def handle_generate_chart(event: MessageEvent, args: Message = CommandArg()):
    """处理图表生成"""
    # 解析指令参数
    arg_list = args.extract_plain_text().strip().split()
    if len(arg_list) != 2:
        await generate_chart.finish(
            "用法：/生成图表 平台 用户名\n"
            "例如：/生成图表 twitter kohinatamika\n"
            "支持平台：twitter, instagram"
        )
    
    platform, username = arg_list

    try:
        # 调用外部 API 生成图表
        logger.info(f"Generating chart for {platform}/{username}")
        
        # 图表API直接返回图片数据
        chart_response = await call_api(f"/api/chart/{platform}/{username}", return_json=False)
        
        if chart_response and chart_response.get("content"):
            # 将二进制图片数据转换为base64
            import base64
            image_data = base64.b64encode(chart_response["content"]).decode()
            await generate_chart.send(MessageSegment.image(f"base64://{image_data}"))
        else:
            await generate_chart.finish("图表生成失败")

    except FinishedException:
        # 正常结束，不需要处理
        pass
    except Exception as e:
        logger.error(f"Unexpected error in generate chart handler: {e}")
        await generate_chart.finish(f"出错了：{str(e)}")

# 注册指令：手动抓取数据
manual_fetch = on_command("manual_fetch", aliases={"手动抓取"}, priority=5)

@manual_fetch.handle()
async def handle_manual_fetch(event: MessageEvent, args: Message = CommandArg()):
    """处理手动抓取数据"""
    # 解析指令参数
    arg_list = args.extract_plain_text().strip().split()
    if len(arg_list) < 1:
        await manual_fetch.finish(
            "用法：/手动抓取 平台 [用户名]\n"
            "例如：/手动抓取 twitter\n"
            "例如：/手动抓取 instagram kohinata_mika\n"
            "支持平台：twitter, instagram"
        )
    
    platform = arg_list[0]
    username = arg_list[1] if len(arg_list) > 1 else None

    try:
        # 调用外部 API 手动抓取数据
        if platform.lower() == "twitter":
            endpoint = "/api/fetch/twitter"
        elif platform.lower() == "instagram":
            endpoint = "/api/fetch/instagram"
        else:
            await manual_fetch.finish("不支持的平台，请使用 twitter 或 instagram")
        
        if username:
            endpoint += f"?username={username}"
        
        logger.info(f"Manual fetch for {platform}/{username if username else 'all'}")
        
        result = await call_api(endpoint, method="POST")
        
        message = f"✅ 手动抓取完成\n"
        message += f"📊 平台: {platform.upper()}\n"
        if username:
            message += f"👤 用户: {username}"
        else:
            message += f"👥 所有用户"
        
        await manual_fetch.finish(message)

    except FinishedException:
        # 正常结束，不需要处理
        pass
    except Exception as e:
        logger.error(f"Unexpected error in manual fetch handler: {e}")
        await manual_fetch.finish(f"出错了：{str(e)}")

# 注册指令：查看统计信息
get_stats = on_command("get_stats", aliases={"统计信息"}, priority=5)

@get_stats.handle()
async def handle_get_stats(event: MessageEvent):
    """处理统计信息查询"""
    try:
        logger.info("Fetching stats")
        
        stats_data = await call_api("/api/stats")
        
        if not stats_data:
            await get_stats.finish("没有找到统计信息")

        # 格式化输出
        message = "📈 统计信息\n"
        
        for key, value in stats_data.items():
            if isinstance(value, dict):
                message += f"📊 {key}:\n"
                for sub_key, sub_value in value.items():
                    message += f"  {sub_key}: {sub_value}\n"
            else:
                message += f"📊 {key}: {value}\n"
        
        await get_stats.finish(message)

    except FinishedException:
        # 正常结束，不需要处理
        pass
    except Exception as e:
        logger.error(f"Unexpected error in get stats handler: {e}")
        await get_stats.finish(f"出错了：{str(e)}")

# 注册指令：生成比较图表
generate_comparison_chart = on_command("compare_chart", aliases={"比较图表", "对比图表"}, priority=5)

@generate_comparison_chart.handle()
async def handle_generate_comparison_chart(event: MessageEvent, args: Message = CommandArg()):
    """处理比较图表生成"""
    # 解析指令参数
    arg_text = args.extract_plain_text().strip()
    
    if not arg_text:
        await generate_comparison_chart.finish(
            "用法：/比较图表 用户列表 [起始日期]\n"
            "例如：/比较图表 twitter:kohinatamika,instagram:kohinata_mika\n"
            "例如：/比较图表 twitter:kohinatamika,instagram:kohinata_mika 2024-01-01\n"
            "用户格式：platform1:username1,platform2:username2\n"
            "日期格式：YYYY-MM-DD（可选，默认30天前）\n"
            "支持平台：twitter, instagram"
        )
    
    # 解析参数
    parts = arg_text.split()
    users_param = parts[0]
    
    # 检查日期参数
    if len(parts) > 1:
        start_date = parts[1]
        # 验证日期格式
        try:
            from datetime import datetime
            datetime.strptime(start_date, "%Y-%m-%d")
        except ValueError:
            await generate_comparison_chart.finish("日期格式错误，请使用 YYYY-MM-DD 格式")
    else:
        # 默认使用30天前的日期
        from datetime import datetime, timedelta
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    
    # 验证用户参数格式
    if "," not in users_param:
        await generate_comparison_chart.finish(
            "用户参数格式错误，请使用：platform1:username1,platform2:username2\n"
            "例如：twitter:kohinatamika,instagram:kohinata_mika"
        )
    
    try:
        # 调用外部 API 生成比较图表
        logger.info(f"Generating comparison chart for users: {users_param}, start_date: {start_date}")
        
        # 构建查询参数
        params = {
            "start_date": start_date,
            "users": users_param
        }
        
        # 构建查询字符串
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        endpoint = f"/api/compare/chart?{query_string}"
        
        # 图表API直接返回图片数据
        chart_response = await call_api(endpoint, return_json=False)
        
        if chart_response and chart_response.get("content"):
            # 将二进制图片数据转换为base64
            import base64
            image_data = base64.b64encode(chart_response["content"]).decode()
            await generate_comparison_chart.send(MessageSegment.image(f"base64://{image_data}"))
        else:
            await generate_comparison_chart.finish("比较图表生成失败")

    except FinishedException:
        # 正常结束，不需要处理
        pass
    except Exception as e:
        logger.error(f"Unexpected error in generate comparison chart handler: {e}")
        await generate_comparison_chart.finish(f"出错了：{str(e)}")

# 注册指令：帮助
follower_help = on_command("follower_help", aliases={"粉丝帮助"}, priority=5)

@follower_help.handle()
async def handle_follower_help(event: MessageEvent):
    """显示帮助信息"""
    help_text = """
📊 粉丝数据管理插件

用户管理：
• /用户列表 - 查看所有跟踪的用户
• /添加用户 平台 用户名 - 添加新用户
• /删除用户 用户ID - 删除用户（软删除）
• /激活用户 用户ID - 激活已删除的用户

数据查询：
• /粉丝数据 [平台] [用户名] [数量] - 查看粉丝数据
• /最新粉丝 - 查看最新粉丝数据
• /生成图表 平台 用户名 - 生成粉丝趋势图表
• /比较图表 用户列表 [起始日期] - 生成多用户增长比较图表

系统操作：
• /手动抓取 平台 [用户名] - 手动触发数据抓取
• /统计信息 - 查看系统统计信息
• /粉丝帮助 - 显示此帮助信息

支持平台：
• twitter - Twitter/X
• instagram - Instagram

示例：
• /添加用户 twitter kohinatamika
• /用户列表
• /粉丝数据 twitter kohinatamika 5
• /生成图表 instagram kohinata_mika
• /比较图表 twitter:kohinatamika,instagram:kohinata_mika
• /比较图表 twitter:kohinatamika,instagram:kohinata_mika 2024-01-01
• /手动抓取 twitter
"""
    await follower_help.finish(help_text)
