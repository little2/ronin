
import base64
import json
import os
from telethon import TelegramClient,functions
from telethon.tl.types import InputMessagesFilterEmpty, Message, User, Chat, Channel, MessageMediaWebPage


from telethon.errors import UserNotParticipantError



from telethon import TelegramClient, events
from telethon.tl.functions.messages import AddChatUserRequest, CreateChatRequest
from telethon.errors import ChatAdminRequiredError, UserAlreadyParticipantError

from telegram import Update 

from telegram.ext import Application, CommandHandler, CallbackContext, MessageHandler, filters
from telegram.constants import ParseMode

from vendor.class_bot import LYClass  # 导入 LYClass
from vendor.class_lycode import LYCode  # 导入 LYClass
from vendor.wpbot import wp_bot  # 导入 wp_bot
import asyncio
import time
import re
import traceback

# 1.需要关注频道
# 2.先申请加入频道
# 3.到指定群组发送指定定键词，即可核准加入群组

# 3.任意一人用你的群连结进群，即可核准加入群组 (?)

# 3.



# 检查是否在本地开发环境中运行
if not os.getenv('GITHUB_ACTIONS'):
    from dotenv import load_dotenv
    load_dotenv()

try:

    # 从环境变量中获取值
    api_id = os.getenv('API_ID')
    api_hash = os.getenv('API_HASH')
    phone_number = os.getenv('PHONE_NUMBER')
    session_name = api_id + 'session_name'  # 确保与上传的会话文件名匹配
    bot_token = os.getenv('BOT_TOKEN')
    

    man_bot_id =os.getenv('MAN_BOT_ID')


    config = {
        'api_id': os.getenv('API_ID'),
        'api_hash': os.getenv('API_HASH'),
        'phone_number': os.getenv('PHONE_NUMBER'),
        'session_name': os.getenv('API_ID') + 'session_name',
        'work_bot_id': os.getenv('WORK_BOT_ID'),
        'work_chat_id': int(os.getenv('WORK_CHAT_ID', 0)),  # 默认值为0
        'media_work_chat_id': int(os.getenv('MEDIA_WORK_CHAT_ID', 0)),  # 默认值为0
        'public_bot_id': os.getenv('PUBLIC_BOT_ID'),
        'warehouse_chat_id': int(os.getenv('WAREHOUSE_CHAT_ID', 0)),  # 默认值为0
        'link_chat_id': int(os.getenv('LINK_CHAT_ID', 0)),
        'key_word': os.getenv('KEY_WORD'),
        'show_caption': os.getenv('SHOW_CAPTION'),
        'bot_username' : os.getenv('BOT_USERNAME'),
        'setting_chat_id': int(os.getenv('SETTING_CHAT_ID'),0),
        'setting_tread_id': int(os.getenv('SETTING_THREAD_ID'),0)
    }

    

    #max_process_time 設為 600 秒，即 10 分鐘
    max_process_time = 60*27  # 25分钟
    max_media_count = 55  # 10个媒体文件
    max_count_per_chat = 11  # 每个对话的最大消息数
    max_break_time = 90  # 休息时间
    

    # 创建 LYClass 实例



    
   
except ValueError:
    print(f"A ValueError occurred: {e}", flush=True)
   
    exit(1)



async def handle_bot_message(update: Update, context) -> None:
    message = update.message
    reply_to_message_id = message.message_id
    response = ''
    bot_chat_id = f"-100{config['work_chat_id']}"

    # print(f"Received message: {message}", flush=True)

    # 

    # 处理文本消息
    if message.text:
        print("[B]Text message received", flush=True)
        # 检查是否为私信
        if message.chat.type not in ['private'] and str(message['chat']['id']).strip() not in [str(bot_chat_id).strip()]:
            return
        
    elif message.photo:
        print("[B]Photo message received", flush=True)
    elif message.video:
        print("[B]Video message received", flush=True)
    elif message.document:
        print("[B]Document message received", flush=True)

    


    if str(message['chat']['id']).strip() == str(bot_chat_id).strip():
        chat_id = message['chat']['id']
        message_id = message['message_id']
        if message['reply_to_message']:
            reply_to_message_id = message['reply_to_message']['message_id']  

    if response:
        await update.message.reply_text(response, parse_mode=ParseMode.HTML)


# 定义处理 /start 命令的回调函数
async def start(update: Update, context: CallbackContext) -> None:
    # 获取 /start 后面的参数，如果有的话
    print("start")
    if context.args:
        parameter = context.args[0]
        await update.message.reply_text(f"Received parameter: {parameter}")
    else:
        await update.message.reply_text("No parameter provided with /start.")



# # 创建客户端
client = TelegramClient(config['session_name'], config['api_id'], config['api_hash'])

application = Application.builder().token(bot_token).build()

