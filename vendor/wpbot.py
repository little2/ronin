

wp_bot = [
    {
        'title': 'filespan1',
        'bot_name': 'FilesPan1Bot',
        'id': '7174271897',  # 6854050358
        'mode': 'enctext',
        'pattern': r'(?:p_FilesPan1Bot_|v_FilesPan1Bot_|d_FilesPan1Bot_)[a-zA-Z0-9-_]{30,100}(?![a-zA-Z0-9-_])',
        'message_thread_id': '23'
    },
   
    {
        'title': 'blgg',
        'bot_name': 'FilesDrive_BLGA_bot',
        'id': '7485716743',  # 6854050358
        'mode': 'enctext',
        'pattern': r'(?:p_|vi_|f_|fds_)[a-zA-Z0-9-_]{30,100}(?![a-zA-Z0-9-_])',
        'message_thread_id': '23'
    },
    {
        'title': 'mediabk',
        'bot_name': 'MediaBK5Bot',
        'id': '6700909600',
        'mode': 'enctext',
        'pattern': r'\b[a-zA-Z0-9\-+=_]{20,33}(?:=_grp|_mda)(?![a-zA-Z0-9-_])',
        'message_thread_id': '32'
    },
    {
        'title': 'showfiles',
        'bot_name': 'ShowFilesBot',
        'id': '6976547743',  # 6854050358
        'mode': 'enctext',
        'pattern': r'(?:showfilesbot_|fds_)[a-zA-Z0-9-_]{15,29}(?![a-zA-Z0-9-_])',
        'message_thread_id': '27'
    },
    {
        'title': 'datapan',
        'bot_name': 'datapanbot',
        'id': '6854050358',  # 6854050358
        'mode': 'enctext',
        'pattern': r'(?:P_DataPanBot_|V_DataPanBot_|D_DataPanBot_|fds_|pk_)[a-zA-Z0-9-_]{30,100}(?![a-zA-Z0-9-_])',
        'message_thread_id': '28'
    },
     {
        'title': 'filesave',
        'bot_name': 'FileSaveNewBot',
        'id': '7008164392',  # 6854050358
        'mode': 'enctext',
        'pattern': r'(?:^|\s)(?:P_|V_|D_)[a-zA-Z0-9-_]{15,29}(?![a-zA-Z0-9-_])',
        'message_thread_id': '25'
    },
    {
        'title': 'jyypbot',
        'bot_name': 'jyypbot',
        'id': '6873643118',
        'mode': 'link',
        'pattern': r'https:\/\/t\.me\/jyypbot\?start=([0-9a-fA-F\-]+)',
        'message_thread_id': '29'
    },
    {
        'title': 'filetobot',
        'bot_name': 'filetobot',
        'id': '291481095',
        'mode': 'link',
        'pattern': r'https:\/\/t\.me\/filetobot\?start=(\w{14,20})',
        'message_thread_id': '29'
    },
    {
        'title': 'filein',
        'bot_name': 'fileinbot',
        'id': '1433650553',
        'mode': 'link',
        'pattern': r'https:\/\/t\.me\/fileinbot\?start=(\w{14,20})',
        'message_thread_id': '30'
    },
    {
        'title': 'fileoffrm',
        'bot_name': 'fileoffrm_bot',
        'id': '7085384480',
        'mode': 'link',
        'pattern': r'https:\/\/t\.me\/fileoffrm_bot\?start=(\w{14,20})',
        'message_thread_id': '31'
    },
    {
        'title': 'wangpan',
        'bot_name': 'wangpanbot',
        'id': '5231326048',
        'mode': 'link',
        'pattern': r'https:\/\/t\.me\/(?i)WangPanBOT\?start=(file\w{14,20})',
        'message_thread_id': '32'
    },
    {
        'title': 'salai',
        'bot_name': 'salaiZTDBOT',
        'id': '8116549849',
        'mode': 'enctext',
        'pattern': r'^(正(?:[\u4e00-\u9fff]{5,10})太(?:[\u4e00-\u9fff]{34,100})密(?:[\u4e00-\u9fff]{5,10})[文图影])$',
        'message_thread_id': '32'
    }
]


