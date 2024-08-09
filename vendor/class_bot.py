
from telethon import types,errors
import asyncio
import json
import os
import re
from telethon.errors import WorkerBusyTooLongRetryError
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import ImportChatInviteRequest
from vendor.wpbot import wp_bot  # 导入 wp_bot

class LYClass:

    # 持久化存储最后读取的消息 ID
    LAST_READ_MESSAGE_FILE = "last_read_message_id.json"

    def __init__(self, client, config):
        self.config = config 
        self.client = client
        

    # 查找文字，若存在匹配的字串，則根據傳入的參數mode來處理，若mode=tobot,則用 fetch_media_from_enctext 函數處理。若 mode=encstr，則用 forward_encstr_to_encbot 函數處理; 
    async def process_by_check_text(self,message,mode):
        try:
            enc_exist = False
            if message.text:
                for bot in wp_bot:
                    pattern = re.compile(bot['pattern'])
                    matches = pattern.findall(message.text)
                    for match in matches:
                        enc_exist=True
                        if mode == 'encstr':
                            print(f">>send to QQ: {message.id}\n")
                            async with self.client.conversation(self.config['work_bot_id']) as conv:
                                await conv.send_message(match)
                                # print(match)
                        elif mode == 'tobot':
                            print(f">>send to Enctext BOT: {message.id}\n")
                            await self.wpbot(self.client, message, bot['bot_name'])
            else:
                print(f"No matching pattern for message: {message.text} {message} \n")
        except Exception as e:
            print(f">>(1)An error occurred while processing message: {e} \n message:{message}\n")
        finally:
            if enc_exist:
                await asyncio.sleep(5)
            else:
                await asyncio.sleep(0)

    async def send_message(self, client, message):
        last_message_id = message.id
        # 构建 caption
        caption_parts = []
        
        # 获取消息来源
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
            sender_title = f"{sender.first_name} {sender.last_name}"
            if sender.username:
                caption_parts.append(f"Original: <a href='https://t.me/{sender.username}'>{sender_title}</a>")
            else:
                caption_parts.append(f"Original: <a href='tg://user?id={message.from_id.user_id}'>{sender_title}</a>")

        caption_text = "\n".join(caption_parts)
        try:
            if hasattr(message, 'grouped_id') and message.grouped_id:
                # 获取相册中的所有消息
                album_messages = await client.get_messages(message.peer_id, limit=100)
                album = [msg for msg in album_messages if msg.grouped_id == message.grouped_id]
                if album:
                    await asyncio.sleep(0.5)  # 间隔80秒
                    last_message_id = max(row.id for row in album)
                    await client.send_file(self.config['warehouse_chat_id'], album, reply_to=message.id, caption=caption_text, parse_mode='html')
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
                    await client.send_file(self.config['warehouse_chat_id'], video, reply_to=message.id, caption=caption_text, parse_mode='html')
                    print(">>Forwarded video.\n")
                    
                    # 调用新的函数
                    #await self.send_video_to_filetobot_and_publish(client, video, message)
                else:
                    # 处理文档
                    document = message.media.document
                    await client.send_file(self.config['warehouse_chat_id'], document, reply_to=message.id, caption=caption_text, parse_mode='html')
                    print(">>Forwarded document.\n")
            elif isinstance(message.media, types.MessageMediaPhoto):
                # 处理图片
                photo = message.media.photo
                await client.send_file(self.config['warehouse_chat_id'], photo, reply_to=message.id, caption=caption_text, parse_mode='html')
                print(">>Forwarded photo.\n")
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
                        print("Received text response, waiting for media...")

            except asyncio.TimeoutError:
                await client.send_message(self.config['work_chat_id'], "filetobot timeout", reply_to=original_message_id)
                print("filetobot response timeout.")
                return

            # 将 filetobot 的响应内容传送给 beachboy807bot，并设置 caption 为原始消息的文本
            async with client.conversation(self.config['public_bot_id']) as publicbot_conv:
                caption_text = "|_SendToBeach_|\n"+original_message.text+"\n"+filetobot_response.message
                await publicbot_conv.send_file(filetobot_response.media, caption=caption_text)
                print("Forwarded filetobot response to publish bot with caption.")

    async def wpbot(self, client, message, bot_username):
        try:
            chat_id = self.config['work_chat_id']
            async with client.conversation(bot_username) as conv:
                # 根据bot_username 找到 wp_bot 中对应的 bot_name = bot_username 的字典
                bot = next((bot for bot in wp_bot if bot['bot_name'] == bot_username), None)
                if bot['mode'] == 'link':
                    message.text = '/start ' + message.text

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
                            print("Forwarded video.")
                            
                            # 调用新的函数
                            await self.send_video_to_filetobot_and_publish(client, video, message)
                        else:
                            # 处理文档
                            document = response.media.document
                            await client.send_file(chat_id, document, reply_to=message.id)

                            caption_text = "|_SendToBeach_|\n"+message.text
                            await client.send_file(self.config['public_bot_id'], document, caption=caption_text)
                            print("Forwarded document.")
                    elif isinstance(response.media, types.MessageMediaPhoto):
                        # 处理图片
                        photo = response.media.photo
                        await client.send_file(chat_id, photo, reply_to=message.id)

                        caption_text = "|_SendToBeach_|\n"+message.text
                        await client.send_file(self.config['public_bot_id'], photo, caption=caption_text)
                        print("Forwarded photo.")
                    else:
                        print("Received media, but not a document, video, or photo.")
                elif response.text:
                    # 处理文本
                    if response.text == "在您发的这条消息中，没有代码可以被解析":
                        await self.wpbot(self.client, message, 'ShowFilesBot')
                       
                    elif "💔抱歉，未找到可解析内容。" in response.text:
                        await client.send_message(chat_id, response.text, reply_to=message.id)
                        
                    elif response.text == "创建者申请了新的分享链接，此链接已过期":
                        await self.wpbot(self.client, message, 'ShowFilesBot')
                    elif response.text == "此机器人面向外国用户使用，访问 @MediaBKHome 获取面向国内用户使用的机器人":
                        await self.wpbot(self.client, message, 'ShowFilesBot')
                        
                    elif response.text == "access @MediaBKHome to get media backup bot for non-chinese-speaking user":
                        await self.wpbot(self.client, message, 'ShowFilesBot')
                    else:
                        print("Received text response: "+response.text)
                    print("Forwarded text.")
                else:
                    print("Received non-media and non-text response")
        except Exception as e:
            print(f"\rAn error occurred: {e}\n")

    

    def save_last_read_message_id(self, chat_id, message_id):
        data = {str(chat_id): message_id}
        if os.path.exists(self.LAST_READ_MESSAGE_FILE):
            with open(self.LAST_READ_MESSAGE_FILE, 'r') as file:
                existing_data = json.load(file)
            existing_data.update(data)
            data = existing_data
        with open(self.LAST_READ_MESSAGE_FILE, 'w') as file:
            json.dump(data, file)

    def load_last_read_message_id(self, chat_id):
        if os.path.exists(self.LAST_READ_MESSAGE_FILE):
            with open(self.LAST_READ_MESSAGE_FILE, 'r') as file:
                data = json.load(file)
                return data.get(str(chat_id), 0)  # 返回 0 作为默认值
        return 0

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





        
       

    async def forward_media_to_warehouse(self, client, message):
        try:
            if_send = False
            last_message_id = message.id
            if message.media:
                if message.chat_id != self.config['warehouse_chat_id']:
                    
                    if isinstance(message.media, types.MessageMediaDocument):
                        if not any(isinstance(attr, types.DocumentAttributeSticker) for attr in message.media.document.attributes):
                            # 排除贴图
                            print(f"Forwarding document to warehouse chat: {message.id}\n")
                            last_message_id = await self.send_message(client, message)
                            if_send=True
                    elif isinstance(message.media, types.MessageMediaPhoto):
                        print(f"Forwarding photo to warehouse chat: {message.id}\n")
                        last_message_id = await self.send_message(client, message)
                        if_send=True
                    
                    
                else:
                    print(f"Message is from warehouse chat, not forwarding: {message.id}\n")
            else:
                print(f"No matching pattern for message: {message.text} {message} \n")
        except Exception as e:
            print(f">>(2)An error occurred while processing message: {e} \n message:{message}\n")
        finally:
            if if_send:
                await asyncio.sleep(3)
            return last_message_id
        
    def check_strings(self,text):
        # 将字串以,分割成数组  # 定义要检查的关键词
        kw = self.config['key_word']
        keywords = kw.split(",")
        # 编译正则表达式模式
        pattern = re.compile("|".join(keywords))
        # 查找文本中匹配的关键词
        found_keywords = pattern.findall(text)
        return found_keywords