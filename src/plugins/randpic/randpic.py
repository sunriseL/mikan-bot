from httpx import AsyncClient
from nonebot.adapters.onebot.v11 import MessageSegment, Message, GroupMessageEvent
from nonebot.adapters.onebot.v11 import GROUP, GROUP_ADMIN, GROUP_OWNER, GROUP_MEMBER
from nonebot.plugin import on_fullmatch, on_message, on_command, on_shell_command
from nonebot.params import Arg, ArgStr, ShellCommandArgs, Fullmatch, Received, CommandArg, RawCommand, CommandStart
from nonebot.typing import T_State
from nonebot.matcher import Matcher
from nonebot.rule import Namespace, ArgumentParser
from nonebot import get_driver, require
from nonebot.log import logger
from pathlib import Path
from typing import Tuple, List, Set
import asyncio
import hashlib
import aiosqlite
import base64
import os

require("nonebot_plugin_apscheduler")
from nonebot_plugin_apscheduler import scheduler

from .config import Config

__plugin_meta__ = {
    "name": "随机发送图片",
    "description": "发送自定义指令后bot会随机发出一张你所存储的图片",
    "usage": "使用命令：<你设置的指令>",
    "type": "application",
    "homepage": "https://github.com/HuParry/nonebot-plugin-randpic",
    "config": Config,
    "supported_adapters": {"nonebot.adapters.onebot.v11"},
}

# 全局变量
config_dict = Config.parse_obj(get_driver().config.dict())
randpic_path = Path(config_dict.randpic_store_dir_path)
randpic_command_list: List[str] = [path for path in os.listdir(randpic_path) if os.path.isdir(randpic_path / path)]
randpic_command_set: Set[str] = set(randpic_command_list)
randpic_command_tuple: Tuple[str, ...] = tuple(randpic_command_set)
randpic_command_add_tuple = tuple("添加" + tup for tup in randpic_command_tuple)
randpic_command_path_tuple = tuple(randpic_path / command for command in randpic_command_tuple)
randpic_banner_group = config_dict.randpic_banner_group
randpic_alias_dict = {}
per_user_limit = {}
LIMIT = config_dict.randpic_limit_value
hash_str = '3srzmcn0vqp_123'
randpic_filename: str = 'randpic_{command}_{index}'
connection: aiosqlite.Connection

# 定时任务：刷新用户限制
@scheduler.scheduled_job("interval", seconds=config_dict.randpic_limit_interval_seconds, id="refresh_per_user_limit")
async def refresh_per_user_limit():
    logger.info("Refresh per-user limit")
    for id in per_user_limit:
        per_user_limit[id] = LIMIT

# 驱动器
driver = get_driver()

@driver.on_startup
async def _():
    logger.info("正在检查文件...")
    await asyncio.create_task(create_file())
    logger.info("文件检查完成，欢迎使用插件！")

async def create_file():
    """创建所需文件夹和数据库"""
    # 创建文件夹
    for path in randpic_command_path_tuple:
        if not path.exists():
            logger.warning(f'未找到{path}文件夹，准备创建{path}文件夹...')
            path.mkdir(parents=True, exist_ok=True)
    
    # 创建数据库
    global connection
    connection = await aiosqlite.connect(randpic_path / "data.db")
    cursor = await connection.cursor()

    # 创建别名表
    await cursor.execute('''
        CREATE TABLE IF NOT EXISTS Alias (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    await connection.commit()

    # 读取别名表
    try:
        result = await cursor.execute('SELECT key, value FROM Alias')
        rows = await result.fetchall()
        global randpic_alias_dict
        randpic_alias_dict = {row[0]: row[1] for row in rows}
    except Exception as e:
        logger.warning(f"读取别名表失败: {e}")
        randpic_alias_dict = {}

async def create_command(command):
    """创建新的命令文件夹和数据库表"""
    path = randpic_path / command
    if path.exists():
        return
    path.mkdir(parents=True, exist_ok=True)

    randpic_command_list.append(command)
    randpic_command_set.add(command)

    global connection
    cursor = await connection.cursor()

    # 创建表
    await cursor.execute(f'DROP table if exists Pic_of_{command};')
    await cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS Pic_of_{command} (
            md5 TEXT PRIMARY KEY,
            img_url TEXT
        )
        ''')
    await connection.commit()
    
    # 更新全局变量
    global randpic_command_tuple, randpic_command_path_tuple
    randpic_command_tuple = tuple(randpic_command_set)
    randpic_command_path_tuple = tuple(randpic_path / cmd for cmd in randpic_command_tuple)

