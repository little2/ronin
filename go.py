from telethon import errors

import json
from telethon import TelegramClient, sync
import os
from vendor.class_bot import LYClass  # 导入 LYClass
from vendor.wpbot import wp_bot  # 导入 wp_bot
import asyncio
import time
import re
import traceback

from telethon.tl.types import InputMessagesFilterEmpty, Message, User, Chat, Channel, MessageMediaWebPage

# 检查是否在本地开发环境中运行
if not os.getenv('GITHUB_ACTIONS'):
    from dotenv import load_dotenv
    load_dotenv()

# 从环境变量中获取值
api_id = os.getenv('API_ID')
api_hash = os.getenv('API_HASH')
phone_number = os.getenv('PHONE_NUMBER')
session_name = api_id + 'session_name'  # 确保与上传的会话文件名匹配

# 创建客户端
client = TelegramClient(session_name, api_id, api_hash)

try:
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
        'setting_chat_id': int(os.getenv('SETTING_CHAT_ID'),0),
        'setting_tread_id': int(os.getenv('SETTING_THREAD_ID'),0),
        'show_caption': os.getenv('SHOW_CAPTION')
    }

    # 创建 LYClass 实例
    tgbot = LYClass(client,config)
    
   
except ValueError:
    print("Environment variable WORK_CHAT_ID or WAREHOUSE_CHAT_ID is not a valid integer.", flush=True)
    exit(1)
    
#max_process_time 設為 600 秒，即 10 分鐘
max_process_time = 1500  # 10分钟
max_media_count = 55  # 10个媒体文件
max_count_per_chat = 11  # 每个对话的最大消息数
max_break_time = 90  # 休息时间


async def validate_chat(client, chat_id):
    try:
        # 跳过特殊系统 ID
        if str(chat_id) == "777000":
            print("777000 is a system ID, skipping validation.")
            return True

        # 获取实体
        entity = await client.get_entity(chat_id)
        print(f"Chat ID {chat_id} exists. Entity: {entity.title if hasattr(entity, 'title') else 'User'}")

        # 根据实体类型进一步处理
        if isinstance(entity, Channel) or isinstance(entity, Chat):
            # 检查是否有权限查看成员
            me = await client.get_me()  # 获取当前 Bot 用户
            async for user in client.iter_participants(chat_id):
                if user.id == me.id:  # 检查自己是否是成员
                    print(f"Bot is a member of {entity.title}")
                    return True
            print(f"Bot is not a member of {entity.title}")
            return False
        elif isinstance(entity, User):
            print(f"Chat ID {chat_id} is a valid User: {entity.first_name}")
            return True
        else:
            print(f"Unknown chat type for Chat ID {chat_id}")
    except errors.RPCError as e:
        print(f"Chat ID {chat_id} is invalid or inaccessible. Error: {e}")
    except ValueError as e:
        print(f"Chat ID {chat_id} is not valid. Error: {e}")
        # traceback.print_exc()  # 打印完整的异常堆栈信息
    return False

async def process_chats(client, data):
    last_read_message_content = data.get("last_read_message_content", {}).copy()

    for chat_id in list(last_read_message_content.keys()):
        
        is_valid = await validate_chat(client, int(chat_id))
        if not is_valid:
            # 移除无效 chat_id
            last_read_message_content.pop(chat_id, None)
    
    # 更新数据
    data["last_read_message_content"] = last_read_message_content

    # 尝试发送数据到指定会话
    try:
        config_str2 = json.dumps(data, indent=2)
        async with client.conversation(tgbot.config['setting_chat_id']) as conv:
            await conv.send_message(config_str2, reply_to=tgbot.config['setting_tread_id'])
    except Exception as e:
        print(f"Error sending message to setting_chat_id: {e}", flush=True)

    return data