# 注册 /start 命令的处理器
application.add_handler(CommandHandler("start", start))  

# # 注册消息处理程序，处理所有消息类型
application.add_handler(MessageHandler(filters.ALL, handle_bot_message))

  

tgbot = LYClass(client,config)

encoder = LYCode()






async def create_group():
    # 设定群组的名称
    group_name = "My New Group"
    
    # 使用自己的用户名或ID作为初始成员
    # initial_members = [int(man_bot_id)]  # 将 'your_own_username' 替换为您的实际用户名或用户ID
    
    try:
        # 使用 get_entity 获取正确的用户实体
        man_bot_entity = await client.get_entity(int(man_bot_id))
        
        # 创建群组并将获取的实体作为初始成员
        result = await client(CreateChatRequest(users=[man_bot_entity], title=group_name))
        
        # 打印结果，确认返回结构
        print("CreateChatRequest result:", result)
        
        # 检查创建的群组并提取信息
        chat_id = result.updates[1].peer.chat_id  # 提取群组ID
        print(f"Group '{group_name}' created successfully with ID: {chat_id}")
        
    except Exception as e:
        print(f"Failed to create group: {e}")


async def get_latest_message(chat_id: int):

    try:
        chat_entity = await client.get_entity(chat_id)
        print(f"Chat entity found: {chat_entity}")
    except Exception as e:
        print(f"Invalid chat_id: {e}")


    # 获取指定聊天的消息，限制只获取一条最新消息
    async for message in client.iter_messages(chat_id, limit=1):
        if not message or not message.text:
            return "No messages found."
        
    # 按行读取 message.text 的内容，并载入到 config 中
    for line in message.text.splitlines():
        if ':' in line:
            index, value = line.split(':', 1)  # 分割成 index 和 value
            index = index.strip()  # 去掉空格
            value = value.strip()  # 去掉空格
            
            # 尝试将 value 转换为整数并存入 config 中
            try:
                config[index] = int(value)
            except ValueError:
                config[index] = value  # 如果不能转换为整数，保留原字符串值
    print(f"{config}", flush=True)
    return "Config updated with latest message content."



