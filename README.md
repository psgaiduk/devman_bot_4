## Description

This telegram shop, working with https://www.elasticpath.com/

In telegram client can:
- Add item to the cart
- Delete item from the cart
- Get product information
- Leave contacts for the order 
(A customer will be automatically created in CMS)

Example work telegram:

![](img/fish-shop.gif)

## Project setup

It is necessary to register ENVIRONMENT variables.
The variable template and their description are in the file

## Installation

Install libraries ```pip install -r requirements.txt```

This command will immediately install:
1. python-dotenv~=0.19.2
2. requests~=2.27.1
3. python-telegram-bot==11.1.0
4. redis==3.2.1

Create project in [Redis](https://redis.com/)
Create shop in [Moltin](https://www.elasticpath.com/)

#### ENVIRONMENT variables used in the project:
1. TELEGRAM_TOKEN - token for use telegram [@BotFather](https://t.me/BotFather)
2. TOKEN_TELEGRAM_LOGGER - token for send log in telegram [@BotFather](https://t.me/BotFather)
3. CHAT_ID - your chat id in telegram where you will be get log message. [Get Chat ID](https://t.me/userinfobot)
4. REDIS_HOST - redis db host
5REDIS_PORT - redis db port 
5. REDIS_PASSWORD - redis password 
6. MOLTIN_CLIENT_ID - client ID in [Moltin (HOME)](https://www.elasticpath.com/)
7. MOLTIN_CLIENT_SECRET - secret key in [Moltin (HOME)](https://www.elasticpath.com/)


## Start Bot

if you want to run shop in telegram ```python main.py```


## Moltin
Firstly you need to fill the shop catalog, but don't forget to add 
pictures and prices for items.