async def process_chats2(client, data):
    last_read_message_content = data["last_read_message_content"]
    last_read_message_content2 = data["last_read_message_content"]
    blacklist = data["blacklist"]

    # 用于存储需要删除的 chat_id
    to_remove = []

    # 遍历 last_read_message_content
    for chat_id, message_id in last_read_message_content.copy().items():
        try:
            # 检查 chat_id 是否有效
            entity = await client.get_entity(int(chat_id))  # 获取 chat_id 的实体
            print(f"Chat ID {chat_id} exists. Entity: {entity.title if hasattr(entity, 'title') else 'User'}")
        
        except errors.RPCError as e:
            # 若 chat_id 不存在，记录下来
            print(f"Chat ID {chat_id} does not exist or user is not in it. Error: {e}")
           
            last_read_message_content.pop(chat_id, None)
            data["last_read_message_content"] = last_read_message_content
            continue  # 继续处理下一个 chat_id 

        except ValueError:
            # 若 chat_id 无效（非数字或解析失败）
            print(f"Chat ID {chat_id} is invalid.")
            to_remove.append(chat_id)
            last_read_message_content.pop(chat_id, None)
            data["last_read_message_content"] = last_read_message_content
            
            continue  # 继续处理下一个 chat_id  

    try:
        config_str2 = json.dumps(data, indent=2)  # 转换为 JSON 字符串
        async with client.conversation(tgbot.config['setting_chat_id']) as conv:
            await conv.send_message(config_str2, reply_to=tgbot.config['setting_tread_id'])
    except Exception as e:
        print(f"Error sending message to setting_chat_id: {e}", flush=True)

    # 更新 JSON 数据
    data["last_read_message_content"] = last_read_message_content
    return data

