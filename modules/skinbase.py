import datetime
from itertools import groupby
from time import time
from pydantic import ValidationError
from typing import List, Union
from api.dmarketapi import DMarketApi
from db.crud import SelectSkin
from api.schemas import MarketOffer, Games, SkinHistory
from config import logger, PrevParams, BuyParams, Timers, BAD_ITEMS, GAMES


class SkinBase:
    def __init__(self, api: DMarketApi):
        self.api = api
        self.repeat = Timers.PREV_BASE
        self.min_price = PrevParams.MIN_AVG_PRICE
        self.max_price = PrevParams.MAX_AVG_PRICE
        # self.popularity = PrevParams.POPULARITY
        self.select_skin = SelectSkin()
        self.min_price_buy = BuyParams.MIN_PRICE
        self.max_price_buy = BuyParams.MAX_PRICE

    @staticmethod
    def check_name(item_name: str):
        for i in BAD_ITEMS:
            if i in item_name.lower():
                if 'Emerald Pinstripe' not in item_name and 'Monkey Business' not in item_name and 'Case Hardened' not in item_name:
                    return False
        logger.debug(f'Item name: {item_name}, checked and returning True')
        return True

    async def get_items(self, min_p: int, max_p: int, game: Games) -> List[MarketOffer]:
        logger.debug(f'Game: {game}. Get items from {min_p} to {max_p}')
        market_offers = await self.api.market_offers(price_from=min_p, price_to=max_p, game=game)
        logger.debug(f'Market offers: {len(market_offers.objects)}')
        cursor = market_offers.cursor
        while cursor:
            logger.debug(f'Game: {game}. Get items from {min_p} to {max_p}. Cursor: {cursor}')
            other_offers = await self.api.market_offers(price_from=min_p, price_to=max_p,
                                                        cursor=cursor, game=game)
            market_offers.objects += other_offers.objects
            logger.debug(f'Market offers: {len(market_offers.objects)}')
            cursor = other_offers.cursor
            logger.debug(f"Cursor: {cursor}")
        market_offers.objects = sorted(market_offers.objects, key=lambda x: x.title)
        skins = [list(group)[0] for _, group in groupby(market_offers.objects, lambda x: x.title)]
        return [s for s in skins if self.check_name(s.title)]

    async def filter_skins(self, skins: List[Union[MarketOffer, SkinHistory]], min_p: int, max_p: int) -> \
            List[SkinHistory]:
        logger.debug(f'Min price: {min_p}. Max price: {max_p}')
        min_p = min_p * 0.9
        max_p = max_p * 1.1
        logger.debug(f'New min price: {min_p}. New max price: {max_p}')
        s = list()
        count = 0
        for i in skins:
            if isinstance(i, MarketOffer):
                game = Games(i.gameId)
            else:
                game = Games(i.game)
            try:
                logger.debug(f'Game: {game}. Get history for {i.title}')
                history = await self.api.last_sales(i.title, game=game)
                # logger.debug(f'History: {history}')
                # logger.debug(f'History: {len(history.sales)}')
                if len(history.sales) == 20:
                    prices = [float(i.price) for i in history.sales]
                    # logger.debug(f"Prices: {prices}")
                    count_prices = len(prices)
                    avg_price = sum(prices) / count_prices
                    logger.debug(f"Avg price: {round(avg_price, 2)}")
                    if min_p/100 <= avg_price <= max_p/100:
                        logger.debug(f"Skin: {i.title}. Game: {game}. Avg price: {avg_price}. Min price: {min_p}. Max price: {max_p} is valid, creating SkinHostory object")
                        try:
                            sk = SkinHistory(
                            title=i.title,
                            game=game.value,
                            sales=history.sales,
                            avg_price=avg_price,
                            update_time=datetime.datetime.now()
                            )   
                            logger.debug(f"SkinHistory object created: {sk}")
                            s.append(sk)
                            logger.debug(f"Length of skins: {len(s)}")
                        except ValidationError as e:
                            logger.error(e.json())
            except Exception as e:
                logger.error(f'Exception in skinbase{e}')
            if count % 500 == 0:
                logger.debug(f'Game: {game}. Parsed {count} skins/items.')
            count += 1
        return s

    async def update_base(self):
        final_skins = list()
        for game in GAMES:
            logger.debug(game)
            skins = await self.get_items(self.min_price, self.max_price, game)
            logger.debug(f'Game: {game}. Skins: {len(skins)} @ point 1')
            skins = [s for s in skins if not self.select_skin.skin_existence(s)]
            logger.debug(f"Game: {game}. Skins: {len(skins)} @ point 2")
            final_skins += await self.filter_skins(skins, self.min_price, self.max_price)
            logger.debug(f"Game: {game}. Final skins: {len(final_skins)}")
        self.select_skin.create_all_skins(final_skins)
        logger.info(f'Total skins analyzed: {len(final_skins)}')

    async def update(self):
        now = time()
        await self.update_base()
        skins_to_update = [s for s in self.select_skin.select_update_time(now, self.repeat)
                        if self.min_price_buy/100 < round(s.avg_price,2) < self.max_price_buy/100]
        logger.debug(f'Skins to update: {len(skins_to_update)}')
        if not skins_to_update:
            logger.info('No skins to update are available.')
        skins = await self.filter_skins(skins_to_update, self.min_price, self.max_price)
        logger.debug(f'Final Filtered skins to update: {len(skins)}')
        self.select_skin.find_by_name(skins)
        logger.debug(f"There should now be at least {len(skins)} skins in the database.")
        logger.debug(f"There are {len(self.select_skin.select_all())} skins in the database.")
        logger.info(f'The skin/item database was updated {round((time() - now) / 60, 2)} minutes.')
