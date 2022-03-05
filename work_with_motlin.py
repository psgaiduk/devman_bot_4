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
        if data.status_code >= 300:
            logger.error(f'Что-то пошло не так код {data.status_code}\n{data.text}')

    def get_header(self):
        url = 'https://api.moltin.com/oauth/access_token'
        data = {'client_id': self.client_id, 'client_secret': self.secret_code, 'grant_type': 'client_credentials'}
        data_for_token = post(url=url, data=data)
        self.check_status(data_for_token)
        data_for_token_json = data_for_token.json()
        token = data_for_token_json['access_token']
        header = {'authorization': f'Bearer {token}', 'content-type': 'application/json'}
        return header

    def get_products(self, product_id=''):
        url = f'{self.url}products{product_id}'
        products_data = get(url, headers=self.get_header())
        self.check_status(products_data)
        return products_data.json()['data']

    def get_image_product(self, product_id):
        url = f'{self.url}files/{product_id}'
        # Временно заменил, я так понял проблемы с амазоном из-за последних событий
        # image_data = get(url, headers=self.header)
        # self.check_status(image_data)
        # return image_data.json()['data']['link']['href']
        return 'https://e1.edimdoma.ru/data/ingredients/0000/5509/5509-ed4_wide.jpg'

    def add_to_cart(self, product_id, chat_id, quantity):
        url = f'{self.url}carts/{chat_id}/items'
        data = {"data": {"id": product_id, "type": "cart_item", "quantity": quantity}}
        data = post(url, headers=self.get_header(), json=data)
        self.check_status(data)

    def get_cart(self, chat_id):
        url = f'{self.url}carts/{chat_id}'
        cart_price_data = get(url, headers=self.get_header())
        self.check_status(cart_price_data)
        cart_price = cart_price_data.json()
        cart_price = cart_price['data']['meta']['display_price']['with_tax']['formatted']
        url = f'{self.url}carts/{chat_id}/items'
        cart_items_data = get(url, headers=self.get_header())
        self.check_status(cart_items_data)
        cart_items = cart_items_data.json()
        return cart_price, cart_items['data']

    def delete_item_from_cart(self, chat_id, item_id):
        url = f'{self.url}carts/{chat_id}/items/{item_id}'
        data = delete(url, headers=self.get_header())
        self.check_status(data)

    def create_customer_in_cms(self, chat_id, email, db):
        url = f'{self.url}customers'
        data = {
         "data": {
           "type": "customer",
           "name": str(chat_id),
           "email": email,
           "password": "mysecretpassword"
         }
        }
        customer_data = post(url, headers=self.get_header(), json=data)
        self.check_status(customer_data)
        customer_id = customer_data.json()['data']['id']
        db.set(f'customer_{chat_id}', customer_id)
