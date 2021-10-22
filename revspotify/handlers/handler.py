
from telegram import Update
from telegram.ext import CallbackContext

from controllers.bot_controller import BotController

TASK, CATEGORY = range(2)


def start_and_help(update: Update, context: CallbackContext) -> int:
    return BotController(update, context).start()
    

def query(update: Update, context: CallbackContext) -> int:
    return BotController(update, context).query()