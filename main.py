from dotenv import load_dotenv
import os
import logging
import redis
from telegram.ext import Filters, Updater
from telegram.ext import CallbackQueryHandler, CommandHandler, MessageHandler
from logger_handler import BotHandler
from functools import partial
from moltin import WorkMoltin
from telegram_handlers import handle_users_reply


logger = logging.getLogger('app_logger')


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
    moltin = WorkMoltin(moltin_client_id, moltin_client_secret)

    logging.basicConfig(level=logging.INFO, format='{asctime} - {levelname} - {name} - {message}', style='{')
    logger.addHandler(BotHandler(logger_token, logger_chat_id))
    logger.info('Начало работы телеграмм бота Интернет магазин')

    handle_users_reply_with_args = partial(handle_users_reply,
                                           moltin=moltin,
                                           db=database)

    updater = Updater(token)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CallbackQueryHandler(handle_users_reply_with_args))
    dispatcher.add_handler(MessageHandler(Filters.text, handle_users_reply_with_args))
    dispatcher.add_handler(CommandHandler('start', handle_users_reply_with_args))
    updater.start_polling()


if __name__ == '__main__':
    main()
