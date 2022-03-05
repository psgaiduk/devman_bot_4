from requests import post, get, delete


class WorkMoltin:

    def __init__(self, client_id, secret_code):
        self.client_id = client_id
        self.secret_code = secret_code
        self.url = 'https://api.moltin.com/v2/'

    def get_header(self):
        url = 'https://api.moltin.com/oauth/access_token'
        data = {'client_id': self.client_id, 'client_secret': self.secret_code, 'grant_type': 'client_credentials'}
        data_for_token = post(url=url, data=data).json()
        token = data_for_token['access_token']
        header = {'authorization': f'Bearer {token}', 'content-type': 'application/json'}
        return header

    def get_products(self, product_id=''):
        url = f'{self.url}products{product_id}'
        return get(url, headers=self.get_header()).json()['data']

    def get_image_product(self, product_id):
        url = f'{self.url}files/{product_id}'
        # Временно заменил, я так понял проблемы с амазоном из-за последних событий
        # return get(url, headers=self.header).json()['data']['link']['href']
        return 'https://e1.edimdoma.ru/data/ingredients/0000/5509/5509-ed4_wide.jpg'

    def add_to_cart(self, product_id, chat_id, quantity):
        url = f'{self.url}carts/{chat_id}/items'
        data = {"data": {"id": product_id, "type": "cart_item", "quantity": quantity}}
        post(url, headers=self.get_header(), json=data)

    def get_cart(self, chat_id):
        url = f'{self.url}carts/{chat_id}'
        cart_price = get(url, headers=self.get_header()).json()
        cart_price = cart_price['data']['meta']['display_price']['with_tax']['formatted']
        url = f'{self.url}carts/{chat_id}/items'
        cart_items = get(url, headers=self.get_header()).json()
        return cart_price, cart_items['data']

    def delete_item_from_cart(self, chat_id, item_id):
        url = f'{self.url}carts/{chat_id}/items/{item_id}'
        delete(url, headers=self.get_header())

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
        customer = post(url, headers=self.get_header(), json=data)
        customer_id = customer.json()['data']['id']
        db.set(f'customer_{chat_id}', customer_id)