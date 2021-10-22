from dotenv import load_dotenv
from os import getenv

load_dotenv()


class Config:
    token = getenv("token")
