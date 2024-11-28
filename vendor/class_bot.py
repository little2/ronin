import asyncio
import base64
from collections import defaultdict
import json
import os
import random
import re
import traceback
from telethon import events,types,errors
from telethon.errors import WorkerBusyTooLongRetryError
from telethon.tl.functions.messages import ImportChatInviteRequest
from vendor.wpbot import wp_bot  # 导入 wp_bot
from types import SimpleNamespace
from telethon.tl.types import PeerUser, PeerChat, PeerChannel

class LYClass:

    # 持久化存储最后读取的消息 ID
    LAST_READ_MESSAGE_FILE = "last_read_message_id.json"

    def __init__(self, client, config):
        self.config = config 
        self.client = client
    

    def is_number(self,s):
        return bool(re.match(r'^-?\d+(\.\d+)?$', s))

    # 查找文字，若存在匹配的字串，則根據傳入的參數mode來處理，若mode=tobot,則用 fetch_media_from_enctext 函數處理。若 mode=encstr，則用 forward_encstr_to_encbot 函數處理; 
    async def process_by_check_text(self,message,mode):
        try:
            enc_exist = False
            if message and message.text:
                #宣告 results_dict 為字典
                results_dict = {'results':[]}
                
                
                for bot in wp_bot:   
                    pattern = re.compile(bot['pattern'])
                    matches = pattern.findall(message.text)
                    for match in matches:

                        enc_exist=True
                        
                        if mode == 'encstr':
                            print(f">>send to WorkBOT(QQ): {message.id}-{match}\n", flush=True)
                            async with self.client.conversation(self.config['work_bot_id']) as conv:
                                await conv.send_message(match)
                                # print(match)
                        elif mode == 'request': ## Request the bot to send the material to the user with the peer ID, but it's possible that no bot has the required resources and might not be able to send it in time
                            print(f">>send request to QQ: {message.id}\n", flush=True)
                            print(f"message:{message.peer_id}")
                            async with self.client.conversation(self.config['work_bot_id']) as conv:
                                await conv.send_message(f"|_{message.peer_id.user_id}_|_request_|{match}")
                        elif mode == 'sendToWZ':
                            print(f">>send to Work Zone: {message.id}\n", flush=True)
                            # 当 message.text 存在, 且包含 |_sendToWZ_| ,则把他它移除
                            new_message = message
                            new_message.text = re.sub(r'\|_sendToWZ_\|', '', match)
                            new_message.id = message.id
                            async with self.client.conversation(self.config['work_chat_id']) as conv:
                                await conv.send_message(new_message.text)

                            # await self.wpbot(self.client, new_message, bot['bot_name'],message.peer_id.user_id)
                        elif mode == 'tobot':
                            print(f">>send to Enctext(WP) BOT: {message.id}\n", flush=True)
                            await self.wpbot(self.client, message, bot['bot_name'])
                        elif mode == 'query':
                            # 使用一个新的字典来存储 bot 信息，避免直接修改原始 bot
                            # 先判断 results_dictp['results'] 中是否有相同的 match，如果有，则不再添加
                            
                            # print(f"\nmatch: {match}\n\n")
                            bot_copy = bot.copy()
                            bot_copy['match'] = match
                            
                            
                            if_exist = False
                            for match_item in results_dict['results']:
                                if match_item['match'] == match:
                                    if_exist = True
                                    continue
                            if not if_exist:
                                results_dict['results'].append(bot_copy)
                            enc_exist = False

                return results_dict           
            else:
                print(f"No matching pattern for message: {message.text} {message} \n")
        except Exception as e:
            print(f">>(1)An error occurred while processing message: {e} \n message:{message}\n")
        finally:
            #print(f"enc_exist:{enc_exist}")
            if enc_exist:
                await asyncio.sleep(5)
            else:
                await asyncio.sleep(0)

    # show_caption = yes, no
    async def send_message(self, client, message):
        last_message_id = message.id
        # 构建 caption
        caption_parts = []
        
        # 获取消息来源 组成caption_text 
        if message.message:
            caption_parts.append(f"Original caption: {message.message}")

        if message.chat:
            caption_parts.append(f"<a href='https://t.me/c/{message.chat.id}/{message.id}'>LINK</a>")
            if hasattr(message.chat, 'title'):
                chat_title = message.chat.title
                # chat_title = chat_title.replace(' ', 'ㅤ')
                # chat_title = chat_title.replace("&", "_and_")
                caption_parts.append(f"{chat_title} #C{message.chat.id}")
            else:
                caption_parts.append(f"#C{message.chat.id}")
            

        if message.forward:
            if message.forward.sender_id:
                forward = await client.get_entity(message.forward.sender_id)
                forward_title = f"{forward.first_name} {forward.last_name}"
                if forward.username:
                    caption_parts.append(f"Forwarded from: <a href='https://t.me/{forward.username}'>{forward_title}</a>")
                else:
                    caption_parts.append(f"Forwarded from: <a href='tg://user?id={message.forward.sender_id}'>{forward_title}</a>")
            if message.forward.channel_post:
                caption_parts.append(f"Forwarded message ID: {message.forward.channel_post}")

        if message.from_id:
            sender = await client.get_entity(message.from_id)

            sender_title = f"{sender.first_name}"
            # if sender.last_name is not None then sender_title = f"{sender.first_name} {sender.last_name}"
            if sender.last_name:
                sender_title = f"{sender.first_name} {sender.last_name}"

            if sender.username:
                caption_parts.append(f"Original: <a href='https://t.me/{sender.username}'>{sender_title}</a>")
            else:
                caption_parts.append(f"Original: <a href='tg://user?id={message.from_id.user_id}'>{sender_title}</a>")

        caption_text = "\n".join(caption_parts)

        # 如果配置中设置了不显示 caption，则将 caption_text 设置为 None
        if self.config['show_caption'] == 'no':
            caption_text = None
        
        try:
            # print(f"Message: {message}")

            

            if hasattr(message, 'grouped_id') and message.grouped_id:
                
                # 获取相册中的所有消息
                # print(f"\r\nPeer ID: {message.peer_id}",flush=True)
                album_messages = await client.get_messages(message.peer_id, limit=100, min_id=message.id,reverse=True)
                # print(f"\r\nAlbum messages: {album_messages}",flush=True)

                album = [msg for msg in album_messages if msg.grouped_id == message.grouped_id]
                # print(f"\r\nAlbum: {album}",flush=True)
                if album:
                    await asyncio.sleep(0.5)  # 间隔80秒
                    last_message_id = max(row.id for row in album)
                    # await client.send_file(self.config['warehouse_chat_id'], album, reply_to=message.id, caption=caption_text, parse_mode='html')
                    await client.send_file(self.config['warehouse_chat_id'], album,  caption=caption_text, parse_mode='html')
                    print(f">>Forwarded album:{last_message_id}\n")
                    # print(f"{message.id}")
                    # print(f"{album[0].id}")
                    # print(f"{album[-1].id}")
                    # last_message_id = album[-1].id  # 获取相册中最后一条消息的ID
                    # print(f"Forwarded album:{last_message_id}")
                    #取得阵列album中的id最大值
                    
            elif isinstance(message.media, types.MessageMediaDocument):
                mime_type = message.media.document.mime_type
                if mime_type.startswith('video/'):
                    # 处理视频
                    video = message.media.document
                    # await client.send_file(self.config['warehouse_chat_id'], video, reply_to=message.id, caption=caption_text, parse_mode='html')
                    
                    await client.send_file(self.config['warehouse_chat_id'], video,  caption=caption_text, parse_mode='html')
                    print(">>>>Forwarded video.\n")
                    
                    # 调用新的函数
                    #await self.send_video_to_filetobot_and_publish(client, video, message)
                else:
                    # 处理文档
                    document = message.media.document
                    # await client.send_file(self.config['warehouse_chat_id'], document, reply_to=message.id, caption=caption_text, parse_mode='html')
                    await client.send_file(self.config['warehouse_chat_id'], document,  caption=caption_text, parse_mode='html')
                    print(">>>>Forwarded document.\n")
            elif isinstance(message.media, types.MessageMediaPhoto):
                # 处理图片
                photo = message.media.photo
                await client.send_file(self.config['warehouse_chat_id'], photo,  caption=caption_text, parse_mode='html')
                
                # await client.send_file(self.config['warehouse_chat_id'], photo, reply_to=message.id, caption=caption_text, parse_mode='html')
                print(">>>>Forwarded photo.\n")
            else:
                print("Received media, but not a document, video, photo, or album.")
        except WorkerBusyTooLongRetryError:
            print(f"WorkerBusyTooLongRetryError encountered. Skipping message {message.id}.")
        except Exception as e:
            print(f"An error occurred: {e}")
        return last_message_id

    async def send_video_to_filetobot_and_publish(self, client, video, original_message):
        
        original_message_id = original_message.id

        # 将视频发送到 filetobot 并等待响应
        async with client.conversation('filetobot') as filetobot_conv:
            filetobot_message = await filetobot_conv.send_file(video)
            try:
                # 持续监听，直到接收到媒体文件
                while True:
                    filetobot_response = await asyncio.wait_for(filetobot_conv.get_response(filetobot_message.id), timeout=30)
                    if filetobot_response.media:
                        break
                    else:
                        print(">>>Received text response, waiting for media...")

            except asyncio.TimeoutError:
                await client.send_message(self.config['work_chat_id'], "filetobot timeout", reply_to=original_message_id)
                print("filetobot response timeout.")
                return

            # 将 filetobot 的响应内容传送给 public_bot_id，并设置 caption 为原始消息的文本
            async with client.conversation(self.config['public_bot_id']) as publicbot_conv:
                caption_text = "|_SendToBeach_|\n"+original_message.text+"\n"+filetobot_response.message
                await publicbot_conv.send_file(filetobot_response.media, caption=caption_text)
                print(">>>>Forwarded filetobot response to publish bot with caption.")

    async def send_video_to_filetobot_and_send_to_qing_bot(self, client, video):
        print(">>>>Sending video to filetobot and forwarding to qing bot.")
        # original_message_id = original_message.id

        # 将视频发送到 filetobot 并等待响应
        async with client.conversation('filetobot') as filetobot_conv:
            filetobot_message = await filetobot_conv.send_file(video)
            try:
                # 持续监听，直到接收到媒体文件
                while True:
                    filetobot_response = await asyncio.wait_for(filetobot_conv.get_response(filetobot_message.id), timeout=30)
                    if filetobot_response.media:
                        break
                    else:
                        print(">>>Received text response, waiting for media...")

            except asyncio.TimeoutError:
                # await client.send_message(self.config['work_chat_id'], "filetobot timeout", reply_to=original_message_id)
                print("filetobot response timeout.")
                return

            # 将 filetobot 的响应内容传送给 public_bot_id，并设置 caption 为原始消息的文本
            async with client.conversation(self.config['work_bot_id']) as publicbot_conv:
                # caption_text = "|_SendToBeach_|\n"+original_message.text+"\n"+filetobot_response.message
                await publicbot_conv.send_file(filetobot_response.media, caption=filetobot_response.message)
                print(">>>>Forwarded filetobot response to qing bot with caption.")


    async def wpbot(self, client, message, bot_username, chat_id=None):
        try:
            if chat_id is None:
                chat_id = self.config['work_chat_id']
            async with client.conversation(bot_username) as conv:
                # 根据bot_username 找到 wp_bot 中对应的 bot_name = bot_username 的字典
                bot = next((bot for bot in wp_bot if bot['bot_name'] == bot_username), None)
                if bot['mode'] == 'link':
                    match = re.search(r"(?i)start=([a-zA-Z0-9_]+)", message.text)
                    message.text = '/start ' + match.group(1)

                # 发送消息到机器人
                forwarded_message = await conv.send_message(message.text)
                
                try:
                    # 获取机器人的响应，等待30秒
                    response = await asyncio.wait_for(conv.get_response(forwarded_message.id), timeout=30)
                except asyncio.TimeoutError:
                    # 如果超时，发送超时消息
                    await client.send_message(chat_id, "the bot was timeout", reply_to=message.id)
                    print("Response timeout.")
                    return

                if response.media:
                    if isinstance(response.media, types.MessageMediaDocument):
                        mime_type = response.media.document.mime_type
                        if mime_type.startswith('video/'):
                            # 处理视频
                            video = response.media.document
                            await client.send_file(chat_id, video, reply_to=message.id)
                           
                            print(">>>Reply with video .")

                            #如果 chat_id 不是 work_chat_id，则将视频发送到 qing bot
                            if chat_id != self.config['work_chat_id']:
                                await client.send_file(self.config['work_chat_id'], video)
                            
                            # 调用新的函数
                            #await self.send_video_to_filetobot_and_publish(client, video, message)
                        else:
                            # 处理文档
                            document = response.media.document
                            await client.send_file(chat_id, document, reply_to=message.id)
                          
                            print(">>>Reply with document.")

                            #如果 chat_id 不是 work_chat_id，则将视频发送到 qing bot
                            if chat_id != self.config['work_chat_id']:
                                await client.send_file(self.config['work_chat_id'], document)

                            #caption_text = "|_SendToBeach_|\n"+message.text
                            #await client.send_file(self.config['public_bot_id'], document, caption=caption_text)
                            
                    elif isinstance(response.media, types.MessageMediaPhoto):
                        # 处理图片
                        photo = response.media.photo
                        await client.send_file(chat_id, photo, reply_to=message.id)
                        print(">>>Reply with photo .")

                        #如果 chat_id 不是 work_chat_id，则将视频发送到 qing bot
                        if chat_id != self.config['work_chat_id']:
                            await client.send_file(self.config['work_chat_id'], photo)

                        #caption_text = "|_SendToBeach_|\n"+message.text
                        #await client.send_file(self.config['public_bot_id'], photo, caption=caption_text)
                        
                    else:
                        print("Received media, but not a document, video, or photo.")
                elif response.text:
                    # 处理文本
                    if response.text == "在您发的这条消息中，没有代码可以被解析":
                        await self.wpbot(self.client, message, 'ShowFilesBot',chat_id)
                    elif "💔抱歉，未找到可解析内容。" in response.text:
                        await client.send_message(chat_id, response.text, reply_to=message.id)   
                    elif "不能为你服务" in response.text:
                        await client.send_message(chat_id, "the bot was timeout", reply_to=message.id)
                        
                    elif response.text == "创建者申请了新的分享链接，此链接已过期":
                        await self.wpbot(self.client, message, 'ShowFilesBot',chat_id)
                    elif response.text == "此机器人面向外国用户使用，访问 @MediaBKHome 获取面向国内用户使用的机器人":
                        await self.wpbot(self.client, message, 'ShowFilesBot',chat_id)
                        
                    elif response.text == "access @MediaBKHome to get media backup bot for non-chinese-speaking user":
                        await self.wpbot(self.client, message, 'ShowFilesBot',chat_id)
                    else:
                        print("Received text response: "+response.text)
                    print("Forwarded text.")
                else:
                    print("Received non-media and non-text response")
        except Exception as e:
            print(f"\rAn error occurred: {e}\n")




    async def update_wpbot_data(self, client, message, datapan):
        try:


            if self.config['bot_username'] is not None:
                bot_username = self.config['bot_username']
            else:
                bot_username = 'Qing002BOT'

            print(f"[B]update_wpbot_data\n")
            # print(f"message: {message}\n")
            ck_message = SimpleNamespace()
            ck_message.id = message.id
            ck_message.text = ''
            if message.reply_to_message and message.reply_to_message.text:
                ck_message.text = message.reply_to_message.text
               
            elif message.text:
                ck_message.text = message.text
                
            elif message.caption:
                ck_message.text = message.caption
               

            # print(f"\nck_message: {ck_message}\n")

            if ck_message.text not in ['',' ']:            
                query = await self.process_by_check_text(ck_message,'query')
                # print(f"query: {query}")
                if query:
                    
                    if message.video:
                        file_id = message.video.file_id
                        file_unique_id = message.video.file_unique_id
                        file_type = 'video'
                    elif message.document:
                        file_id = message.document.file_id
                        file_unique_id = message.document.file_unique_id
                        file_type = 'document'    
                    elif message.photo:
                        file_id = message.photo[-1].file_id
                        file_unique_id = message.photo[-1].file_unique_id
                        file_type = 'photo'

                    # 准备插入的数据
                    data = {
                        'enc_str': query['results'][0]['match'],
                        'file_unique_id': file_unique_id,
                        'file_id': file_id,
                        'file_type': file_type,
                        'bot_name': bot_username,
                        'wp_bot': query['results'][0]['bot_name']
                    }

                    # 使用 insert 或者更新功能
                    query_sql = (datapan
                            .insert(**data)
                            .on_conflict(
                                conflict_target=[datapan.enc_str],  # 冲突字段
                                update={datapan.file_unique_id: data['file_unique_id'],
                                        datapan.file_id: data['file_id'],
                                        datapan.bot_name: data['bot_name'],
                                        datapan.wp_bot: data['wp_bot']}
                            ))

                    query_sql.execute()

                    # # 根据 bot 进行排序和分组
                    # bot_dict = defaultdict(list)
                    # for bot_result in query['results']:
                    #     if isinstance(bot_result, dict):
                    #         bot_dict[bot_result['bot_name']].append((bot_result['match'], bot_result['bot_name'], bot_result['mode']))
                    #     else:
                    #         print(f"Unexpected bot_result type: {type(bot_result)} - {bot_result}")


                    # # 展示结果
                    # for bot, entries in sorted(bot_dict.items()):
                    #     # print(f"Bot: {bot}")
                    #     for match, bot_name, mode in entries:
                            
            
        except Exception as e:
            print(f"[B]发生错误: {e}")
            traceback.print_exc()  # 打印完整的 traceback
    

    def save_last_read_message_id(self, chat_id, message_id):
        data = {str(chat_id): message_id}
        if hasattr(self, 'setting') and isinstance(self.setting, dict) and 'last_read_message_content' in self.setting:
            existing_data = self.setting['last_read_message_content']
            if isinstance(existing_data, dict):
                existing_data.update(data)
                data = existing_data
            else:
                print("Error: 'last_read_message_content' is not a dictionary.")

        elif os.path.exists(self.LAST_READ_MESSAGE_FILE):
            with open(self.LAST_READ_MESSAGE_FILE, 'r') as file:
                existing_data = json.load(file)
            existing_data.update(data)
            data = existing_data
        with open(self.LAST_READ_MESSAGE_FILE, 'w') as file:
            json.dump(data, file)

    def load_last_read_message_id(self, chat_id):
        ## 如果 self 存在屬性 setting 且 setting 中存在 last_read_message_content
        if hasattr(self, 'setting'):
            try:
                # decoded_data = base64.urlsafe_b64decode(self.setting['last_read_message_content'].encode('utf-8'))
                # original_content = json.loads(decoded_data.decode('utf-8'))
                # return original_content.get(str(chat_id), 0)  # 返回 0 作为默认值
                return self.setting['last_read_message_content'].get(str(chat_id), 0)  # 返回 0 作为默认值
            except Exception as e:
                print(f"Error loading last read message content: {e}")
                return 0


        elif os.path.exists(self.LAST_READ_MESSAGE_FILE):
            with open(self.LAST_READ_MESSAGE_FILE, 'r') as file:
                data = json.load(file)
                return data.get(str(chat_id), 0)  # 返回 0 作为默认值
        return 0
    
    def get_last_read_message_content(self):
        if os.path.exists(self.LAST_READ_MESSAGE_FILE):
            with open(self.LAST_READ_MESSAGE_FILE, 'r') as file:
                data = json.load(file)
                return data
        return 0

    async def load_tg_setting(self, chat_id, message_thread_id=0):
        try:
            chat_id = self.format_chat_id(chat_id)
            chat_entity = await self.client.get_entity(int(chat_id))
            # print(f"Chat entity found: {chat_entity}")
        except Exception as e:
            print(f"Invalid chat_id: {e}")
            print("Traceback:\r\n")
            traceback.print_exc()  # 打印完整的异常堆栈信息，包含行号
            return None  # 提前返回，避免后续逻辑报错

        # 获取指定聊天的消息，限制只获取一条最新消息
        # 使用 get_messages 获取指定 thread_id 的消息
        try:
            messages = await self.client.get_messages(chat_entity, limit=1, reply_to=message_thread_id)
            # print(f"Messages found: {messages}")
        except Exception as e:
            print(f"Error fetching messages: {e}")
            return
        

   


        if not messages or not messages[0].text:
            return "No messages found."

        # 确认 messages[0] 中否为 json , 若是则返回, 不是则返回 None
        if messages[0].text.startswith('{') and messages[0].text.endswith('}'):
            
            return json.loads(messages[0].text)
        else:
            
            return json.loads("{}")
        

    def format_chat_id(self, chat_id):
        """
        格式化聊天 ID，如果为正数，转换为 Telegram 内部格式
        :param chat_id: 聊天 ID
        :return: 格式化后的聊天 ID
        """
        if self.is_number(str(chat_id)):
            if int(chat_id) > 0:
                return f"-100{chat_id}"
        return chat_id


    async def join_channel_from_link(self, client, invite_link):
        try:
            print(f"Joining channel from link: {invite_link}")
            # 提取邀请链接中的哈希部分
            invite_hash = invite_link.split('/')[-1]

            if invite_hash.startswith('+'):
                invite_hash = invite_hash[1:]
            
            # 通过邀请链接加入群组
            updates = await client(ImportChatInviteRequest(invite_hash))
            print(f"成功加入群组: {updates.chats[0].title}")
            return True
        
        except errors.FloodWaitError as e:
            print(f"BB-A wait of {e.seconds} seconds is required (caused by ImportChatInviteRequest)")
            return False
        except Exception as e:
            print(f"An error occurred: {e}")
            return True





    async def forward_media_to_tlgur(self, client, message):
        # 定义一个包含多个可能值的列表
        bot_usernames = ['tlgur_botbot', 'tIgurbot']

        # 使用 random.choice 随机选择列表中的一个值
        bot_username = random.choice(bot_usernames)
        

        # 检查消息是否包含有效的媒体
        if not message.media or not message.media.photo:
            print("No media found in the message.")
            return
        original_message_id = message.id    
        photo = message.media.photo
        async with client.conversation(bot_username) as conv:



            try:
                # 发送图片
                forwarded_message = await conv.send_file(photo)
                print("File sent, awaiting response...")


                # 循环等待响应并监听消息编辑事件
                while True:
                    try:
                        # 首先等待机器人发送第一次回复（Uploading...）
                        response = await conv.get_response(forwarded_message.id)
                        print(f"Initial response: {response.text}")

                        if "Uploading..." in response.text:
                            print("Received 'Uploading...', now waiting for final URL...")

                            # 等待该消息的修改（例如从 'Uploading...' 到 URL）
                            while True:
                                edited_response = await conv.wait_event(events.MessageEdited(from_users=bot_username))
                                print(f"Edited response: {edited_response.text}")

                                # 检查是否包含网址（假设 URL 格式为 "http" 开头的字符串）
                                url_match = re.search(r'http[s]?://\S+', edited_response.text)
                                if url_match:
                                    await client.send_message(self.config['media_work_chat_id'], edited_response.text, reply_to=original_message_id)
                                    print(f"Final URL received: {url_match.group()}")
                                    break  # 跳出循环，处理完毕

                            break  # 跳出外部循环

                        else:
                            print("Received something else, continuing to wait...")

                    except asyncio.TimeoutError:
                        print("Response timeout.")
                        break  # 跳出循环避免无限等待

                
                    
            except asyncio.exceptions.CancelledError:
                print("The conversation was cancelled.")
                return
            
            except errors.FloodWaitError as e:
                print(f"Flood wait error: {e.seconds} seconds")
                await asyncio.sleep(e.seconds)
            
            except Exception as e:
                print(f"An error occurred: {e}")


    
    async def forward_media_to_tlgur1(self, client, message):   
        bot_username = 'tlgur_botbot' 
        #https://t.me/tIgurbot

       
        photo = message.media.photo
        async with client.conversation(bot_username) as conv:
            forwarded_message = await conv.send_file(photo)

            try:
                # 获取机器人的响应，等待30秒
                response = await asyncio.wait_for(conv.get_response(forwarded_message.id), timeout=30)
                print(f"response: {response}")
            except asyncio.TimeoutError:
                # 如果超时，发送超时消息
                
                print("Response timeout.")
                return


    async def forward_media_to_warehouse(self, client, message):
        try:
            if_send = False
            last_message_id = message.id
            if message.media:
                if message.chat_id != self.config['warehouse_chat_id']:
                    
                    if isinstance(message.media, types.MessageMediaDocument):
                        if not any(isinstance(attr, types.DocumentAttributeSticker) for attr in message.media.document.attributes):
                            # 排除贴图
                            print(f">>>Forwarding document to warehouse chat: {message.id}\n", flush=True)
                            last_message_id = await self.send_message(client, message)
                            if_send=True
                    elif isinstance(message.media, types.MessageMediaPhoto):
                        print(f">>>Forwarding photo to warehouse chat: {message.id}\n", flush=True)
                        last_message_id = await self.send_message(client, message)
                        if_send=True
                    
                    
                else:
                    print(f"Message is from warehouse chat, not forwarding: {message.id}\n", flush=True)
            else:
                print(f"No matching pattern for message: {message.text} {message} \n", flush=True)
        except Exception as e:
            print(f">>(2)An error occurred while processing message: {e} \n message:{message}\n", flush=True)
        finally:
            if if_send:
                await asyncio.sleep(3)
            return last_message_id
        
    def check_strings(self,text):
        # 将字串以,分割成数组  # 定义要检查的关键词
        kw = str(self.config['key_word'])
        keywords = kw.split(",")
        # 编译正则表达式模式
        pattern = re.compile("|".join(keywords))
        # 查找文本中匹配的关键词
        found_keywords = pattern.findall(text)
        return found_keywords