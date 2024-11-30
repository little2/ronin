import base64
from collections import defaultdict
import json
from types import SimpleNamespace
from telethon import TelegramClient, sync
import os
import peewee
from peewee import PostgresqlDatabase, Model, CharField, OperationalError
from playhouse.pool import PooledPostgresqlDatabase

from telegram import Update 
import telegram
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram.constants import ParseMode
from telegram.error import RetryAfter
from telethon.sessions import StringSession
from vendor.class_bot import LYClass  # 导入 LYClass
from vendor.wpbot import wp_bot  # 导入 wp_bot
import asyncio
import time
import random
import re
import traceback
from vendor.class_lycode import LYCode  # 导入 LYClass

from telethon.tl.types import InputMessagesFilterEmpty, Message, User, Chat, Channel, MessageMediaWebPage

##
## 目前问题，卡在 mbot 收到，无法转给 QQBOT



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
        'session_string': os.getenv('SESSION_STRING'),
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
    max_process_time = 60*27  # 27分钟
    max_media_count = 55  # 10个媒体文件
    max_count_per_chat = 11  # 每个对话的最大消息数
    max_break_time = 90  # 休息时间
    

    # 创建 LYClass 实例



    
   
except ValueError:
    print("Environment variable WORK_CHAT_ID or WAREHOUSE_CHAT_ID is not a valid integer.", flush=True)
    exit(1)


