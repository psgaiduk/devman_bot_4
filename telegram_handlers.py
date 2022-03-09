import re
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import logging
from functools import partial
from telegram_function import send_product_photo, create_cart, create_start_menu


logger = logging.getLogger('app_logger')


def start(_, update, moltin):
    """
    Хэндлер для состояния START.
    """

    products = moltin.get_products()

    keyboard = [[InlineKeyboardButton(product["name"], callback_data=product['id'])] for product in products]

    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text('Выберите рыбу:', reply_markup=reply_markup)
    return "HANDLE_MENU"


def handle_menu(bot, update, moltin):
    query = update.callback_query

    keyboard = [
        [InlineKeyboardButton("1 кг", callback_data=f'1 - {query.data}'),
         InlineKeyboardButton("5 кг", callback_data=f'5 - {query.data}'),
         InlineKeyboardButton("10 кг", callback_data=f'10 - {query.data}')],
        [InlineKeyboardButton("Назад", callback_data='return_back')]]

    _, cart_items = moltin.get_cart(query.message.chat_id)
    if cart_items:
        keyboard.append([InlineKeyboardButton("Корзина", callback_data='cart')])

    reply_markup = InlineKeyboardMarkup(keyboard)

    send_product_photo(moltin, bot, query.data, query, reply_markup)

    return "HANDLE_DESCRIPTION"


def handle_description(bot, update, moltin):
    query = update.callback_query
    chat_id = query.message.chat_id
    if query.data == 'return_back':

        create_start_menu(moltin, bot, chat_id, query)

        return "HANDLE_MENU"
    elif query.data == 'cart':
        create_cart(bot, moltin, chat_id, query)

        return "HANDLE_CART"
    else:
        query.answer('Товар добавлен')
        weight, product_id = query.data.split(' - ')
        moltin.add_to_cart(product_id, chat_id, int(weight))

        keyboard = [
            [InlineKeyboardButton("1 кг", callback_data=f'1 - {product_id}'),
             InlineKeyboardButton("5 кг", callback_data=f'5 - {product_id}'),
             InlineKeyboardButton("10 кг", callback_data=f'10 - {product_id}')],
            [InlineKeyboardButton("Назад", callback_data='return_back')],
            [InlineKeyboardButton("Корзина", callback_data='cart')],
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        send_product_photo(moltin, bot, product_id, query, reply_markup)
        return "HANDLE_DESCRIPTION"


def handle_cart(bot, update, moltin):
    query = update.callback_query
    chat_id = query.message.chat_id
    if query.data == 'return_back':
        create_start_menu(moltin, bot, chat_id, query)
        return "HANDLE_MENU"
    elif query.data == 'payment':
        message = 'Пришлите вашу почту, мы с вами свяжемся'
        bot.send_message(text=message,
                         chat_id=chat_id,
                         message_id=query.message.message_id,)
        return "HANDLE_WAIT_EMAIL"
    else:
        moltin.delete_item_from_cart(chat_id, query.data)
        create_cart(bot, moltin, chat_id, query)
        return "HANDLE_CART"


def handle_wait_email(bot, update, moltin, db):
    email = update.message.text
    # Взято здесь
    # https://ru.stackoverflow.com/questions/306126/%D0%92%D0%B0%D0%BB%D0%B8%D0%B4%D0%B0%D1%86%D0%B8%D1%8F-email-%D0%B2-python
    pattern = r"^[-\w\.]+@([-\w]+\.)+[-\w]{2,4}$"

    if re.match(pattern, email):
        message = f'''Вы указали этот email {email}

Наш менеджер с вами свяжется в ближайшее время
Чтобы начать покупки снова, отправьте любое сообщение    
'''
        moltin.create_customer_in_cms(update.message.chat_id, email, db)
        moltin.delete_all_from_cart(update.message.chat_id)
        state = 'START'
    else:
        message = 'Вы указали не корректный email'
        state = 'HANDLE_WAIT_EMAIL'

    bot.send_message(text=message,
                     chat_id=update.message.chat_id,)

    return state


def handle_users_reply(bot, update, moltin, db):
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

    start_with_args = partial(start, moltin=moltin)

    handle_menu_with_args = partial(handle_menu, moltin=moltin)

    handle_description_with_args = partial(handle_description, moltin=moltin)

    handle_cart_with_args = partial(handle_cart, moltin=moltin)

    handle_wait_email_with_args = partial(handle_wait_email, moltin=moltin, db=db)

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
