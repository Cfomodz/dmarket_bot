import sys
from os import getenv

from dotenv import load_dotenv
from loguru import logger

from api.schemas import Games

load_dotenv()

PUBLIC_KEY = getenv("DMARKET_PUBLIC_KEY")
SECRET_KEY = getenv("DMARKET_SECRET_KEY")

if not PUBLIC_KEY or not SECRET_KEY:
    raise RuntimeError(
        "Missing DMarket API credentials. Copy .env.example to .env and set "
        "DMARKET_PUBLIC_KEY and DMARKET_SECRET_KEY."
    )

logger_config = {
    "handlers": [
        {"sink": sys.stderr, 'colorize': True, 'level': 'INFO'},
        {"sink": sys.stderr, "serialize": False, 'level': 'DEBUG'},
        {"sink": "log/info.log", "serialize": False, 'level': 'INFO'},
    ]
}
logger.configure(**logger_config)

API_URL = "https://api.dmarket.com"
GAMES = [Games.RUST]
DATABASE_NAME = '/skins.db'

BAD_ITEMS = ['key', 'pin', 'sticker', 'case', 'operation', 'pass', 'capsule', 'package',
             'challengers', 'patch', 'music', 'kit', 'graffiti']

SELL_FEE = 7


class Timers:
    PREV_BASE = 60 * 60 * 5
    ORDERS_BASE = 60 * 10


class PrevParams:
    MIN_AVG_PRICE = 90
    MAX_AVG_PRICE = 225


class BuyParams:
    STOP_ORDERS_BALANCE = 500
    FREQUENCY = True
    MIN_PRICE = 90
    MAX_PRICE = 225

    PROFIT_PERCENT = 15
    GOOD_POINTS_PERCENT = 30
    AVG_PRICE_COUNT = 7

    ALL_SALES = 80
    DAYS_COUNT = 23
    SALE_COUNT = 11
    LAST_SALE = 3
    FIRST_SALE = 20

    MAX_COUNT_SELL_OFFERS = 20

    BOOST_PERCENT = 24
    BOOST_POINTS = 3

    MAX_THRESHOLD = 0.1
    MIN_THRESHOLD = 3


class SellParams:
    MIN_PERCENT = 7
    MAX_PERCENT = 15
