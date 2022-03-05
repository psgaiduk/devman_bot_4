from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
import logging


logger = logging.getLogger('app_logger')


def create_start_menu(moltin, bot, chat_id, query):
    products = moltin.get_products()

    keyboard = [[InlineKeyboardButton(product["name"], callback_data=product['id'])] for product in products]

    reply_markup = InlineKeyboardMarkup(keyboard)

    bot.delete_message(chat_id=chat_id,
                       message_id=query.message.message_id)

    bot.send_message(reply_markup=reply_markup, text='Выберите рыбу:',
                     chat_id=chat_id,
                     message_id=query.message.message_id)


def create_cart(bot, moltin, chat_id, query):
    cart_price, cart_items = moltin.get_cart(chat_id)
    message = 'Корзина пуста'
    keyboard = []
    if cart_items:
        message = 'Товары в корзине:'
        items = []
        for item in cart_items:
            items.append({'id': item['id'], 'name': item['name']})
            message += f'\n\n\n*{item["name"]}*\n\n' \
                       f'{item["quantity"]} кг - за {item["meta"]["display_price"]["with_tax"]["value"]["formatted"]}'
        message += f'\n\n*Общая цена {cart_price}*'
        keyboard = [[InlineKeyboardButton(f'Оплатить товары на сумму: {cart_price}', callback_data='payment')]]

        keyboard.extend([[InlineKeyboardButton(f'Убрать из корзины {item["name"]}', callback_data=item['id'])]
                         for item in items])

    keyboard.append([InlineKeyboardButton(f'В меню', callback_data='return_back')])

    reply_markup = InlineKeyboardMarkup(keyboard)

    bot.delete_message(chat_id=chat_id,
                       message_id=query.message.message_id)

    bot.send_message(text=message,
                     chat_id=chat_id,
                     message_id=query.message.message_id,
                     reply_markup=reply_markup,
                     parse_mode=ParseMode.MARKDOWN)


def send_photo_product(moltin, bot, product_id, query, reply_markup):
    product = moltin.get_products(product_id=f'/{product_id}')

    image_id = product['relationships']['main_image']['data']['id']
    image_product = moltin.get_image_product(product_id=image_id)

    _, cart_items = moltin.get_cart(query.message.chat_id)

    quantity_item = [item['quantity'] for item in cart_items if item['product_id'] == product_id]
    text_quantity = ''
    if quantity_item:
        text_quantity = f'\n\nВ корзине уже {quantity_item[0]} кг'

    message = f'*{product["name"]}*\n\n{product["description"]}\n' \
              f'{product["meta"]["display_price"]["with_tax"]["formatted"]} за кг.\n' \
              f'В наличии: {product["meta"]["stock"]["level"]} кг.{text_quantity}'

    bot.delete_message(chat_id=query.message.chat_id,
                       message_id=query.message.message_id)

    bot.send_photo(photo=image_product,
                   caption=message,
                   chat_id=query.message.chat_id,
                   reply_markup=reply_markup,
                   parse_mode=ParseMode.MARKDOWN)