# 使用连接池并启用自动重连
db = PooledPostgresqlDatabase(
    os.getenv('DB_NAME'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    host=os.getenv('DB_HOST'),
    port=int(os.getenv('DB_PORT', 5432)),
    sslmode=os.getenv('DB_SSLMODE', 'require'),
    max_connections=32,  # 最大连接数
    stale_timeout=300  # 5 分钟内未使用的连接将被关闭
)

# 定义一个 Peewee 数据模型
class datapan(Model):
    enc_str = CharField(max_length=100, unique=True, null=False)
    file_unique_id = CharField(max_length=50, null=False)
    file_id = CharField(max_length=100, null=False)
    file_type = CharField(max_length=10, null=False)
    bot_name = CharField(max_length=50, null=False)
    wp_bot = CharField(max_length=50, null=False)

    class Meta:
        database = db

# 封装重试逻辑
def retry_atomic(retries=3, base_delay=1):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            global db  # Add this line
            for attempt in range(retries):
                try:
                    # 在 db.atomic() 中进行数据库操作
                    with db.atomic():
                        return await func(*args, **kwargs)
                except (peewee.InterfaceError, OperationalError) as e:
                    delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                    print(f"Database error: {e}. Retrying {attempt + 1}/{retries} after {delay:.2f} seconds...", flush=True)
                    if db.is_closed():
                        db.connect(reuse_if_open=True)
                    time.sleep(delay)
            print("Max retries reached. Operation failed.")
            db.close()
            db = PooledPostgresqlDatabase(
                os.getenv('DB_NAME'),
                user=os.getenv('DB_USER'),
                password=os.getenv('DB_PASSWORD'),
                host=os.getenv('DB_HOST'),
                port=int(os.getenv('DB_PORT', 5432)),
                sslmode=os.getenv('DB_SSLMODE', 'require'),
                max_connections=32,  # 最大连接数
                stale_timeout=300  # 5 分钟内未使用的连接将被关闭
            )

            return None
        return wrapper
    return decorator

def check_connection():
    if db.is_closed():
        db.connect()

# 连接到数据库
check_connection()

# 如果需要，创建表
# db.create_tables([datapan], safe=True)


@retry_atomic(retries=3, base_delay=1)
async def handle_database_operations(match):
    # 执行数据库查询
    print(f"[B]Querying database for {match}...", flush=True)
    return datapan.get_or_none(datapan.enc_str == match)

async def handle_bot_message(update: Update, context) -> None:
    if not update.message:
        print("Update does not contain a message object.")
        return

    message = update.message
    reply_to_message_id = message.message_id
    response = ''
    bot_chat_id = f"-100{config['work_chat_id']}"

    # print(f"Received message: {message}", flush=True)

    # 

    # 处理文本消息
    if message.text:
        
        # 检查是否为私信
        if message.chat.type not in ['private'] and str(message['chat']['id']).strip() not in [str(bot_chat_id).strip()]:
            return
        

        message_type = "文本"
        query = await tgbot.process_by_check_text(message, 'query')
        if query:
            bot_dict = defaultdict(list)
            for bot_result in query['results']:
                if isinstance(bot_result, dict):
                    bot_dict[bot_result['title']].append((bot_result['match'], bot_result['bot_name'], bot_result['mode']))

            # 遍历查询结果，生成回复
            for title, entries in sorted(bot_dict.items()):
                unparse_enc = False
                match_results = ""
                bot_mode = ""
                bot_username = ""

                for match, bot_name, mode in entries:
                    bot_mode = mode 
                    bot_username = bot_name

                    try:
                        if title == 'salai':
                            decode_row = encoder.decode(match)
                            if decode_row['bot'] == config['bot_username']:
                                if decode_row['file_type'] == 'photo':
                                    await context.bot.send_photo(
                                        chat_id=message.chat_id,
                                        photo=decode_row['file_id'],
                                        caption=f"<code>{match}</code>",
                                        reply_to_message_id=reply_to_message_id,
                                        parse_mode=ParseMode.HTML
                                    )
                                elif decode_row['file_type'] == 'video':
                                    await context.bot.send_video(
                                        chat_id=message.chat_id,
                                        video=decode_row['file_id'],
                                        caption=f"<code>{match}</code>",
                                        reply_to_message_id=reply_to_message_id,
                                        parse_mode=ParseMode.HTML
                                    )
                                elif decode_row['file_type'] == 'document':
                                    await context.bot.send_document(
                                        chat_id=message.chat_id,
                                        document=decode_row['file_id'],
                                        caption=f"<code>{match}</code>",
                                        reply_to_message_id=reply_to_message_id,
                                        parse_mode=ParseMode.HTML
                                    )
                         
                            continue

                        # 执行封装的数据库操作
                        
                        if db.is_closed():
                            print("[B]Database connection is closed. Reconnecting...", flush=True)
                            is_show_enc = True
                            check_connection()
                        else:
                            
                            
                            result = await handle_database_operations(match)
                        
                            if result:
                                is_show_enc = False
                                encode_text = encoder.encode(result.file_unique_id, result.file_id, config['bot_username'], result.file_type)
                                reply_caption = f"<code>{encode_text}</code>"
                                # reply_caption = f"<code>{encoder.encode(result.file_unique_id, result.file_id, config['bot_username'], result.file_type)}</code>"
                                
                                try:
                                    print(f"Received text message from man_bot_id {man_bot_id}")
                                    await context.bot.send_message(
                                        chat_id=man_bot_id,
                                        text=encode_text
                                    )
                                except Exception as e:
                                    print(f"Error while sending message: {e}")
                                    traceback.print_exc()


                                

                                if result.file_type == 'photo':
                                    await context.bot.send_photo(
                                        chat_id=message.chat_id,
                                        photo=result.file_id,
                                        caption=reply_caption,
                                        reply_to_message_id=reply_to_message_id,
                                        parse_mode=ParseMode.HTML
                                    )
                                elif result.file_type == 'video':   
                                    await context.bot.send_video(
                                        chat_id=message.chat_id,
                                        video=result.file_id,
                                        caption=reply_caption,
                                        reply_to_message_id=reply_to_message_id,
                                        parse_mode=ParseMode.HTML
                                    )
                                elif result.file_type == 'document':
                                    await context.bot.send_document(
                                        chat_id=message.chat_id,
                                        document=result.file_id,
                                        caption=reply_caption,
                                        reply_to_message_id=reply_to_message_id,
                                        parse_mode=ParseMode.HTML
                                    )
                            else:
                                is_show_enc = True

                        if is_show_enc:
                            unparse_enc = True
                            if bot_mode == 'enctext':
                                match_results += match + "\n"
                            elif bot_mode == 'link':
                                match_results += f"https://t.me/{bot_name}?start={match}\n"
                            await context.bot.send_message(
                                chat_id=f"-100{config['work_chat_id']}",
                                text=match
                            )
                    except RetryAfter as e:
                        retry_after = int(e.retry_after)
                        print(f"Flood control exceeded. Pausing for {retry_after} seconds.")
                        await asyncio.sleep(retry_after)
                        print("Resuming operation after pause.")
                    
                    except Exception as e:
                        print(f"An unexpected error occurred: {e}", flush=True)
                        traceback.print_exc()

                if unparse_enc:
                    if bot_mode == 'enctext':
                        response += f"<pre>{match_results}</pre> via @{bot_username}\n\n"
                    elif bot_mode == 'link':
                        response += f"{match_results}\n\n"

    elif message.photo:
        if db.is_connection_usable():
            print("[B]Photo message received", flush=True)
            await tgbot.update_wpbot_data('', message, datapan)
            encode_text = encoder.encode(message.photo[-1].file_unique_id, message.photo[-1].file_id, config['bot_username'], 'photo');
            reply_caption = f"<code>{encode_text}</code>"
            await context.bot.send_message(
                chat_id=bot_chat_id,
                text=encode_text
            ) 

            # 检查是否为私信
            if message.chat.type in ['private']:
                
                await context.bot.send_photo(
                    chat_id=message.chat_id,
                    photo=message.photo[-1].file_id,
                    caption=reply_caption,
                    reply_to_message_id=reply_to_message_id,
                    parse_mode=ParseMode.HTML
                )
            


    elif message.video:
        if db.is_connection_usable():
            print("[B]Video message received", flush=True)
            await tgbot.update_wpbot_data('', message, datapan)
            encode_text = encoder.encode(message.video.file_unique_id, message.video.file_id, config['bot_username'], 'video')
            reply_caption = f"<code>{encode_text}</code>"


            # 检查是否为私信
            if message.chat.type in ['private']:



                print(f"[B]encode_text: {encode_text}", flush=True)
                await context.bot.send_video(
                    chat_id=message.chat_id,
                    video=message.video.file_id,
                    caption=reply_caption,
                    reply_to_message_id=reply_to_message_id,
                    parse_mode=ParseMode.HTML
                )

            try:
                await context.bot.send_message(
                    chat_id=bot_chat_id,
                    text=encode_text
                )
                print(f"[B]Message sent successfully to Man-BOT-{man_bot_id}")
            except telegram.error.BadRequest as e:
                print(f"[B]BadRequest: {e}. Possible issues with chat_id or message formatting.")
            except telegram.error.Forbidden as e:
                print(f"[B]Forbidden: {e}. Bot might not have permission to send message to {man_bot_id}.")
            except Exception as e:
                print(f"[B]Unexpected error: {e}")


    elif message.document:
        if db.is_connection_usable():
            print("[B]Document message received", flush=True)
            await tgbot.update_wpbot_data('', message, datapan)
            encode_text = encoder.encode(message.document.file_unique_id, message.document.file_id, config['bot_username'], 'document')
            reply_caption = f"<code>{encode_text}</code>"

            # 检查是否为私信
            if message.chat.type in ['private']:

                await context.bot.send_document(
                    chat_id=message.chat_id,
                    document=message.document.file_id,
                    caption=reply_caption,
                    reply_to_message_id=reply_to_message_id,
                    parse_mode=ParseMode.HTML
                )

            await context.bot.send_message(
                chat_id=bot_chat_id,
                text=encode_text
            ) 

    if str(message['chat']['id']).strip() == str(bot_chat_id).strip():
        chat_id = message['chat']['id']
        message_id = message['message_id']
        if message['reply_to_message']:
            reply_to_message_id = message['reply_to_message']['message_id']  
            
            # print(f"chat_id: {chat_id}, message_id: {message_id}, reply_to_message_id: {reply_to_message_id}", flush=True)

            # 删除消息
            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=reply_to_message_id)
                await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
                
            except Exception as e:
                await update.message.reply_text(f"删除失败: {e}")   

       


    if response:
        await update.message.reply_text(response, parse_mode=ParseMode.HTML)


