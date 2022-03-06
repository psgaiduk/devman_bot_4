from requests import post, get, delete
import logging


logger = logging.getLogger('app_logger')


class WorkMoltin:

    def __init__(self, client_id, secret_code):
        self.client_id = client_id
        self.secret_code = secret_code
        self.url = 'https://api.moltin.com/v2/'

    @staticmethod
    def check_status(data):
        logger.debug(f'get status {data.status_code}')
        if data.status_code >= 300:
            logger.error(f'Что-то пошло не так код {data.status_code}\n{data.text}')

    def get_header(self):
        logger.debug('start get header')
        url = 'https://api.moltin.com/oauth/access_token'
        data = {'client_id': self.client_id, 'client_secret': self.secret_code, 'grant_type': 'client_credentials'}
        logger.debug(f'data for get token\nurl = {url}\ndata = {data}')
        data_for_token = post(url=url, data=data)
        logger.debug(f'get data token\n{data_for_token}')
        self.check_status(data_for_token)
        data_for_token_json = data_for_token.json()
        logger.debug(f'json token\n{data_for_token_json}')
        token = data_for_token_json['access_token']
        header = {'authorization': f'Bearer {token}', 'content-type': 'application/json'}
        logger.debug(f'return header = {header}')
        return header

    def get_json_data_from_moltin(self, url):
        logger.debug(f'Start work get json data from moltin\nurl = {url}')
        logger.debug(f'create url = {url}')
        data = get(url, headers=self.get_header())
        self.check_status(data)
        data_json = data.json()
        logger.debug(f'get products data in json\n{data_json}')
        return data_json

    def get_products(self, product_id=''):
        logger.debug(f'Start work get products\nproduct_id = {product_id}')
        url = f'{self.url}products{product_id}'
        logger.debug(f'create url = {url}')
        products_data_json = self.get_json_data_from_moltin(url)
        return products_data_json['data']

    def get_image_product(self, product_id):
        logger.debug(f'Start work get image product\nproduct_id = {product_id}')
        url = f'{self.url}files/{product_id}'
        logger.debug(f'create url = {url}')
        image_data_json = self.get_json_data_from_moltin(url)
        return image_data_json['data']['link']['href']

    def add_to_cart(self, product_id, chat_id, quantity):
        logger.debug(f'Start work add to cart\nproduct_id = {product_id}\n'
                     f'chat_id = {chat_id}\n'
                     f'quantity = {quantity}')
        url = f'{self.url}carts/{chat_id}/items'
        logger.debug(f'create url = {url}')
        data = {"data": {"id": product_id, "type": "cart_item", "quantity": quantity}}
        logger.debug(f'data to post request\n{data}')
        data = post(url, headers=self.get_header(), json=data)
        self.check_status(data)

    def get_cart(self, chat_id):
        logger.debug(f'Start work get cart\nchat_id = {chat_id}')
        url = f'{self.url}carts/{chat_id}'
        logger.debug(f'create url = {url}')
        cart_price_json = self.get_json_data_from_moltin(url)
        cart_price = cart_price_json['data']['meta']['display_price']['with_tax']['formatted']
        logger.debug(f'get cart price = {cart_price}')
        url = f'{self.url}carts/{chat_id}/items'
        logger.debug(f'create url = {url}')
        cart_items_json = self.get_json_data_from_moltin(url)
        cart_items = cart_items_json['data']
        logger.debug(f'cart items = {cart_items}')
        print(cart_items)
        return cart_price, cart_items

    def delete_item_from_cart(self, chat_id, item_id=''):
        logger.debug(f'Start work delete item from cart\n'
                     f'chat_id = {chat_id}\n'
                     f'item_id = {item_id}')
        if item_id:
            item_id = f'/{item_id}'
        url = f'{self.url}carts/{chat_id}/items{item_id}'
        logger.debug(f'create url = {url}')
        data = delete(url, headers=self.get_header())
        self.check_status(data)

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
        self.check_status(customer_data)
        customer_id_json = customer_data.json()
        logger.debug(f'get customer id json\n{customer_id_json}')
        customer_id = customer_id_json['data']['id']
        logger.debug(f'customer_id = {customer_id}')
        db.set(f'customer_{chat_id}', customer_id)
