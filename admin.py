import telebot
from telebot.types import ReplyKeyboardRemove
import config

debug_bot = telebot.TeleBot(config.API_TOKEN_DEBUG)


def alarma(message, notification=False):
    debug_bot.send_message('52899166', '[Univision VOTE]\n\n' + message, disable_notification=(not notification),
                           reply_markup=ReplyKeyboardRemove())
    print(message)