import logging

from config import Config

class Logger:
    def __init__(self, context):
        logging_format = '%(asctime)s - %(message)s'
        self.logging = logging
        self.logging.basicConfig(level=logging.INFO,
                            format=logging_format,
                            filename='log.txt',
                            filemode='a')
        self.context = context
                        
    def log_info(self, from_user, action, message):
        from_user.first_name = from_user.first_name if from_user.first_name else ""
        from_user.last_name = from_user.last_name if from_user.last_name else ""
        full_name = from_user.first_name + ' ' + from_user.last_name
        username = from_user.username if from_user.username else ""
        
        log_message = f'name: {full_name} - username: {username} - action: {action} - message: {message}'
        if Config.LOG_CHAT_ID is not None:
            self.context.bot.send_message(chat_id=Config.LOG_CHAT_ID, text=log_message)
        self.logging.info(log_message)