async def telegram_loop(client, tgbot, max_process_time, max_media_count, max_count_per_chat):
    start_time = time.time()
    media_count = 0

    NEXT_CYCLE = False
    async for dialog in client.iter_dialogs():
        NEXT_DIALOGS = False
        entity = dialog.entity

        

        # 设一个黑名单列表，如果 entity.id 在黑名单列表中，则跳过
        blacklist = []
        
        skip_vaildate_list = [2201450328]

        if tgbot.setting['blacklist']:
            blacklist = tgbot.setting['blacklist']

        if tgbot.setting['warehouse_chat_id']:
            tgbot.config['warehouse_chat_id'] = tgbot.setting['warehouse_chat_id']





        if entity.id in blacklist:
            NEXT_DIALOGS = True
            continue

        # 跳过来自 WAREHOUSE_CHAT_ID 的对话
        if entity.id == tgbot.config['warehouse_chat_id']:
            NEXT_DIALOGS = True
            continue

        # 如果entity.id 是属于 wp_bot 下的 任一 id, 则跳过
        if entity.id in [int(bot['id']) for bot in wp_bot]:
            NEXT_DIALOGS = True
            continue

        # 打印处理的实体名称（频道或群组的标题）
        if isinstance(entity, Channel) or isinstance(entity, Chat):
            entity_title = entity.title
        elif isinstance(entity, User):
            entity_title = f'{entity.first_name or ""} {entity.last_name or ""}'.strip()
        else:
            entity_title = f'Unknown entity {entity.id}'

        if dialog.unread_count >= 0 and (dialog.is_group or dialog.is_channel or dialog.is_user):
            count_per_chat = 0
            time.sleep(0.5)  # 每次请求之间等待0.5秒
            last_read_message_id = tgbot.load_last_read_message_id(entity.id)

          

            print(f"\r\n>Reading messages from entity {entity.id}/{entity_title} - {last_read_message_id} - U:{dialog.unread_count} \n", flush=True)

            async for message in client.iter_messages(entity, min_id=last_read_message_id, limit=50, reverse=True, filter=InputMessagesFilterEmpty()):
                NEXT_MESSAGE = False
                if message.id <= last_read_message_id:
                    continue

                last_message_id = message.id  # 初始化 last_message_id

                ## 如果是 media 类型的消息
                if message.media and not isinstance(message.media, MessageMediaWebPage):

                    if tgbot.config['warehouse_chat_id'] != 0 and entity.id != tgbot.config['work_chat_id'] and entity.id != tgbot.config['warehouse_chat_id']:
                        if media_count >= max_media_count:
                            NEXT_CYCLE = True
                            break

                        if count_per_chat >= max_count_per_chat:
                            NEXT_DIALOGS = True
                            break

                        last_message_id = await tgbot.forward_media_to_warehouse(client, message)
                        media_count += 1
                        count_per_chat += 1
                        last_read_message_id = last_message_id
                    else:
                        continue

                ## 如果是 text 类型的消息
                elif message.text:
                    if dialog.is_user: 
                        print(f"Message from {message.peer_id.user_id} in entity {entity.id} - {entity_title}")
                        try:
                            # 检查用户是否在指定频道中
                            is_in_channel = False
                            async for user in client.iter_participants(2496026022):
                                if user.id == message.peer_id.user_id:
                                    is_in_channel = True
                                    break
                            

                            chat_id = 4582586805
                            user_to_add = message.peer_id.user_id
                            # 如果用户不在频道中，批准入群申请
                            if not is_in_channel:
                                await client(AddChatUserRequest(
                                    chat_id,
                                    user_to_add,
                                    fwd_limit=10  # Allow the user to see the 10 last messages
                                ))

                                
                               
                               
                                print(f"User {message.peer_id.user_id} approved to join chat {4582586805}")

                        except Exception as e:
                            print(f"Error checking or approving user: {e}")

                    combined_regex = r"(https?://t\.me/(?:joinchat/)?\+?[a-zA-Z0-9_\-]{15,50})|(?<![a-zA-Z0-9_\-])\+[a-zA-Z0-9_\-]{15,17}(?![a-zA-Z0-9_\-])"
                    matches = re.findall(combined_regex, message.text)
                    if matches:
                        if dialog.is_user:
                            for match in matches:
                                match_str = match[0] or match[1]
                                if not match_str.startswith('https://t.me/'):
                                    match_str = 'https://t.me/' + match_str
                                    join_result = await tgbot.join_channel_from_link(client, match_str)
                                    if not join_result:
                                        NEXT_DIALOGS = True
                                        break
                    elif dialog.is_group or dialog.is_channel:
                    



                        if '海水浴场' in message.text:
                            if entity.id in skip_vaildate_list:
                                continue

                            if isinstance(entity, Channel) or isinstance(entity, Chat):
                                entity_title = entity.title


                tgbot.save_last_read_message_id(entity.id, last_message_id)

                if NEXT_MESSAGE or NEXT_DIALOGS or NEXT_CYCLE:
                    break

        elapsed_time = time.time() - start_time
        if elapsed_time > max_process_time:
            NEXT_CYCLE = True
            break

        if NEXT_DIALOGS or NEXT_CYCLE:
            break

    if NEXT_CYCLE:
        print(f"\nExecution time exceeded {int(max_process_time)} seconds. Stopping. T:{int(elapsed_time)} of {int(max_process_time)} ,C:{media_count} of {max_media_count}\n", flush=True)
       



async def main():


    # await client.start(phone_number)
    start_time = time.time()
    print(f"\nRestarting\n", flush=True)

    # 启动 polling
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    
   

    
    setting_chat_id = tgbot.config['setting_chat_id']
    # print(f"Setting chat id: {tgbot.config}", flush=True)
    



    while True:
        loop_start_time = time.time()
        tgbot.setting = await tgbot.load_tg_setting(setting_chat_id, tgbot.config['setting_tread_id'])

        if tgbot.setting['max_process_time']:
            max_process_time = tgbot.setting['max_process_time']
        if tgbot.setting['max_media_count']:
            max_media_count = tgbot.setting['max_media_count']
        if tgbot.setting['max_count_per_chat']:
            max_count_per_chat = tgbot.setting['max_count_per_chat']
        if tgbot.setting['max_break_time']:
            max_break_time = tgbot.setting['max_break_time']


        await telegram_loop(client, tgbot, max_process_time, max_media_count, max_count_per_chat)
        
        elapsed_time = time.time() - start_time
        if elapsed_time > max_process_time:
            await application.stop()  # 停止轮询
            print(f"\nStopping main loop after exceeding max_process_time of {max_process_time} seconds.\n", flush=True)
            break

        tgbot.setting['last_read_message_content'] = tgbot.get_last_read_message_content()

        # print(f"Last read message content: {tgbot.setting}", flush=True)
        config_str2 = json.dumps(tgbot.setting, indent=2)  # 转换为 JSON 字符串
        async with client.conversation(tgbot.config['setting_chat_id']) as conv:
            await conv.send_message(config_str2, reply_to=tgbot.config['setting_tread_id'])


        print("\nExecution time is " + str(int(elapsed_time)) + f" seconds. Continuing next cycle... after {max_break_time} seconds.\n\n", flush=True)
        print(f"-\n", flush=True)
        print(f"-------------------------------------\n", flush=True)
        await asyncio.sleep(max_break_time)  #间隔180秒
           
with client:
    client.loop.run_until_complete(main())