async def randpic_log(command, caller_id, group_id):
    """记录随机图片使用日志"""
    global connection
    cursor = await connection.cursor()

    await cursor.execute('''
            CREATE TABLE IF NOT EXISTS randpic_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            command TEXT,
            time DATETIME DEFAULT CURRENT_TIMESTAMP,
            caller_id TEXT,
            group_id TEXT
        );
        ''')

    await cursor.execute("INSERT INTO randpic_log (command, caller_id, group_id) VALUES (?, ?, ?)", 
                        (command, caller_id, group_id))
    await connection.commit()

# 消息处理器
msg = on_message(priority=5, block=False)

@msg.handle()
async def msg_handle(event: GroupMessageEvent):
    """处理随机图片请求"""
    if event.group_id in randpic_banner_group:
        return
    
    arg = str(event.get_message()).strip()
    if arg in randpic_command_set:
        command = arg
    elif arg in randpic_alias_dict:
        command = randpic_alias_dict[arg]
    else:
        return

    # 检查用户限制
    if not event.user_id in per_user_limit:
        per_user_limit[event.user_id] = LIMIT

    if per_user_limit[event.user_id] <= 0:
        logger.info(f"{event.user_id} count less equal zero")
        await msg.finish("次数超限，请稍后")

    await randpic_log(command, event.user_id, event.group_id)

    # 获取随机图片
    global connection
    cursor = await connection.cursor()
    await cursor.execute(f'SELECT img_url FROM Pic_of_{command} ORDER BY RANDOM() limit 1')
    data = await cursor.fetchone()
    if data is None:
        await msg.finish('当前还没有图片!')
    
    file_name = data[0]
    # 使用pathlib处理路径，确保跨平台兼容性
    img = randpic_path / Path(file_name)
    with open(img, "rb") as f:
        file_content = f.read()
        encoded_content = base64.b64encode(file_content)
        b64_string = encoded_content.decode('utf-8')
    
    b64_string = "base64://" + b64_string
    try:
        await msg.send(MessageSegment.image(b64_string))
        per_user_limit[event.user_id] -= 1
    except Exception as e:
        logger.info(e)
        await msg.send(f'{command}出不来了，稍后再试试吧~')

# 添加别名命令
add_alias = on_command("添加alias")

@add_alias.handle()
async def add_alias_handler(args: Message = CommandArg()):
    """添加别名"""
    args = str(args).split(" ")
    if len(args) != 2:
        await add_alias.finish("输入格式有误: /添加alias <词条> <alias>")
        return
    
    command = args[0]
    alias = args[1]

    if not command in randpic_command_set:
        await add_alias.finish(f'"{command}"不是合法词条')
        return

    if alias in randpic_command_set:
        await add_alias.finish(f'"{alias}"已为词条')
        return
    
    global connection
    cursor = await connection.cursor()
    await cursor.execute(f"INSERT INTO Alias (key, value) VALUES (?, ?)", (alias, command))
    await connection.commit()

    randpic_alias_dict[alias] = command
    await add_alias.send(f'Alias("{alias}"->"{command}")添加成功')

# 删除别名命令
remove_alias = on_command("删除alias")

@remove_alias.handle()
async def remove_alias_handler(event: GroupMessageEvent, args: Message = CommandArg()):
    """删除别名"""
    if event.user_id != 540729251:
        await remove_alias.finish("无权限执行")
        return

    alias = str(args).strip()
    
    if not alias in randpic_alias_dict:
        await remove_alias.finish(f'"{alias}"不是合法alias')
        return
    
    global connection
    cursor = await connection.cursor()
    await cursor.execute(f"DELETE FROM Alias WHERE key='{alias}'")
    await connection.commit()

    randpic_alias_dict.pop(alias)
    await remove_alias.send(f"{alias}删除成功")

# 添加词条命令
add_keyword = on_command("添加词条")

