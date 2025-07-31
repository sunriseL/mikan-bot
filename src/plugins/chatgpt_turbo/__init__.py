import base64
import httpx
import nonebot
import json
import os
import copy
import random

from nonebot import on_command, on_message
from nonebot.params import CommandArg
from nonebot.rule import to_me
from nonebot.permission import SUPERUSER
from nonebot.adapters.onebot.v11 import (
    Message,
    MessageSegment,
    PrivateMessageEvent,
    MessageEvent,
    helpers,
    Bot
)
from nonebot.plugin import PluginMetadata
from openai import AsyncOpenAI

from .config import Config, ConfigError
from .prompts import prompt_map, default_key

__plugin_meta__ = PluginMetadata(
    name="支持OneAPI、DeepSeek、OpenAI聊天Bot",
    description="具有上下文关联和多模态识别（OpenAI），适配OneAPI、DeepSeek官方，OpenAI官方的nonebot插件。",
    usage="""
    @机器人发送问题时机器人不具有上下文回复的能力
    chat 使用该命令进行问答时，机器人具有上下文回复的能力
    clear 清除当前用户的聊天记录
    切换 [角色名] 切换角色（仅管理员）
    set_limit [数字] 设置对话上限（仅管理员）
    """,
    config=Config,
    extra={},
    type="application",
    homepage="https://github.com/Alpaca4610/nonebot_plugin_chatgpt_turbo",
    supported_adapters={"~onebot.v11"},
)

# 配置初始化
plugin_config = Config.parse_obj(nonebot.get_driver().config.dict())

# 检查 API 密钥配置
if not plugin_config.oneapi_key or plugin_config.oneapi_key == "your-api-key-here":
    nonebot.logger.warning("ChatGPT Turbo 插件: 未配置 API 密钥，插件将不会正常工作")
    # 不抛出异常，让其他插件正常工作
else:
    # 只有在配置了有效密钥时才初始化客户端
    if plugin_config.oneapi_url:
        client = AsyncOpenAI(
            api_key=plugin_config.oneapi_key, base_url=plugin_config.oneapi_url
        )
    else:
        client = AsyncOpenAI(api_key=plugin_config.oneapi_key)

    model_id = plugin_config.oneapi_model

# 客户端和模型配置已在上面处理

# 会话管理
session = {}
session_limit = {}

# 群组角色管理
PROMPT_FILE = os.path.join(os.path.dirname(__file__), "group_prompts.json")
group_prompts = {}

def load_group_prompts():
    """加载群组角色配置"""
    global group_prompts
    if os.path.exists(PROMPT_FILE):
        with open(PROMPT_FILE, 'r', encoding='utf-8') as f:
            group_prompts = json.load(f)
    if not group_prompts:
        group_prompts["default"] = default_key

def save_group_prompts():
    """保存群组角色配置"""
    with open(PROMPT_FILE, 'w', encoding='utf-8') as f:
        json.dump(group_prompts, f, ensure_ascii=False, indent=2)

# 初始化加载配置
load_group_prompts()

# 事件处理器
chat_record = on_message(rule=to_me(), block=True, priority=99)
clear_request = on_command("clear", block=True, priority=1)
switch_command = on_command("切换", block=True, priority=1, permission=SUPERUSER)
change_limit_request = on_command("set_limit", block=True, priority=1, permission=SUPERUSER)

@switch_command.handle()
async def _(bot: Bot, event: MessageEvent, args: Message = CommandArg()):
    """切换角色命令"""
    group_id = event.get_session_id().split("_")[1]
    prompt_key = args.extract_plain_text().strip()
    
    if prompt_key not in prompt_map:
        await switch_command.finish(f"无效的角色名称: {prompt_key}。可用角色: {', '.join(prompt_map.keys())}")
        
    group_prompts[group_id] = prompt_key
    save_group_prompts()
    
    # 清除现有会话
    if group_id in session:
        del session[group_id]
        
    await switch_command.finish(f"已切换至 {prompt_key}")

