import nonebot
from nonebot import on_command
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import Message, MessageSegment
from nonebot.plugin import PluginMetadata

__plugin_meta__ = PluginMetadata(
    name="帮助系统",
    description="显示所有插件的帮助信息",
    usage="""
/help - 显示所有插件帮助
/help [插件名] - 显示指定插件详细帮助
    """,
    type="application",
    supported_adapters={"~onebot.v11"},
)

# 插件帮助信息
PLUGIN_HELP = {
    "follower": {
        "name": "粉丝数据管理插件",
        "description": "管理社交媒体粉丝数据，支持用户管理、数据查询、图表生成等功能",
        "commands": {
            "/用户列表": "查看所有跟踪的用户",
            "/添加用户 [平台] [用户名]": "添加新用户到跟踪列表",
            "/删除用户 [用户ID]": "删除用户（软删除）",
            "/激活用户 [用户ID]": "激活已删除的用户",
            "/粉丝数据 [平台] [用户名] [数量]": "查看粉丝数据",
            "/最新粉丝": "查看最新粉丝数据",
            "/生成图表 [平台] [用户名]": "生成粉丝趋势图表",
            "/手动抓取 [平台] [用户名]": "手动触发数据抓取",
            "/统计信息": "查看系统统计信息",
            "/粉丝帮助": "显示此帮助信息"
        },
        "aliases": {
            "list_users, 用户列表": "查看用户列表",
            "add_user, 添加用户": "添加用户",
            "delete_user, 删除用户": "删除用户",
            "activate_user, 激活用户": "激活用户",
            "get_followers, 粉丝数据": "查看粉丝数据",
            "get_latest_followers, 最新粉丝": "查看最新数据",
            "generate_chart, 生成图表": "生成图表",
            "manual_fetch, 手动抓取": "手动抓取",
            "get_stats, 统计信息": "查看统计",
            "follower_help, 粉丝帮助": "帮助信息"
        },
        "examples": [
            "/添加用户 twitter kohinatamika",
            "/用户列表",
            "/粉丝数据 twitter kohinatamika 5",
            "/生成图表 instagram kohinata_mika",
            "/手动抓取 twitter"
        ],
        "platforms": ["Twitter/X", "Instagram"]
    },
    "chatgpt_turbo": {
        "name": "ChatGPT Turbo 聊天插件",
        "description": "支持OneAPI、DeepSeek、OpenAI的智能聊天机器人，具有上下文记忆和多模态识别功能",
        "commands": {
            "@机器人 [消息]": "与机器人对话（带上下文记忆）",
            "clear": "清除当前群组的聊天记录",
            "切换 [角色名]": "切换角色（仅管理员）",
            "set_limit [数字]": "设置对话上限（仅管理员）"
        },
        "roles": ["小日向美香（默认）", "樱井阳菜", "铃原希实", "羊宫妃那"],
        "examples": [
            "@机器人 你好！",
            "切换 樱井阳菜",
            "clear",
            "set_limit 30"
        ]
    },
    "randpic": {
        "name": "随机图片插件",
        "description": "支持自定义词条和别名的随机图片发送插件",
        "commands": {
            "[词条名]": "发送对应词条的随机图片",
            "/添加 [词条名]": "向指定词条添加图片",
            "/添加词条 [词条名]": "创建新词条（需要管理员权限）",
            "/添加alias [词条名] [别名]": "为词条添加别名",
            "/删除alias [别名]": "删除别名（需要管理员权限）",
            "/checknsy": "查看各词条的图片数量",
            "/check_count [参数]": "查看使用统计"
        },
        "examples": [
            "capoo",
            "/添加 capoo",
            "/添加词条 meme",
            "/checknsy"
        ]
    }
}

# 创建帮助命令
help_cmd = on_command("help", aliases={"帮助", "帮助信息"}, priority=5, block=True)

@help_cmd.handle()
async def handle_help(event, args: Message = CommandArg()):
    """处理帮助命令"""
    plugin_name = args.extract_plain_text().strip().lower()
    
    if not plugin_name:
        # 显示所有插件概览
        await show_all_plugins(event)
    else:
        # 显示指定插件详细帮助
        await show_plugin_detail(event, plugin_name)

async def show_all_plugins(event):
    """显示所有插件概览"""
    help_text = "🤖 **机器人插件帮助系统**\n\n"
    help_text += "📋 **可用插件列表：**\n\n"
    
    for key, plugin in PLUGIN_HELP.items():
        help_text += f"🔹 **{plugin['name']}** (`{key}`)\n"
        help_text += f"   {plugin['description']}\n\n"
    
    help_text += "💡 **使用方法：**\n"
    help_text += "• `/help` - 显示此帮助信息\n"
    help_text += "• `/help [插件名]` - 显示指定插件详细帮助\n"
    help_text += "• 例如：`/help follower`、`/help chatgpt_turbo`、`/help randpic`\n\n"
    help_text += "🎯 **快速开始：**\n"
    help_text += "• 粉丝数据：`/添加用户 twitter kohinatamika`\n"
    help_text += "• 智能聊天：`@机器人 你好！`\n"
    help_text += "• 随机图片：发送 `capoo` 获取随机图片"
    
    await help_cmd.finish(Message(help_text))

async def show_plugin_detail(event, plugin_name: str):
    """显示指定插件详细帮助"""
    if plugin_name not in PLUGIN_HELP:
        await help_cmd.finish(f"❌ 未找到插件：{plugin_name}\n\n💡 使用 `/help` 查看所有可用插件")
    
    plugin = PLUGIN_HELP[plugin_name]
    
    help_text = f"📖 **{plugin['name']}** 详细帮助\n\n"
    help_text += f"📝 **描述：** {plugin['description']}\n\n"
    
    # 命令列表
    help_text += "🔧 **可用命令：**\n"
    for cmd, desc in plugin['commands'].items():
        help_text += f"• `{cmd}` - {desc}\n"
    help_text += "\n"
    
    # 别名（如果有）
    if 'aliases' in plugin:
        help_text += "🔄 **命令别名：**\n"
        for aliases, desc in plugin['aliases'].items():
            help_text += f"• `{aliases}` - {desc}\n"
        help_text += "\n"
    
    # 角色（如果有）
    if 'roles' in plugin:
        help_text += "👥 **可用角色：**\n"
        for role in plugin['roles']:
            help_text += f"• {role}\n"
        help_text += "\n"
    
    # 平台（如果有）
    if 'platforms' in plugin:
        help_text += "🌐 **支持平台：**\n"
        for platform in plugin['platforms']:
            help_text += f"• {platform}\n"
        help_text += "\n"
    
    # 使用示例
    if 'examples' in plugin:
        help_text += "💡 **使用示例：**\n"
        for example in plugin['examples']:
            help_text += f"• `{example}`\n"
        help_text += "\n"
    
    help_text += "🔙 返回总览：`/help`"
    
    await help_cmd.finish(Message(help_text)) 