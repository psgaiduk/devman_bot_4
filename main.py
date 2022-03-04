from dotenv import load_dotenv
from requests import get, post, delete
import os
import logging
import redis
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Filters, Updater
from telegram.ext import CallbackQueryHandler, CommandHandler, MessageHandler
from logger_handler import BotHandler
from functools import partial
import re

logger = logging.getLogger('app_logger')


def get_token(moltin_client_id, moltin_client_secret):
    url = 'https://api.moltin.com/oauth/access_token'
    data = {'client_id': moltin_client_id, 'client_secret': moltin_client_secret, 'grant_type': 'client_credentials'}
    data_for_token = post(url=url, data=data).json()
    return data_for_token['access_token']


def get_products(token, product_id=''):
    url = f'https://api.moltin.com/v2/products{product_id}'
    header = {'authorization': f'Bearer {token}', 'content-type': 'application/json'}
    return get(url, headers=header).json()['data']


def get_image_product(token, product_id):
    url = f'https://api.moltin.com/v2/files/{product_id}'
    header = {'authorization': f'Bearer {token}', 'content-type': 'application/json'}
    # return get(url, headers=header).json()['data']['link']['href']
    return 'https://e1.edimdoma.ru/data/ingredients/0000/5509/5509-ed4_wide.jpg'


def add_to_cart(token, product_id, chat_id, quantity):
    url = f'https://api.moltin.com/v2/carts/{chat_id}/items'
    data = {"data": {"id": product_id, "type": "cart_item", "quantity": quantity}}
    header = {'authorization': f'Bearer {token}', 'content-type': 'application/json'}
    post(url, headers=header, json=data)


def get_cart(token, chat_id):
    url = f'https://api.moltin.com/v2/carts/{chat_id}'
    header = {'authorization': f'Bearer {token}', 'content-type': 'application/json'}
    cart_price = get(url, headers=header).json()
    cart_price = cart_price['data']['meta']['display_price']['with_tax']['formatted']
    url = f'https://api.moltin.com/v2/carts/{chat_id}/items'
    cart_items = get(url, headers=header).json()
    return cart_price, cart_items['data']


def delete_item_from_cart(token, chat_id, item_id):
    url = f'https://api.moltin.com/v2/carts/{chat_id}/items/{item_id}'
    header = {'authorization': f'Bearer {token}', 'content-type': 'application/json'}
    delete(url, headers=header)


def create_customer_in_cms(token, chat_id, email, db):
    url = f'https://api.moltin.com/v2/customers'
    header = {'authorization': f'Bearer {token}', 'content-type': 'application/json'}
    data = {
     "data": {
       "type": "customer",
       "name": str(chat_id),
       "email": email,
       "password": "mysecretpassword"
     }
    }
    customer = post(url, headers=header, json=data)
    customer_id = customer.json()['data']['id']
    db.set(f'customer_{chat_id}', customer_id)


def create_start_menu(token, bot, chat_id, query):
    products = get_products(token)

    keyboard = [[InlineKeyboardButton(product["name"], callback_data=product['id'])] for product in products]

    reply_markup = InlineKeyboardMarkup(keyboard)

    bot.send_message(reply_markup=reply_markup, text='Выберите рыбу:',
                     chat_id=chat_id,
                     message_id=query.message.message_id)

    bot.delete_message(chat_id=chat_id,
                       message_id=query.message.message_id)


def create_cart(bot, token, chat_id, query):
    cart_price, cart_items = get_cart(token, chat_id)
    message = 'Корзина пуста'
    keyboard = []
    if cart_items:
        message = 'Товары в корзине:'
        items = []
        for item in cart_items:
            items.append({'id': item['id'], 'name': item['name']})
            message += f'\n\n\n{item["name"]}\n\n' \
                       f'{item["quantity"]} кг - за {item["meta"]["display_price"]["with_tax"]["value"]["formatted"]}'
        message += f'\n\nОбщая цена {cart_price}'
        keyboard = [[InlineKeyboardButton(f'Оплатить товары на сумму: {cart_price}', callback_data='payment')]]

        keyboard.extend([[InlineKeyboardButton(f'Убрать из корзины {item["name"]}', callback_data=item['id'])]
                         for item in items])

    keyboard.append([InlineKeyboardButton(f'В меню', callback_data='return_back')])

    reply_markup = InlineKeyboardMarkup(keyboard)

    bot.send_message(text=message,
                     chat_id=chat_id,
                     message_id=query.message.message_id,
                     reply_markup=reply_markup)

    bot.delete_message(chat_id=chat_id,
                       message_id=query.message.message_id)


def start(_, update, moltin_client_id, moltin_client_secret):
    """
    Хэндлер для состояния START.
    """

    token = get_token(moltin_client_id, moltin_client_secret)
    products = get_products(token)

    keyboard = [[InlineKeyboardButton(product["name"], callback_data=product['id'])] for product in products]

    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text('Выберите рыбу:', reply_markup=reply_markup)
    return "HANDLE_MENU"


