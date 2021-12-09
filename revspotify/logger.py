import logging

from config import Config

def log(func):
    def wrapper(*args, **kwargs):
        # if bot is mentioned, log the message
        bot_username = Config.BOT_USERNAME
        update = args[0]
        reply_to_message = update.message.reply_to_message
        reply_to_message_from_user = {}
        if reply_to_message is not None:
            reply_to_message_from_user = reply_to_message.from_user.to_dict()
        if reply_to_message_from_user.get("username") == bot_username or f"@{bot_username}" in update.message.text:
            Logger(args[1], args[0]).log_info("mentioned")
        return func(*args, **kwargs)
    return wrapper 

class Logger:
    def __init__(self, context, update):
        logging_format = '%(asctime)s - %(message)s'
        self.logging = logging
        self.logging.basicConfig(level=logging.INFO,
                            format=logging_format,
                            filename='log.txt',
                            filemode='a')
        self.context = context
        self.update = update
                        
    def log_info(self, action):
        message = self.update.message
        from_user = message.from_user
        text = message.text
        from_user.first_name = from_user.first_name if from_user.first_name else ""
        from_user.last_name = from_user.last_name if from_user.last_name else ""
        full_name = from_user.first_name + ' ' + from_user.last_name
        username = from_user.username if from_user.username else ""
        chat_id = message.chat_id
        message_id = message.message_id

        log_message = f'chat_id: {chat_id} - message_id: {message_id} - name: {full_name} - username: @{username} - action: {action} - message: {text}'
        if Config.LOG_CHAT_ID is not None:
            self.context.bot.send_message(chat_id=Config.LOG_CHAT_ID, text=log_message)
            self.context.bot.forward_message(chat_id=Config.LOG_CHAT_ID, from_chat_id=self.update.message.chat_id, message_id=self.update.message.message_id)
        self.logging.info(log_message)