async def main():
    await client.start(phone_number)
    start_time = time.time()
    media_count = 0
    
    try:
        await tgbot.client.send_message(tgbot.config['work_bot_id'], "/start")
    except Exception as e:
        print(f"Error sending message to work_bot_id: {e}", flush=True)
        return
    
    setting_chat_id = tgbot.config['setting_chat_id']
    
    tgbot.setting = await tgbot.load_tg_setting(setting_chat_id, tgbot.config['setting_tread_id'])
    
    # tgbot.setting = await process_chats(client, tgbot.setting)
    # print("Updated JSON:", tgbot.setting)

    while True:
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

            # 若setting中有blacklist，则使用setting中的blacklist



            # 如果 tgbot.setting 不存在，使用空字典作为默认值
            blacklist = (tgbot.setting or {}).get('blacklist', [])
            
            if tgbot.setting['warehouse_chat_id']:
                tgbot.config['warehouse_chat_id'] = int(tgbot.setting['warehouse_chat_id'])

            enclist = []

            skip_vaildate_list =[]

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
                
            

            if dialog.unread_count >= 0 and (dialog.is_group or dialog.is_channel or dialog.is_user):
                count_per_chat=0

                time.sleep(0.5)  # 每次请求之间等待0.5秒

                # if entity.id == tgbot.config['work_chat_id']:
                #     last_read_message_id = 14244
                # else:
                last_read_message_id = tgbot.load_last_read_message_id(entity.id)
                          
                print(f"\r\n>Reading messages from entity {entity.id}/{entity_title} - {last_read_message_id} - U:{dialog.unread_count} \n", flush=True)
                async for message in client.iter_messages(entity, min_id=last_read_message_id, limit=50, reverse=True, filter=InputMessagesFilterEmpty()):
                    NEXT_MESSAGE = False
                    #如果 message.message 是 "doc+vzvd_WpvvhUc0tI+2wYG_RQAAsU=_mda"，则跳过
                    if message.message == "doc+vzvd_WpvvhUc0tI+2wYG_RQAAsU=_mda":
                        continue

                    if message.id <= last_read_message_id:
                        continue
                   
                    last_message_id = message.id  # 初始化 last_message_id
                   
                    ##### 当前消息是媒体文件，且不是网页 #####
                    if message.media and not isinstance(message.media, MessageMediaWebPage):
                        if dialog.is_user:
                            # 使用正则表达式进行匹配，忽略大小写
                            try:
                                # 正则表达式匹配 |_forward_|@ 之后的字符串
                                match = re.search(r'\|_forward_\|\s*@([^\s]+)', message.message, re.IGNORECASE)
                                
                                if match:
                                    captured_str = match.group(1).strip()  # 捕获到的字符串
                                    print(f"Captured string: {captured_str}")
                                    
                                    # 判断是否为数字
                                    if tgbot.is_number(captured_str):
                                        print(f"Forward to number: {captured_str}")
                                        #如何captured_str是-100开头，则拿掉-100，再转成整数发送
                                        if captured_str.startswith('-100'):
                                            captured_str = captured_str.replace('-100','')
                                        
                                        message.text = ''
                                        await tgbot.client.send_message(int(captured_str), message)  # 如果是数字，转成整数发送
                                    else:
                                        print(f"Forward to bot: {captured_str}")
                                        await tgbot.client.send_message(captured_str, message)  # 如果不是数字，按字符串发送
                                else:
                                    # 如果没有匹配到正则，走默认的处理逻辑
                                    await tgbot.send_video_to_filetobot_and_send_to_qing_bot(client, message)
                            except Exception as e:
                                print(f"Error forwarding message: {e}", flush=True)
                                traceback.print_exc()  # 打印完整的异常堆栈信息
                                
                            finally:
                                NEXT_MESSAGE = True


                            
                        if entity.id == tgbot.config['media_work_chat_id']:    
                            if media_count >= max_media_count:
                                NEXT_CYCLE = True
                                break
                            
                            if count_per_chat >= max_count_per_chat:
                                NEXT_DIALOGS = True
                                break


                            await tgbot.forward_media_to_tlgur(client,message)

                            # print(f"last_message_id: {last_message_id}")
                            media_count = media_count + 1
                            count_per_chat = count_per_chat +1
                            last_read_message_id = last_message_id

                        elif entity.id == 827297596:
                            print(f"{entity.id} \n", flush=True)
                            async with client.conversation(1808436284) as conv:
                                photo = message.media.photo
                                
                                forwarded_message = await conv.send_file(photo)
                                print(f"forwarded_message: {message} {message.id}")
                                await client.delete_messages(entity.id, message.id)
                             


                        elif tgbot.config['warehouse_chat_id']!=0 and entity.id != tgbot.config['work_chat_id'] and entity.id != tgbot.config['warehouse_chat_id']:
                            
                            if media_count >= max_media_count:
                                NEXT_CYCLE = True
                                break
                            
                            if count_per_chat >= max_count_per_chat:
                                NEXT_DIALOGS = True
                                break

                            last_message_id = await tgbot.forward_media_to_warehouse(client,message)
                            
                            # print(f"\r\n@>{dialog}", flush=True)

                            
                            
                            # print(f"last_message_id: {last_message_id}")
                            media_count = media_count + 1
                            count_per_chat = count_per_chat +1
                            last_read_message_id = last_message_id
                        else:
                            if tgbot.config['warehouse_chat_id']!=0:
                                print(f"Media from warehouse is empty \n", flush=True)
                            elif entity.id == tgbot.config['work_chat_id']:
                                print(f"skipping work_chat\n", flush=True)
                            elif entity.id == tgbot.config['warehouse_chat_id']:
                                print(f"skipping warehouse\n", flush=True)
                               

                                
                           

                    elif message.text:
                       
                        # 使用正则表达式进行匹配，忽略大小写
                        try:
                            match = re.search(r'\|_kick_\|\s*(.*?)\s*(bot)', message.text, re.IGNORECASE)
                            if match:
                                botname = match.group(1) + match.group(2)  # 直接拼接捕获的组
                                print(f"Kick:{botname}")
                                await tgbot.client.send_message(botname, "/start")
                                NEXT_MESSAGE = True
                        except Exception as e:
                            print(f"Error kicking bot: {e}", flush=True)
                            

                        # print(f">>>Reading TEXT from entity {entity.id}/{entity_title} - {message}\n")
                        regex1 = r"https?://t\.me/(?:joinchat/)?\+?[a-zA-Z0-9_\-]{15,50}"
                        regex2 = r"(?<![a-zA-Z0-9_\-])\+[a-zA-Z0-9_\-]{15,17}(?![a-zA-Z0-9_\-])"

                        # 合并两个正则表达式
                        combined_regex = rf"({regex1})|({regex2})"

                        # pattern = r'(https?://t\.me/(?:joinchat/)?\+?[a-zA-Z0-9_\-]{15,50}|\+?[a-zA-Z0-9_\-]{15,17})'
                        matches = re.findall(combined_regex, message.text)
                        # matches = re.findall(pattern, message.text)
                        if matches:
                            for match in matches:
                                match_str = match[0] or match[1]
                                if not match_str.startswith('https://t.me/'):
                                    match_str = 'https://t.me/' + match_str

                                if entity.id == tgbot.config['link_chat_id']:
                                    # print(f"'{message.text}' ->matches: {match_str}. =>join\n")
                                    join_result = await tgbot.join_channel_from_link(client, match_str)  
                                    if not join_result:
                                        print(f"Failed to join channel from link: {match_str}", flush=True)
                                        NEXT_DIALOGS = True
                                        break
                                else:
                                    # print(f"'{message.text}' ->matches: {match_str}  {entity.id} {tgbot.config['link_chat_id']}. =>forward\n")
                                    if match_str not in ['https://t.me/FilesDrive_BLGA_bot']:
                                        await client.send_message(tgbot.config['work_bot_id'], f"{match_str}")  
                            # print(f"matches: 178\n")
                               
                                     
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
                                            
                                            await tgbot.client.delete_messages(
                                                entity=entity.id,  # 对话的 chat_id
                                                message_ids=message.id  # 刚刚发送消息的 ID
                                            )


                                        else:
                                            await tgbot.process_by_check_text(message, 'tobot')
                                            media_count += 1
                                            count_per_chat += 1

                        elif dialog.is_group or dialog.is_channel:
                        
                            if entity.id in enclist:
                                # 检查字符串中的关键词
                                
                                ckresult = tgbot.check_strings(message.text)
                                if ckresult:
                                    # print(f"===============\n{message}\n===============\n")
                                    if media_count >= max_media_count:
                                        NEXT_CYCLE = True
                                        break
                                    
                                    if count_per_chat >= max_count_per_chat:
                                        NEXT_DIALOGS = True
                                        break


                                    await tgbot.process_by_check_text(message,'encstr')
                                    media_count = media_count + 1
                                    count_per_chat = count_per_chat +1
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
                                        print(f"Message from entity {entity.id} has no sender.", flush=True)
                                else:
                                    await tgbot.process_by_check_text(message,'encstr')
                        elif dialog.is_user:
                            if '|_request_|' in message.text:
                                await tgbot.process_by_check_text(message,'request')
                            elif '|_sendToWZ_|' in message.text:
                                await tgbot.process_by_check_text(message,'sendToWZ')
                            else:
                                await tgbot.process_by_check_text(message,'encstr')
                            


                           
                    tgbot.save_last_read_message_id(entity.id, last_message_id)

                    if NEXT_MESSAGE or NEXT_DIALOGS or NEXT_CYCLE:
                        # print(f"matches: 218\n")
                        break   


            elapsed_time = time.time() - start_time
            if elapsed_time > max_process_time:  
                NEXT_CYCLE = True
                break                
            
            if  NEXT_DIALOGS or NEXT_CYCLE:
                break 



        if NEXT_CYCLE:
            print(f"\nExecution time exceeded {int(max_process_time)} seconds. Stopping. T:{int(elapsed_time)} of {int(max_process_time)} ,C:{media_count} of {max_media_count}\n", flush=True)
            print(f"-\n", flush=True)
            #await tgbot.client.send_message(tgbot.config['warehouse_chat_id'], tgbot.get_last_read_message_content())
            break
        



        config_str2 = json.dumps(tgbot.setting, indent=2)  # 转换为 JSON 字符串
        async with client.conversation(tgbot.config['setting_chat_id']) as conv:
            await conv.send_message(config_str2, reply_to=tgbot.config['setting_tread_id'])

        print("\nExecution time is " + str(int(elapsed_time)) + f" seconds. Continuing next cycle... after {max_break_time} seconds.\n\n", flush=True)
        print(f"-\n", flush=True)
        print(f"-------------------------------------\n", flush=True)
        await asyncio.sleep(max_break_time)  # 间隔180秒
        media_count = 0

with client:
    client.loop.run_until_complete(main())
