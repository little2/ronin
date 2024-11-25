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



async def main():
    await client.start(phone_number)
    start_time = time.time()
    media_count = 0
    
    try:
        await tgbot.client.send_message(tgbot.config['work_bot_id'], "/start")
    except Exception as e:
        print(f"Error sending message to work_bot_id: {e}", flush=True)
        return
    

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
            blacklist = [2131062766, 1766929647, 1781549078, 6701952909, 6366395646,93372553,2197546676, 2022425523]  # Example blacklist with entity IDs
            # blacklist = [2154650877,2190384328,2098764817,1647589965,1731239234,1877274724,2131062766, 1766929647, 1781549078, 6701952909, 6366395646,93372553,2215190216,2239552986,2215190216,2171778803,1704752058]

            enclist = [2012816724,2239552986,2215190216,7061290326,2175483382,2252083262] 

            skip_vaildate_list =[2201450328]

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
                count_per_chat=0

                time.sleep(0.5)  # 每次请求之间等待0.5秒

                # if entity.id == tgbot.config['work_chat_id']:
                #     last_read_message_id = 14244
                # else:
                last_read_message_id = tgbot.load_last_read_message_id(entity.id)
                          
                print(f"\r\n>Reading messages from entity {entity.id}/{entity_title} - {last_read_message_id} - U:{dialog.unread_count} \n", flush=True)
                async for message in client.iter_messages(entity, min_id=last_read_message_id, limit=50, reverse=True, filter=InputMessagesFilterEmpty()):
                    NEXT_MESSAGE = False
                   
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
        



        print("\nExecution time is " + str(int(elapsed_time)) + f" seconds. Continuing next cycle... after {max_break_time} seconds.\n\n", flush=True)
        print(f"-\n", flush=True)
        print(f"-------------------------------------\n", flush=True)
        await asyncio.sleep(max_break_time)  # 间隔180秒
        media_count = 0

with client:
    client.loop.run_until_complete(main())
