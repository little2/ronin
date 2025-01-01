#!/usr/bin/env python
# pylint: disable=unused-argument

import asyncio
from peewee import PostgresqlDatabase
from playhouse.pool import PooledPostgresqlDatabase
from vendor.class_tgbot import lybot  # 导入自定义的 LYClass
import logging
import os
from telegram import Update
from telegram.ext import Application, MessageHandler, filters

from telethon import TelegramClient, events

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# 检查是否在本地开发环境中运行
if not os.getenv('GITHUB_ACTIONS'):
    from dotenv import load_dotenv
    load_dotenv()

config = {
    'api_id': os.getenv('API_ID'),
    'api_hash': os.getenv('API_HASH'),
    'phone_number': os.getenv('PHONE_NUMBER'),
    'session_name': os.getenv('API_ID') + 'session_name',
    'bot_token': os.getenv('BOT_TOKEN'),
    'dyer_bot_token': os.getenv('DYER_BOT_TOKEN',''),
    'db_name': os.getenv('DB_NAME'),
    'db_user': os.getenv('DB_USER'),
    'db_password': os.getenv('DB_PASSWORD'),
    'db_host': os.getenv('DB_HOST'),
    'db_port': int(os.getenv('DB_PORT',5432)),
    'db_sslmode': os.getenv('DB_SSLMODE','require'),
    'man_bot_id': os.getenv('MAN_BOT_ID'),
    'warehouse_chat_id': int(os.getenv('WAREHOUSE_CHAT_ID'))
}




# MBot
client = TelegramClient(config['session_name'], config['api_id'], config['api_hash'])



# 使用连接池并启用自动重连
db = PooledPostgresqlDatabase(
    config['db_name'],
    user=config['db_user'],
    password=config['db_password'],
    host=config['db_host'],
    port=config['db_port'],
    sslmode=config['db_sslmode'],
    max_connections=32,  # 最大连接数
    stale_timeout=300  # 5 分钟内未使用的连接将被关闭
)


# 初始化 Bot 和 Application
tgbot = lybot(db)
tgbot.config = config
application = Application.builder().token(config['bot_token']).build()
application.add_handler(MessageHandler(filters.ALL, tgbot.handle_bot_message))

dyerbot = lybot(db)
dyerbot.config = config
dyer_application = Application.builder().token(config['dyer_bot_token']).build()
dyer_application.add_handler(MessageHandler(filters.ALL, dyerbot.handle_bot_message))
# 添加消息处理程序






# 主运行函数
async def main():
    # 启动 polling
    
    await tgbot.set_bot_info(application)
    await dyerbot.set_bot_info(dyer_application)

    await application.initialize()
    await application.start()
    await application.updater.start_polling()

    tgbot.dyer_bot_username = dyerbot.bot_username
    tgbot.dyer_application = dyer_application

    await dyer_application.initialize()
    await dyer_application.start()
    await dyer_application.updater.start_polling()

    while True:
        await tgbot.man_bot_loop(client)
        await asyncio.sleep(5)

        if not db.is_closed():
            try:
                db.execute_sql('SELECT 1')
            except Exception as e:
                print(f"Error keeping pool connection alive: {e}")

with client:
    client.loop.run_until_complete(main())
