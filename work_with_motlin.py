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
        try:
            data.raise_for_status()
        except Exception as err:
            logger.exception(err)

    def get_header(self):
        logger.debug('start get header')
        url = 'https://api.moltin.com/oauth/access_token'
        data = {'client_id': self.client_id, 'client_secret': self.secret_code, 'grant_type': 'client_credentials'}
        logger.debug(f'data for get token\nurl = {url}\ndata = {data}')
        response_with_token = post(url=url, data=data)
        logger.debug(f'get data token\n{response_with_token}')
        self.check_status(response_with_token)
        dict_with_token = response_with_token.json()
        logger.debug(f'dict with token\n{dict_with_token}')
        token = dict_with_token['access_token']
        header = {'authorization': f'Bearer {token}', 'content-type': 'application/json'}
        logger.debug(f'return header = {header}')
        return header

    def get_data_from_moltin(self, url):
        logger.debug(f'Start work get json data from moltin\nurl = {url}')
        logger.debug(f'create url = {url}')
        data = get(url, headers=self.get_header())
        self.check_status(data)
        data = data.json()
        logger.debug(f'get data in dict\n{data}')
        return data

    def get_products(self, product_id=''):
        logger.debug(f'Start work get products\nproduct_id = {product_id}')
        url = f'{self.url}products{product_id}'
        logger.debug(f'create url = {url}')
        products = self.get_data_from_moltin(url)
        return products['data']

    def get_image_product(self, product_id):
        logger.debug(f'Start work get image product\nproduct_id = {product_id}')
        url = f'{self.url}files/{product_id}'
        logger.debug(f'create url = {url}')
        image_product = self.get_data_from_moltin(url)
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
        self.check_status(data)

    def get_cart(self, chat_id):
        logger.debug(f'Start work get cart\nchat_id = {chat_id}')
        url = f'{self.url}carts/{chat_id}'
        logger.debug(f'create url = {url}')
        carts = self.get_data_from_moltin(url)
        cart_price = carts['data']['meta']['display_price']['with_tax']['formatted']
        logger.debug(f'get cart price = {cart_price}')
        url = f'{self.url}carts/{chat_id}/items'
        logger.debug(f'create url = {url}')
        carts_items = self.get_data_from_moltin(url)
        cart_items = carts_items['data']
        logger.debug(f'cart items = {cart_items}')
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
        customer = customer_data.json()
        logger.debug(f'get customer id json\n{customer}')
        customer_id = customer['data']['id']
        logger.debug(f'customer_id = {customer_id}')
        db.set(f'customer_{chat_id}', customer_id)
