from telegram import Bot
import logging


class BotHandler(logging.Handler):

    def __init__(self, logger_token, logger_chat_id):
        logging.Handler.__init__(self)
        self.logger_chat_id = logger_chat_id
        self.bot_logger = Bot(token=logger_token)

    def emit(self, record):
        message = self.format(record)
        self.bot_logger.send_message(
            text=message,
            chat_id=self.logger_chat_id)