@add_keyword.handle()
async def add_keyword_handler(event: GroupMessageEvent, args: Message = CommandArg()):
    """添加新词条"""
    if event.user_id != 540729251:
        await add_keyword.finish("无权限执行")
        return
    
    command = str(args)
    await create_command(command)
    await add_keyword.send(f"{command}添加成功")

# 检查统计命令
check_count_parser = ArgumentParser()
check_count_parser.add_argument("--start_time", help="Start time in format YYYY-MM-DD HH:MM:SS", default=None)
check_count_parser.add_argument("--end_time", help="End time in format YYYY-MM-DD HH:MM:SS", default=None)
check_count_parser.add_argument("--group_id", type=int, help="Group ID (integer)", default=None)
check_count_parser.add_argument("--user_id", type=int, help="User ID (integer)", default=None)

check_count = on_shell_command("check_count", parser=check_count_parser)

@check_count.handle()
async def check_count_handler(event: GroupMessageEvent, args: Namespace = ShellCommandArgs()):
    """检查使用统计"""
    group_id = args.group_id if args.group_id else event.group_id
    
    global connection
    cursor = await connection.cursor()
    await cursor.execute('''
        SELECT command, group_id, caller_id, COUNT(*) AS count
        FROM randpic_log
        WHERE group_id = ?
        GROUP BY command, group_id, caller_id;
    ''', (group_id, ))
    result = await cursor.fetchall()
    await cursor.close()
    await check_count.send(str(result))

# 检查词条数量命令
checknsy = on_command("checknsy")

@checknsy.handle()
async def checknsy_handler(event: GroupMessageEvent, args: Message = CommandArg()):
    """检查各词条的图片数量"""
    msg = "\n".join(f"{command}: {len(os.listdir(randpic_path / command))}" 
                   for command in randpic_command_list)
    await checknsy.send(msg)

# 添加图片命令
add = on_command("添加", aliases={"add", "加图"})

@add.handle()
async def add_start(matcher: Matcher, state: T_State, args: Message = CommandArg()):
    """开始添加图片流程"""
    command = str(args[0]).strip()
    if not command in randpic_command_set:
        await add.finish(f'"{command}"词条不存在')
    state["keyword"] = command
    if len(args) > 1:
        matcher.set_arg("pic", args[1:])

@add.got("pic", prompt="请发送图片！")
async def add_pic(state: T_State, pic_list: Message = Arg('pic')):
    """处理图片添加"""
    global connection
    cursor = await connection.cursor()
    command = state["keyword"]

    await create_command(command)

    succ_count = 0
    fail_count = 0

    for pic_name in pic_list:
        if pic_name.type != 'image':
            await add.send(pic_name + MessageSegment.text("\n输入格式有误，请重新触发指令！"), at_sender=True)
            continue
        
        pic_url = pic_name.data['url']

        async with AsyncClient() as client:
            resp = await client.get(pic_url, timeout=5.0)

        try:
            resp.raise_for_status()
        except Exception as e:
            logger.warning(e)
            fail_count += 1
            continue

        data = resp.content
        fmd5 = hashlib.md5(data).hexdigest()

        await cursor.execute(f'SELECT img_url FROM Pic_of_{command} where md5=?', (fmd5,))
        status = await cursor.fetchone()

        if status is not None:
            fail_count += 1
        else:
            without_extension, extension = os.path.splitext(pic_url)
            randpic_cur_picnum = len(os.listdir(randpic_path / command))
            file_name = (randpic_filename.format(command=command, index=str(randpic_cur_picnum + 1))
                        + (extension if extension != '' else '.jpg'))
            file_path = randpic_path / command / file_name

            try:
                with file_path.open("wb") as f:
                    f.write(data)
                # 使用正斜杠确保跨平台兼容性
                db_path = f"{command}/{file_name}".replace("\\", "/")
                await cursor.execute(f'insert or replace into Pic_of_{command}(md5, img_url) values (?, ?)',
                                   (fmd5, db_path))
                await connection.commit()
                succ_count += 1
            except Exception as e:
                logger.warning(e)
                fail_count += 1
    
    await add.send(f"{command}添加完成！成功{succ_count}张，失败{fail_count}张") 