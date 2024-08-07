from telethon import TelegramClient
import os

# 检查是否在本地开发环境中运行
if not os.getenv('GITHUB_ACTIONS'):
    from dotenv import load_dotenv
    load_dotenv()

# 从环境变量中获取值
api_id = os.getenv('API_ID')
api_hash = os.getenv('API_HASH')
phone_number = os.getenv('PHONE_NUMBER')
session_name = api_id + 'session_name'  # 确保与上传的会话文件名匹配

session_file = session_name + '.session'
if os.path.exists(session_file):
    os.remove(session_file)

# 创建客户端
client = TelegramClient(session_name, api_id, api_hash)
client.start(phone_number)