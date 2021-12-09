from dotenv import load_dotenv
from os import getenv

load_dotenv()


class Config:
    TOKEN = getenv("TOKEN")
    LOG_CHAT_ID = getenv("LOG_CHAT_ID")
    BOT_USERNAME = getenv("BOT_USERNAME")