@chat_record.handle()
async def _(bot: Bot, event: MessageEvent):
    """带记忆的聊天处理"""
    # 私聊检查
    if isinstance(event, PrivateMessageEvent) and not plugin_config.enable_private_chat:
        await chat_record.finish("对不起，私聊暂不支持此功能。")
    
    content = str(event.get_message())
    img_url = helpers.extract_image_urls(event.message)
    
    if not content or content.strip() == "":
        await chat_record.finish(MessageSegment.text("内容不能为空！"), at_sender=True)
    
    group_id = event.get_session_id().split("_")[1]
    session_id = group_id
    
    # 初始化会话限制
    if session_id not in session_limit:
        session_limit[session_id] = 20
    
    # 会话长度管理
    if session_id in session and len(session[session_id]) > session_limit[session_id]:
        delete_count = random.randint(1, 5)
        session[session_id] = session[session_id][:1] + session[session_id][1 + 2 * delete_count:]
    
    # 初始化会话
    if session_id not in session:
        session[session_id] = []
        current_prompt = group_prompts.get(group_id, default_key)
        session[session_id].append({"role": "system", "content": prompt_map[current_prompt]})

    # 处理文本消息
    if not img_url or "deepseek" in model_id:
        try:
            msgs = copy.deepcopy(session[session_id])
            msgs.append({"role": "user", "content": content})
            response = await client.chat.completions.create(
                model=model_id,
                messages=msgs,
            )
        except Exception as error:
            await chat_record.finish(str(error), at_sender=True)
            
        session[session_id].append({"role": "user", "content": content})
        session[session_id].append({"role": "assistant", "content": response.choices[0].message.content})
        
        # DeepSeek-R1 思维链处理
        if model_id == "deepseek-reasoner" and plugin_config.r1_reason:
            if isinstance(event, PrivateMessageEvent):
                await chat_record.send(
                    MessageSegment.text("思维链\n" + str(response.choices[0].message.reasoning_content)),
                    at_sender=True,
                )
                await chat_record.finish(
                    MessageSegment.text("回复\n" + str(response.choices[0].message.content)),
                    at_sender=True,
                )
            else:
                msgs = []
                msgs.append({
                    "type": "node",
                    "data": {
                        "name": "DeepSeek-R1思维链",
                        "uin": bot.self_id,
                        "content": MessageSegment.text(str(response.choices[0].message.reasoning_content))
                    }
                })
                msgs.append({
                    "type": "node",
                    "data": {
                        "name": "DeepSeek-R1回复",
                        "uin": bot.self_id,
                        "content": MessageSegment.text(str(response.choices[0].message.content))
                    }
                })
                await bot.call_api("send_group_forward_msg", group_id=event.group_id, messages=msgs)
        else:
            await chat_record.finish(
                MessageSegment.text(str(response.choices[0].message.content)),
                at_sender=True,
            )
    else:
        # 处理图片消息
        try:
            image_data = base64.b64encode(
                httpx.get(img_url[0]).content).decode("utf-8")
            session[session_id].append({
                "role": "user",
                "content": [
                    {"type": "text", "text": content},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{image_data}"},
                    },
                ],
            })
            response = await client.chat.completions.create(
                model=model_id, messages=session[session_id]
            )
        except Exception as error:
            await chat_record.finish(str(error), at_sender=True)
        
        await chat_record.finish(
            MessageSegment.text(response.choices[0].message.content), at_sender=True
        )

@clear_request.handle()
async def _(event: MessageEvent):
    """清除历史记录"""
    group_id = event.get_session_id().split("_")[1]
    if group_id in session:
        del session[group_id]
    await clear_request.finish(
        MessageSegment.text("成功清除历史记录！"), at_sender=True
    )

@change_limit_request.handle()
async def _(event: MessageEvent, msg: Message = CommandArg()):
    """设置对话上限"""
    group_id = event.get_session_id().split("_")[1]
    try:
        limit = int(msg.extract_plain_text().strip())
        session_limit[group_id] = limit
        await change_limit_request.finish(
            MessageSegment.text(f"对话上限设置为 {limit}"), at_sender=True
        )
    except ValueError:
        await change_limit_request.finish(
            MessageSegment.text("请输入有效的数字！"), at_sender=True
        ) 