import os
from peewee import PostgresqlDatabase, Model, CharField
from playhouse.pool import PooledPostgresqlDatabase

from telegram import Update
import telegram
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram.constants import ParseMode
from vendor.class_bot import LYClass  # 导入 LYClass
from vendor.wpbot import wp_bot  # 导入 wp_bot

# 检查是否在本地开发环境中运行
if not os.getenv('GITHUB_ACTIONS'):
    from dotenv import load_dotenv
    load_dotenv()

# 获取 Telegram API 信息
bot_token = os.getenv('BOT_TOKEN')
man_bot_id =os.getenv('MAN_BOT_ID')

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

tgbot = LYClass('','')

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

# 连接到数据库
db.connect()

# 如果需要，创建表
db.create_tables([datapan], safe=True)

def check_connection():
    if db.is_closed():
        db.connect()

# 定义一个 /start 命令处理函数
async def start(update: Update, context) -> None:
    await update.message.reply_text('Hello! 我是你的 Telegram 机器人!')

# 定义一个处理不同类型消息的函数
async def handle_message(update: Update, context) -> None:
    message = update.message

    if message.text:
        # 文本消息
        message_type = "文本"
        
        query = await tgbot.process_by_check_text(message,'query')
        if query:
            if query['mode'] == 'enctext':
                response = f"<code>{query['match']}</code> via @{query['bot_name']}"
            elif query['mode'] == 'link':
                response = f"https://t.me/{query['bot_name']}?start={query['match']}"
           
            check_connection()
            # 使用 peewee 查询数据库 where enc_str = query['match']
            result = datapan.get_or_none(datapan.enc_str == query['match'])
            if result:
                # 指定要回复的 message_id
                reply_to_message_id = message.message_id

                if result.file_type == 'photo':
                    # 回复消息中的照片
                    await context.bot.send_photo(
                        chat_id=message.chat_id,
                        photo=result.file_id,
                        caption=f"#{result.file_unique_id} #ZTD",
                        reply_to_message_id=reply_to_message_id,
                        parse_mode=ParseMode.HTML
                    )
                    response = f"文件 ID: {result.file_id}"
                    return True
                elif result.file_type == 'video':   
                    # 回复消息中的视频
                    await context.bot.send_video(
                        chat_id=message.chat_id,
                        video=result.file_id,
                        caption=f"#{result.file_unique_id} #ZTD",
                        reply_to_message_id=reply_to_message_id,
                        parse_mode=ParseMode.HTML
                    )
                    response = f"文件 ID: {result.file_id}"
                    return True
                elif result.file_type == 'document':
                    # 回复消息中的文件
                    await context.bot.send_document(
                        chat_id=message.chat_id,
                        document=result.file_id,
                        caption=f"#{result.file_unique_id} #ZTD",
                        reply_to_message_id=reply_to_message_id,
                        parse_mode=ParseMode.HTML
                    )
                    response = f"文件 ID: {result.file_id}"
                    return True
            else:
                #传递给work_bot_id work_bot_id
                # 通过 bot 对象发送消息
                try:
                    await context.bot.send_message(chat_id=man_bot_id, text=f"|_request_|{query['match']}")
                except telegram.error.BadRequest as e:
                    print(f"Error: {e}")
                
                

            
        else:
            print(f"query: {query}")
            response = f"你发送的是{message_type}消息。"
        
    elif message.photo:
        # 照片消息
        await tgbot.update_wpbot_data('', message, datapan)
        message_type = "照片"
        file_id = message.photo[-1].file_id  # 获取最大的分辨率
        response = f"你发送的是{message_type}消息。File ID: {file_id}"
    
    elif message.video:
        # 视频消息
        message_type = "视频"
        await tgbot.update_wpbot_data('', message, datapan)
        file_id = message.video.file_id
        response = f"你发送的是{message_type}消息。File ID: {file_id}"
    
    elif message.document:
        # 文档/文件消息
        await tgbot.update_wpbot_data('', message, datapan)
        message_type = "文件"
        file_id = message.document.file_id
        response = f"你发送的是{message_type}消息。File ID: {file_id}"
    
    elif message.voice:
        # 语音消息
        message_type = "语音"
        file_id = message.voice.file_id
        response = f"你发送的是{message_type}消息。File ID: {file_id}"
    
    elif message.audio:
        # 音频消息
        message_type = "音频"
        file_id = message.audio.file_id
        response = f"你发送的是{message_type}消息。File ID: {file_id}"
    
    elif message.video_note:
        # 视频笔记消息
        message_type = "视频笔记"
        file_id = message.video_note.file_id
        response = f"你发送的是{message_type}消息。File ID: {file_id}"

    else:
        # 其他类型消息
        message_type = "未知类型"
        response = f"你发送的是{message_type}消息。"

    # 打印消息类型和内容到控制台
    sender_name = message.from_user.username or message.from_user.id
    print(f"收到来自 {sender_name} 的 {message_type} 消息")

    # 回复消息
    await update.message.reply_html(response)

# 启动 Telegram 机器人
def main():
    try:
        print("启动机器人...")
        # 使用 Application 初始化，轮询获取更新
        application = Application.builder().token(bot_token).build()

        # 注册 /start 命令处理程序
        application.add_handler(CommandHandler("start", start))

        # 注册消息处理程序，处理所有消息类型
        application.add_handler(MessageHandler(filters.ALL, handle_message))

        # 启动轮询方式获取消息
        application.run_polling()
    except KeyboardInterrupt:
        print("机器人已手动停止")
    finally:
        db.close()  # 关闭数据库连接
        print("数据库连接已关闭")

if __name__ == '__main__':
    main()
