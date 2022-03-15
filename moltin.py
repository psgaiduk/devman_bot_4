import time

from requests import post, get, delete
import logging

logger = logging.getLogger('app_logger')


class WorkMoltin:

    def __init__(self, client_id, secret_code):
        self.client_id = client_id
        self.secret_code = secret_code
        self.url = 'https://api.moltin.com/v2/'
        self.time_get_header = None
        self.time_token_expires = None
        self.header = self.get_header()

    def get_header(self):
        if self.time_get_header:
            time_passed_since_get_token = time.time() - self.time_get_header
            if time_passed_since_get_token < self.time_token_expires:
                return self.header
        logger.debug('start get header')
        url = 'https://api.moltin.com/oauth/access_token'
        data = {'client_id': self.client_id, 'client_secret': self.secret_code, 'grant_type': 'client_credentials'}
        logger.debug(f'data for get token\nurl = {url}\ndata = {data}')
        response_with_token = post(url=url, data=data)
        logger.debug(f'get data token\n{response_with_token}')
        response_with_token.raise_for_status()
        dict_with_token = response_with_token.json()
        logger.debug(f'dict with token\n{dict_with_token}')
        token = dict_with_token['access_token']
        header = {'authorization': f'Bearer {token}', 'content-type': 'application/json'}
        logger.debug(f'return header = {header}')
        self.time_token_expires = dict_with_token['expires_in']
        self.time_get_header = time.time()
        self.header = header
        return header

    def get_product(self, product_id):
        logger.debug(f'Start work get products\nproduct_id = {product_id}')
        url = f'{self.url}products/{product_id}'
        logger.debug(f'create url = {url}')
        products = get(url, headers=self.get_header())
        products.raise_for_status()
        products = products.json()
        logger.debug(f'get data in dict\n{products}')
        return products['data']

    def get_all_products(self):
        logger.debug(f'Start work get products')
        url = f'{self.url}products'
        logger.debug(f'create url = {url}')
        products = get(url, headers=self.get_header())
        products.raise_for_status()
        products = products.json()
        return products['data']

    def get_image_product(self, product_id):
        logger.debug(f'Start work get image product\nproduct_id = {product_id}')
        url = f'{self.url}files/{product_id}'
        logger.debug(f'create url = {url}')
        image_product = get(url, headers=self.get_header())
        image_product.raise_for_status()
        image_product = image_product.json()
        logger.debug(f'get data in dict\n{image_product}')
        return image_product['data']['link']['href']

    def add_to_cart(self, product_id, chat_id, quantity):
        logger.debug(f'Start work add to cart\nproduct_id = {product_id}\n'
                     f'chat_id = {chat_id}\n'
                     f'quantity = {quantity}')
        url = f'{self.url}carts/{chat_id}/items'
        logger.debug(f'create url = {url}')
        data = {"data": {"id": product_id, "type": "cart_item", "quantity": quantity}}
        logger.debug(f'data to post request\n{data}')
        data = post(url, headers=self.get_header(), json=data)
        data.raise_for_status()

    def get_cart(self, chat_id):
        logger.debug(f'Start work get cart\nchat_id = {chat_id}')
        url = f'{self.url}carts/{chat_id}'
        logger.debug(f'create url = {url}')
        carts = get(url, headers=self.get_header())
        carts.raise_for_status()
        carts = carts.json()
        logger.debug(f'get data in dict\n{carts}')
        cart_price = carts['data']['meta']['display_price']['with_tax']['formatted']
        logger.debug(f'get cart price = {cart_price}')
        url = f'{self.url}carts/{chat_id}/items'
        logger.debug(f'create url = {url}')
        carts_items = get(url, headers=self.get_header())
        carts_items.raise_for_status()
        carts_items = carts_items.json()
        logger.debug(f'get data in dict\n{carts_items}')
        cart_items = carts_items['data']
        logger.debug(f'cart items = {cart_items}')
        return cart_price, cart_items

    def delete_item_from_cart(self, chat_id, item_id):
        logger.debug(f'Start work delete item from cart\n'
                     f'chat_id = {chat_id}\n'
                     f'item_id = {item_id}')
        url = f'{self.url}carts/{chat_id}/items/{item_id}'
        logger.debug(f'create url = {url}')
        data = delete(url, headers=self.get_header())
        data.raise_for_status()

    def delete_all_from_cart(self, chat_id):
        logger.debug(f'Start work delete item from cart\n'
                     f'chat_id = {chat_id}')

        url = f'{self.url}carts/{chat_id}/items'
        logger.debug(f'create url = {url}')
        data = delete(url, headers=self.get_header())
        data.raise_for_status()

    def create_customer_in_cms(self, chat_id, email, db):
        logger.debug(f'Start work create customer in cms\n'
                     f'chat_id = {chat_id}\n'
                     f'email = {email}\n'
                     f'db = {db}')
        url = f'{self.url}customers'
        logger.debug(f'create url = {url}')
        data = {
            "data": {
                "type": "customer",
                "name": str(chat_id),
                "email": email,
                "password": "mysecretpassword"
            }
        }
        logger.debug(f'create data for get customer\n{data}')
        customer_data = post(url, headers=self.get_header(), json=data)
        customer_data.raise_for_status()
        customer = customer_data.json()
        logger.debug(f'get customer id\n{customer}')
        customer_id = customer['data']['id']
        logger.debug(f'customer_id = {customer_id}')
        db.set(f'customer_{chat_id}', customer_id)