# 创建客户端


# 如果 config 有屬性 session_string 且 值不为空，則使用 session_string 來建立 client
if hasattr(config, 'session_string') and config['session_string']:
    client = TelegramClient(StringSession(config['session_string']), config['api_id'], config['api_hash'])
else:
    session_name = config['session_name']
    


client = TelegramClient(session_name, config['api_id'], config['api_hash'])

application = Application.builder().token(bot_token).build()
# 注册消息处理程序，处理所有消息类型
application.add_handler(MessageHandler(filters.ALL, handle_bot_message))
    
tgbot = LYClass(client,config)

encoder = LYCode()


async def telegram_loop(client, tgbot, max_process_time, max_media_count, max_count_per_chat):
    start_time = time.time()
    media_count = 0

    NEXT_CYCLE = False
    async for dialog in client.iter_dialogs():
        NEXT_DIALOGS = False
        entity = dialog.entity

       

        # 跳过来自 WAREHOUSE_CHAT_ID 的对话
        if entity.id == tgbot.config['warehouse_chat_id']:
            NEXT_DIALOGS = True
            continue

       

        # 如果entity.id 是属于 wp_bot 下的 任一 id, 则跳过
        if entity.id in [int(bot['id']) for bot in wp_bot]:
            
            NEXT_DIALOGS = True
            continue

       

        # 设一个黑名单列表，如果 entity.id 在黑名单列表中，则跳过
        blacklist = []
        enclist = []
        skip_vaildate_list = []

       

        if tgbot.setting['blacklist']:
            blacklist = tgbot.setting['blacklist']

        if entity.id in blacklist:
            NEXT_DIALOGS = True
            continue

        # 打印处理的实体名称（频道或群组的标题）
        if isinstance(entity, Channel) or isinstance(entity, Chat):
            entity_title = entity.title
        elif isinstance(entity, User):
            entity_title = f'{entity.first_name or ""} {entity.last_name or ""}'.strip()
        else:
            entity_title = f'Unknown entity {entity.id}'

        if dialog.unread_count > 0 and (dialog.is_group or dialog.is_channel or dialog.is_user):
            count_per_chat = 0
            time.sleep(0.5)  # 每次请求之间等待0.5秒
            last_read_message_id = tgbot.load_last_read_message_id(entity.id)
            print(f">Reading messages from entity {entity.id}/{entity_title} - {last_read_message_id} - U:{dialog.unread_count} \n", flush=True)

            # iter_messages = await client.get_messages(entity, limit=50, min_id=last_read_message_id, reverse=True)
     

            async for message in client.iter_messages(entity, min_id=last_read_message_id, limit=50, reverse=True, filter=InputMessagesFilterEmpty()):
            # for message in iter_messages:
                NEXT_MESSAGE = False
                if message.id <= last_read_message_id:
                    continue

                last_message_id = message.id  # 初始化 last_message_id

                ## 如果是 media 类型的消息
                if message.media and not isinstance(message.media, MessageMediaWebPage):
                    if dialog.is_user:
                        try:
                            match = re.search(r'\|_forward_\|\s*@([^\s]+)', message.message, re.IGNORECASE)
                            if match:
                                captured_str = match.group(1).strip()
                                if captured_str.isdigit():
                                    if captured_str.startswith('-100'):
                                        captured_str = captured_str.replace('-100', '')
                                    await tgbot.client.send_message(int(captured_str), message)
                                else:
                                    await tgbot.client.send_message(captured_str, message)
                            else:
                                await tgbot.send_video_to_filetobot_and_send_to_qing_bot(client, message)
                        except Exception as e:
                            print(f"Error forwarding message: {e}", flush=True)
                            traceback.print_exc()
                        finally:
                            NEXT_MESSAGE = True

                    if entity.id == tgbot.config['media_work_chat_id']:
                        if media_count >= max_media_count:
                            NEXT_CYCLE = True
                            break

                        if count_per_chat >= max_count_per_chat:
                            NEXT_DIALOGS = True
                            break

                        await tgbot.forward_media_to_tlgur(client, message)
                        media_count += 1
                        count_per_chat += 1
                        last_read_message_id = last_message_id

                    elif tgbot.config['warehouse_chat_id'] != 0 and entity.id != tgbot.config['work_chat_id'] and entity.id != tgbot.config['warehouse_chat_id']:
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
                    try:
                        match = re.search(r'\|_kick_\|\s*(.*?)\s*(bot)', message.text, re.IGNORECASE)
                        if match:
                            botname = match.group(1) + match.group(2)
                            await tgbot.client.send_message(botname, "/start")
                            NEXT_MESSAGE = True
                    except Exception as e:
                        print(f"Error kicking bot: {e}", flush=True)




                    combined_regex = r"(https?://t\.me/(?:joinchat/)?\+?[a-zA-Z0-9_\-]{15,50})|(?<![a-zA-Z0-9_\-])\+[a-zA-Z0-9_\-]{15,17}(?![a-zA-Z0-9_\-])"
                    matches = re.findall(combined_regex, message.text)
                    if matches:
                        for match in matches:
                            match_str = match[0] or match[1]
                            if not match_str.startswith('https://t.me/'):
                                match_str = 'https://t.me/' + match_str

                            if entity.id == tgbot.config['link_chat_id']:
                                join_result = await tgbot.join_channel_from_link(client, match_str)
                                if not join_result:
                                    NEXT_DIALOGS = True
                                    break
                            else:
                                await client.send_message(tgbot.config['work_bot_id'], f"{match_str}")

                    elif entity.id == tgbot.config['work_chat_id']:
                        if media_count >= max_media_count:
                            NEXT_CYCLE = True
                            break

                        if count_per_chat >= max_count_per_chat:
                            NEXT_DIALOGS = True
                            break

                        query = await tgbot.process_by_check_text(message, 'query')
                        if query:
                            for bot_result in query['results']:
                                if isinstance(bot_result, dict):
                                    if(bot_result['title'] == 'salai'):
                                        
                                        async with tgbot.client.conversation(tgbot.config['work_bot_id']) as conv:
                                            await conv.send_message(bot_result['match'])

                                        await tgbot.client.delete_messages(
                                            entity=entity.id,  # 对话的 chat_id
                                            message_ids=message.id  # 刚刚发送消息的 ID
                                        )


                                    else:
                                        await tgbot.process_by_check_text(message, 'tobot')
                                        media_count += 1
                                        count_per_chat += 1

                                    

                                        # bot_dict[bot_result['title']].append((bot_result['match'], bot_result['bot_name'], bot_result['mode']))


                        
                    elif dialog.is_group or dialog.is_channel:
                        if entity.id in enclist:
                            ckresult = tgbot.check_strings(message.text)
                            if ckresult:
                                if media_count >= max_media_count:
                                    NEXT_CYCLE = True
                                    break

                                if count_per_chat >= max_count_per_chat:
                                    NEXT_DIALOGS = True
                                    break

                                await tgbot.process_by_check_text(message, 'encstr')
                                media_count += 1
                                count_per_chat += 1
                        else:
                            if '海水浴场' in message.text:
                                if entity.id in skip_vaildate_list:
                                    continue

                                if isinstance(entity, Channel) or isinstance(entity, Chat):
                                    entity_title = entity.title

                                if message.from_id is not None:
                                    sender = await client.get_entity(message.from_id)
                                    text = "|_SendToProve_|\n" + str(sender.first_name) + "\n" + str(entity_title) + "\n" + str(sender.id)
                                    async with tgbot.client.conversation(tgbot.config['work_bot_id']) as conv:
                                        await conv.send_message(text)
                            else:
                                await tgbot.process_by_check_text(message, 'encstr')
                    elif dialog.is_user:
                       
                    
                        try:
                            if '|_forward_|' in message.text:
                                match = re.search(r'\|_forward_\|\s*@([^\s]+)', message.message, re.IGNORECASE)
                                if match:
                                    captured_str = match.group(1).strip()
                                    if captured_str.isdigit():
                                        if captured_str.startswith('-100'):
                                            captured_str = captured_str.replace('-100', '')
                                        await tgbot.client.send_message(int(captured_str), message)
                                    else:
                                        await tgbot.client.send_message(captured_str, message)
                            elif '|_request_|' in message.text:
                                await tgbot.process_by_check_text(message, 'request')   ##Send to QQBOT with caption
                            elif '|_sendToWZ_|' in message.text:
                                await tgbot.process_by_check_text(message, 'sendToWZ')
                            else:
                                await tgbot.process_by_check_text(message, 'encstr')    ##Send to QQBOT

                        except Exception as e:
                            print(f"Error forwarding message: {e}", flush=True)
                            traceback.print_exc()
                        finally:
                            NEXT_MESSAGE = True

                        

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


    await client.start(phone_number)
    start_time = time.time()
    print(f"\nRestarting\n", flush=True)



    # return
    # 启动 polling
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    print(f"Bot Start Polling\n", flush=True)



    setting_chat_id = tgbot.config['setting_chat_id']
    print(f"Setting chat id: {tgbot.config}", flush=True)
    tgbot.setting = await tgbot.load_tg_setting(setting_chat_id, tgbot.config['setting_tread_id'])


    while True:
        loop_start_time = time.time()
        await telegram_loop(client, tgbot, max_process_time, max_media_count, max_count_per_chat)
        

        if not db.is_closed():
            try:
                db.execute_sql('SELECT 1')
            except Exception as e:
                print(f"Error keeping pool connection alive: {e}")
        


        elapsed_time = time.time() - start_time
        if elapsed_time > max_process_time:
            await application.stop()  # 停止轮询
            print(f"\nStopping main loop after exceeding max_process_time of {max_process_time} seconds.\n", flush=True)
            break

        # input_string = json.dumps(tgbot.get_last_read_message_content())
        # byte_data = input_string.encode('utf-8')
        # tgbot.setting['last_read_message_content'] = base64.urlsafe_b64encode(byte_data).decode('utf-8')
       
        tgbot.setting['last_read_message_content'] = tgbot.get_last_read_message_content()

        # print(f"Last read message content: {tgbot.setting}", flush=True)
        config_str2 = json.dumps(tgbot.setting, indent=2)  # 转换为 JSON 字符串
        async with client.conversation(tgbot.config['setting_chat_id']) as conv:
            await conv.send_message(config_str2, reply_to=tgbot.config['setting_tread_id'])

        loop_elapsed_time = time.time() - loop_start_time
        if loop_elapsed_time < max_break_time:
            print("\nExecution time is " + str(int(elapsed_time)) + f" seconds. Continuing next cycle... after {max_break_time - loop_elapsed_time} seconds.\n\n", flush=True)
        
            print(f"-------------------------------------\n", flush=True)
            await asyncio.sleep(max_break_time - loop_elapsed_time)
           
            


with client:
    client.loop.run_until_complete(main())



