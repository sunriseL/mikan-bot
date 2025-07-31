
import aiosqlite
from nonebot import require, get_driver
require("nonebot_plugin_apscheduler")

from nonebot_plugin_apscheduler import scheduler
from nonebot.log import logger
from nonebot import on_command
from nonebot.adapters.onebot.v11 import MessageEvent, MessageSegment, Message
from nonebot.params import CommandArg
import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import asyncio
import requests
import json
import xml.etree.ElementTree as ET
from lxml import etree
from io import BytesIO
import base64
from datetime import datetime

local_connection: aiosqlite.Connection

# 激活驱动器
driver = get_driver()

root_path = "F:\Code\Bot\data"

@driver.on_startup
async def init():
    local_connection = await aiosqlite.connect(root_path + "/" + "follower.db")
    cursor = await local_connection.cursor()
    # await cursor.execute("DROP TABLE IF EXISTS social_media;")
    await cursor.execute('''
    CREATE TABLE IF NOT EXISTS social_media (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    platform TEXT NOT NULL,
    username TEXT NOT NULL,
    follower_count INTEGER NOT NULL,
    time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);''')
    await local_connection.commit()
    return

@scheduler.scheduled_job("interval", seconds=600, id="get_instagram_follower_count", misfire_grace_time=None)
async def get_instagram_follower_count():
    logger.info("Log instagram follower count")

    response = requests.get("https://i.instagram.com/api/v1/users/web_profile_info/?username=kohinata_mika",
                            headers={"User-Agent": "Instagram 76.0.0.15.395 Android (24/7.0; 640dpi; 1440x2560; samsung; SM-G930F; herolte; samsungexynos8890; en_US; 138226743)"},
                            proxies={"http": "http://127.0.0.1:7890", "https": "http://127.0.0.1:7890"})
    result = json.loads(response.text)
    count = result["data"]["user"]["edge_followed_by"]["count"]
    # print(result)
    local_connection = await aiosqlite.connect(root_path + "/" + "follower.db")
    cursor = await local_connection.cursor()
    await cursor.execute(
            "INSERT INTO social_media (platform, username, follower_count) VALUES (?, ?, ?)",
            ("instagram", "kohinata_mika", count),
        )
    await local_connection.commit()
    
@scheduler.scheduled_job("interval", seconds=600, id="get_twitter_follower_count", misfire_grace_time=None)
async def get_twitter_follower_count():
    logger.info("Log twitter follower count")

    response = requests.get("http://172.31.240.1:1200/twitter/user/kohinatamika")
    # print(response.text)
    root = etree.fromstring(response.text.encode("utf-8"))
    # print(root)
    desc = root.xpath("//description")[0].text
    # print(desc)
    desc = desc.replace("- Powered by RSSHub", "")
    result = json.loads(desc)
    # print(result)
    count = result["followers_count"]
    local_connection = await aiosqlite.connect(root_path + "/" + "follower.db")
    cursor = await local_connection.cursor()
    await cursor.execute(
            "INSERT INTO social_media (platform, username, follower_count) VALUES (?, ?, ?)",
            ("twitter", "kohinatamika", count),
        )
    await local_connection.commit()
    

# 注册指令：粉丝趋势
follower_trend = on_command("follower_count", priority=5)

@follower_trend.handle()
async def handle_follower_trend(event: MessageEvent, args: Message = CommandArg()):
    # 解析指令参数
    arg_list = args.extract_plain_text().strip().split()
    if len(arg_list) != 2:
        await follower_trend.finish("用法：/粉丝趋势 平台 用户名\n例如：/粉丝趋势 twitter kohinatamika")
    
    platform, username = arg_list

    try:
        # 连接数据库
        conn = sqlite3.connect(root_path + "/" + "follower.db")
        df = pd.read_sql_query(
            'SELECT platform, username, follower_count, time FROM social_media WHERE platform = ? AND username = ?',
            conn,
            params=(platform, username)
        )
        conn.close()

        if df.empty:
            await follower_trend.finish(f"没有找到平台 {platform} 用户 {username} 的数据。")

        # 处理时间：UTC -> 北京时间
        df['time'] = pd.to_datetime(df['time'], format='%Y-%m-%d %H:%M:%S')
        df['time'] = df['time'].dt.tz_localize('UTC').dt.tz_convert('Asia/Shanghai')
        df['time'] = df['time'].dt.tz_localize(None)

        # 按时间排序
        df = df.sort_values('time')

        # 绘图代码

        # 绘图
        plt.figure(figsize=(14, 6))
        # 图片生成时间：当前时间
        # sns.lineplot(data=df, x='time', y='follower_count', marker='o')
        sns.set(style="whitegrid")
        sns.lineplot(
            data=df, x='time', y='follower_count',
            marker='o', linewidth=1, markersize=5, alpha=0.9, markeredgewidth=0 # 设置点和线的可见性
        )
        generate_time = datetime.now().strftime('Created at: %Y-%m-%d %H:%M:%S')
        plt.text(
            0.99, 0.01, generate_time,
            fontsize=8, color='gray',
            ha='right', va='bottom',
            transform=plt.gca().transAxes  # 相对坐标，保证不随图缩放改变位置
        )
        plt.title(f"{username}-{platform}")
        ax = plt.gca()
        ax.xaxis.set_major_locator(mdates.HourLocator(interval=96))  # 每小时一个刻度
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))  # 格式：年月日 小时:分钟

        plt.xlabel("Time")
        plt.ylabel("Follower Count")
        plt.xticks(rotation=90)
        plt.tight_layout()

        # 保存到内存
        buffer = BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        plt.close()

        # 发送图片
        base64_data = base64.b64encode(buffer.read()).decode()

        await follower_trend.send(MessageSegment.image(f'base64://{base64_data}'))

    except Exception as e:
        await follower_trend.finish(f"出错了：{e}")