def send_photo_product(token, bot, product_id, query, reply_markup):
    product = get_products(token, product_id=f'/{product_id}')

    image_id = product['relationships']['main_image']['data']['id']
    image_product = get_image_product(token, product_id=image_id)

    _, cart_items = get_cart(token, query.message.chat_id)

    quantity_item = [item['quantity'] for item in cart_items if item['product_id'] == product_id]
    text_quantity = ''
    if quantity_item:
        text_quantity = f'\n\nВ корзине уже {quantity_item[0]} кг'

    message = f'{product["name"]}\n\n{product["description"]}\n' \
              f'{product["meta"]["display_price"]["with_tax"]["formatted"]} за кг.\n' \
              f'В наличии: {product["meta"]["stock"]["level"]} кг.{text_quantity}'

    bot.send_photo(photo=image_product,
                   caption=message,
                   chat_id=query.message.chat_id,
                   reply_markup=reply_markup)

    bot.delete_message(chat_id=query.message.chat_id,
                       message_id=query.message.message_id)


def handle_menu(bot, update, moltin_client_id, moltin_client_secret):
    query = update.callback_query

    token = get_token(moltin_client_id, moltin_client_secret)

    keyboard = [
        [InlineKeyboardButton("1 кг", callback_data=f'1 - {query.data}'),
         InlineKeyboardButton("5 кг", callback_data=f'5 - {query.data}'),
         InlineKeyboardButton("10 кг", callback_data=f'10 - {query.data}')],
        [InlineKeyboardButton("Назад", callback_data='return_back')]]

    _, cart_items = get_cart(token, query.message.chat_id)
    if cart_items:
        keyboard.append([InlineKeyboardButton("Корзина", callback_data='cart')])

    reply_markup = InlineKeyboardMarkup(keyboard)

    send_photo_product(token, bot, query.data, query, reply_markup)

    return "HANDLE_DESCRIPTION"


def handle_description(bot, update, moltin_client_id, moltin_client_secret):
    query = update.callback_query
    token = get_token(moltin_client_id, moltin_client_secret)
    chat_id = query.message.chat_id
    if query.data == 'return_back':

        create_start_menu(token, bot, chat_id, query)

        return "HANDLE_MENU"
    elif query.data == 'cart':
        create_cart(bot, token, chat_id, query)

        return "HANDLE_CART"
    else:
        query.answer('Товар добавлен')
        weight, product_id = query.data.split(' - ')
        add_to_cart(token, product_id, chat_id, int(weight))

        keyboard = [
            [InlineKeyboardButton("1 кг", callback_data=f'1 - {product_id}'),
             InlineKeyboardButton("5 кг", callback_data=f'5 - {product_id}'),
             InlineKeyboardButton("10 кг", callback_data=f'10 - {product_id}')],
            [InlineKeyboardButton("Назад", callback_data='return_back')],
            [InlineKeyboardButton("Корзина", callback_data='cart')],
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        send_photo_product(token, bot, product_id, query, reply_markup)
        return "HANDLE_DESCRIPTION"


def handle_cart(bot, update, moltin_client_id, moltin_client_secret):
    query = update.callback_query
    token = get_token(moltin_client_id, moltin_client_secret)
    chat_id = query.message.chat_id
    if query.data == 'return_back':
        create_start_menu(token, bot, chat_id, query)
        return "HANDLE_MENU"
    elif query.data == 'payment':
        message = 'Пришлите вашу почту, мы с вами свяжемся'
        bot.send_message(text=message,
                         chat_id=chat_id,
                         message_id=query.message.message_id,)
        return "HANDLE_WAIT_EMAIL"
    else:
        delete_item_from_cart(token, chat_id, query.data)
        create_cart(bot, token, chat_id, query)
        return "HANDLE_CART"


def handle_wait_email(bot, update, moltin_client_id, moltin_client_secret, db):
    email = update.message.text
    pattern = r"^[-\w\.]+@([-\w]+\.)+[-\w]{2,4}$"

    if re.match(pattern, email):
        token = get_token(moltin_client_id, moltin_client_secret)
        message = f'Вы указали этот email {email}'
        create_customer_in_cms(token, update.message.chat_id, email, db)
        # status = 'HANDLE_PHONE'
    else:
        message = 'Вы указали не корректный email'
        # status = 'HANDLE_EMAIL'

    bot.send_message(text=message,
                     chat_id=update.message.chat_id,)

    # return status


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

    handle_menu_with_args = partial(handle_menu,
                                    moltin_client_id=moltin_client_id,
                                    moltin_client_secret=moltin_client_secret,)

    handle_description_with_args = partial(handle_description,
                                           moltin_client_id=moltin_client_id,
                                           moltin_client_secret=moltin_client_secret,)

    handle_cart_with_args = partial(handle_cart,
                                    moltin_client_id=moltin_client_id,
                                    moltin_client_secret=moltin_client_secret,)

    handle_wait_email_with_args = partial(handle_wait_email,
                                          moltin_client_id=moltin_client_id,
                                          moltin_client_secret=moltin_client_secret,
                                          db=db)

    states_functions = {
        'START': start_with_args,
        'HANDLE_MENU': handle_menu_with_args,
        'HANDLE_DESCRIPTION': handle_description_with_args,
        'HANDLE_CART': handle_cart_with_args,
        'HANDLE_WAIT_EMAIL': handle_wait_email_with_args,
    }
    state_handler = states_functions[user_state]
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
    dispatcher.add_handler(CallbackQueryHandler(handle_users_reply_with_args))
    dispatcher.add_handler(MessageHandler(Filters.text, handle_users_reply_with_args))
    dispatcher.add_handler(CommandHandler('start', handle_users_reply_with_args))
    updater.start_polling()


if __name__ == '__main__':
    main()
