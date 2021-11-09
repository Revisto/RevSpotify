
from telegram import Update
from telegram.ext import CallbackContext

from controllers.bot_controller import BotController

TASK, CATEGORY = range(2)


def start_and_help(update: Update, context: CallbackContext) -> int:
    return BotController(update, context).start()
    
def query(update: Update, context: CallbackContext) -> int:
    return BotController(update, context).query()

def send_playlis(update: Update, context: CallbackContext) -> int:
    return BotController(update, context).send_playlist()

def cancel(update: Update, context: CallbackContext) -> int:
    return BotController(update, context).cancel()

def search_intro(update: Update, context: CallbackContext) -> int:
    return BotController(update, context).search_intro()

def search_track(update: Update, context: CallbackContext) -> int:
    return BotController(update, context).search_track()

def search_track(update: Update, context: CallbackContext) -> int:
    return BotController(update, context).search_track()

def choose_from_search_results(update: Update, context: CallbackContext) -> int:
    return BotController(update, context).choose_from_search_results()