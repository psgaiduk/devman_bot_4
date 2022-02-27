from dotenv import load_dotenv
from requests import get, post

import os
import logging
import redis
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Filters, Updater
from telegram.ext import CallbackQueryHandler, CommandHandler, MessageHandler
from logger_handler import BotHandler
from functools import partial


logger = logging.getLogger('app_logger')


def get_token(moltin_client_id, moltin_client_secret):
    url = 'https://api.moltin.com/oauth/access_token'
    data = {'client_id': moltin_client_id, 'client_secret': moltin_client_secret, 'grant_type': 'client_credentials'}
    data_for_token = post(url=url, data=data).json()
    return data_for_token['access_token']


def get_products(token):
    url = 'https://api.moltin.com/v2/products'
    header = {'authorization': f'Bearer {token}', 'content-type': 'application/json'}
    return get(url, headers=header).json()['data']


def start(_, update, moltin_client_id, moltin_client_secret):
    """
    Хэндлер для состояния START.

    Бот отвечает пользователю фразой "Привет!" и переводит его в состояние ECHO.
    Теперь в ответ на его команды будет запускаеться хэндлер echo.
    """

    token = get_token(moltin_client_id, moltin_client_secret)
    products = get_products(token)

    keyboard = [[InlineKeyboardButton(product["name"], callback_data=product['id'])] for product in products]

    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text('Please choose:', reply_markup=reply_markup)
    return "ECHO"


def echo(bot, update):
    """
    Хэндлер для состояния ECHO.

    Бот отвечает пользователю тем же, что пользователь ему написал.
    Оставляет пользователя в состоянии ECHO.
    """
    users_reply = update.message.text
    update.message.reply_text(users_reply)
    return "ECHO"


def button(bot, update):
    query = update.callback_query

    bot.edit_message_text(text="Selected option: {}".format(query.data),
                          chat_id=query.message.chat_id,
                          message_id=query.message.message_id)


def handle_users_reply(bot, update, moltin_client_id, moltin_client_secret, db):
    """
    Функция, которая запускается при любом сообщении от пользователя и решает как его обработать.
    Эта функция запускается в ответ на эти действия пользователя:
        * Нажатие на inline-кнопку в боте
        * Отправка сообщения боту
        * Отправка команды боту
    Она получает стейт пользователя из базы данных и запускает соответствующую функцию-обработчик (хэндлер).
    Функция-обработчик возвращает следующее состояние, которое записывается в базу данных.
    Если пользователь только начал пользоваться ботом, Telegram форсит его написать "/start",
    поэтому по этой фразе выставляется стартовое состояние.
    Если пользователь захочет начать общение с ботом заново, он также может воспользоваться этой командой.
    """
    if update.message:
        user_reply = update.message.text
        chat_id = update.message.chat_id
    elif update.callback_query:
        user_reply = update.callback_query.data
        chat_id = update.callback_query.message.chat_id
    else:
        return
    if user_reply == '/start':
        user_state = 'START'
    else:
        user_state = db.get(chat_id).decode("utf-8")

    start_with_args = partial(start,
                              moltin_client_id=moltin_client_id,
                              moltin_client_secret=moltin_client_secret)

    states_functions = {
        'START': start_with_args,
        'ECHO': echo
    }
    state_handler = states_functions[user_state]
    # Если вы вдруг не заметите, что python-telegram-bot перехватывает ошибки.
    # Оставляю этот try...except, чтобы код не падал молча.
    # Этот фрагмент можно переписать.
    try:
        next_state = state_handler(bot, update)
        db.set(chat_id, next_state)
    except Exception as err:
        logging.exception(err)


def main():
    dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path)

    token = os.getenv("TELEGRAM_TOKEN")
    logger_token = os.getenv("TOKEN_TELEGRAM_LOGGER")
    logger_chat_id = os.getenv("CHAT_ID")
    moltin_client_id = os.getenv('MOLTIN_CLIENT_ID')
    moltin_client_secret = os.getenv('MOLTIN_CLIENT_SECRET')
    database_password = os.getenv("REDIS_PASSWORD")
    database_host = os.getenv("REDIS_HOST")
    database_port = int(os.getenv("REDIS_PORT"))

    database = redis.Redis(host=database_host, port=database_port, password=database_password)

    logging.basicConfig(level=logging.INFO, format='{asctime} - {levelname} - {name} - {message}', style='{')
    logger.addHandler(BotHandler(logger_token, logger_chat_id))
    logger.info('Начало работы телеграмм бота Интернет магазин')

    handle_users_reply_with_args = partial(handle_users_reply,
                                           moltin_client_id=moltin_client_id,
                                           moltin_client_secret=moltin_client_secret,
                                           db=database)

    updater = Updater(token)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CallbackQueryHandler(button))
    dispatcher.add_handler(CallbackQueryHandler(handle_users_reply_with_args))
    dispatcher.add_handler(MessageHandler(Filters.text, handle_users_reply_with_args))
    dispatcher.add_handler(CommandHandler('start', handle_users_reply_with_args))
    updater.start_polling()


if __name__ == '__main__':
    main()
