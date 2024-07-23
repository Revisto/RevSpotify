import json
import os

class MessageHandler:
    def __init__(self, locale='en'):
        self.locale = locale
        self.messages = self.load_messages()

    def load_messages(self):
        locale_file = os.path.join(os.path.dirname(__file__), f'locales/{self.locale}.json')
        with open(locale_file, 'r', encoding='utf-8') as file:
            return json.load(file)

    def get_message(self, key, **kwargs):
        message = self.messages.get(key, '')
        return message.format(**kwargs)