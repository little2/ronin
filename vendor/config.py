import os
class Config:
    def __init__(self):
        self.api_id = os.getenv('API_ID')
        self.api_hash = os.getenv('API_HASH')
        self.phone_number = os.getenv('PHONE_NUMBER')
        self.bot_token = os.getenv('BOT_TOKEN')
        self.man_bot_id = os.getenv('MAN_BOT_ID')
        self.session_name = self.api_id + 'session_name'  # 确保与上传的会话文件名匹配

        self.db_name = os.getenv('DB_NAME')
        self.db_user = os.getenv('DB_USER')
        self.db_password = os.getenv('DB_PASSWORD')
        self.db_host = os.getenv('DB_HOST')
        self.db_port = int(os.getenv('DB_PORT', 5432))
        self.db_sslmode = os.getenv('DB_SSLMODE', 'require')

        self.work_bot_id = os.getenv('WORK_BOT_ID')
        self.work_chat_id = int(os.getenv('WORK_CHAT_ID', 0))  # 默认值为0
        self.media_work_chat_id = int(os.getenv('MEDIA_WORK_CHAT_ID', 0))  # 默认值为0
        self.public_bot_id = os.getenv('PUBLIC_BOT_ID')
        self.warehouse_chat_id = int(os.getenv('WAREHOUSE_CHAT_ID', 0))  # 默认值为0
        self.link_chat_id = int(os.getenv('LINK_CHAT_ID', 0))
        self.key_word = os.getenv('KEY_WORD')
        self.show_caption = os.getenv('SHOW_CAPTION')