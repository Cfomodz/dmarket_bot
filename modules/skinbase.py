import asyncio
import datetime
import re
from itertools import groupby
from time import time

from pydantic import ValidationError

from api.dmarketapi import DMarketApi
from api.schemas import Games, MarketOffer, SkinHistory
from config import BAD_ITEMS, GAMES, BuyParams, PrevParams, Timers, logger
from db.crud import SelectSkin


class SkinBase:
    MAX_CONCURRENT_REQUESTS = 5

    def __init__(self, api: DMarketApi):
        self.api = api
        self.repeat = Timers.PREV_BASE
        self.min_price = PrevParams.MIN_AVG_PRICE
        self.max_price = PrevParams.MAX_AVG_PRICE
        self.select_skin = SelectSkin()
        self.min_price_buy = BuyParams.MIN_PRICE
        self.max_price_buy = BuyParams.MAX_PRICE

    @staticmethod
    def check_name(item_name: str):
        name_lower = item_name.lower()
        for bad in BAD_ITEMS:
            if re.search(r"\b" + re.escape(bad) + r"\b", name_lower):
                return False
        return True

    async def get_items(self, min_p: int, max_p: int, game: Games) -> list[MarketOffer]:
        logger.debug(f"Game: {game}. Get items from {min_p} to {max_p}")
        market_offers = await self.api.market_offers(price_from=min_p, price_to=max_p, game=game)
        logger.debug(f"Market offers: {len(market_offers.objects)}")
        cursor = market_offers.cursor
        while cursor:
            logger.debug(f"Game: {game}. Get items from {min_p} to {max_p}. Cursor: {cursor}")
            other_offers = await self.api.market_offers(
                price_from=min_p, price_to=max_p, cursor=cursor, game=game
            )
            market_offers.objects += other_offers.objects
            logger.debug(f"Market offers: {len(market_offers.objects)}")
            cursor = other_offers.cursor
        market_offers.objects = sorted(market_offers.objects, key=lambda x: x.title)
        skins = [list(group)[0] for _, group in groupby(market_offers.objects, lambda x: x.title)]
        return [s for s in skins if self.check_name(s.title)]

    async def _fetch_one(
        self, sem: asyncio.Semaphore, item: MarketOffer | SkinHistory, min_p: float, max_p: float
    ) -> SkinHistory | None:
        if isinstance(item, MarketOffer):
            game = Games(item.gameId)
        else:
            game = Games(item.game)
        try:
            async with sem:
                history = await self.api.last_sales(item.title, game=game)
            if len(history.sales) == 20:
                prices = [s.price_cents for s in history.sales]
                avg_price = sum(prices) / len(prices)
                if min_p <= avg_price <= max_p:
                    return SkinHistory(
                        title=item.title,
                        game=game.value,
                        sales=history.sales,
                        avg_price=avg_price,
                        update_time=datetime.datetime.now(),
                    )
        except ValidationError as e:
            logger.error(e.json())
        except Exception as e:
            logger.error(f"Exception in skinbase: {e}")
        return None

    async def filter_skins(
        self, skins: list[MarketOffer | SkinHistory], min_p: int, max_p: int
    ) -> list[SkinHistory]:
        min_p = min_p * 0.9
        max_p = max_p * 1.1
        sem = asyncio.Semaphore(self.MAX_CONCURRENT_REQUESTS)
        results = []
        # Process in chunks so progress is visible and a crash loses little work
        chunk_size = 500
        for start in range(0, len(skins), chunk_size):
            chunk = skins[start : start + chunk_size]
            fetched = await asyncio.gather(*(self._fetch_one(sem, i, min_p, max_p) for i in chunk))
            results += [s for s in fetched if s]
            logger.debug(f"Parsed {min(start + chunk_size, len(skins))}/{len(skins)} skins/items.")
        return results

    async def update_base(self):
        final_skins = list()
        for game in GAMES:
            skins = await self.get_items(self.min_price, self.max_price, game)
            logger.debug(f"Game: {game}. Skins: {len(skins)}")
            skins = [s for s in skins if not self.select_skin.skin_existence(s)]
            logger.debug(f"Game: {game}. New skins: {len(skins)}")
            final_skins += await self.filter_skins(skins, self.min_price, self.max_price)
        self.select_skin.create_all_skins(final_skins)
        logger.info(f"Total skins analyzed: {len(final_skins)}")

    async def update(self):
        now = time()
        await self.update_base()
        skins_to_update = [
            s
            for s in self.select_skin.select_update_time(now, self.repeat)
            if self.min_price_buy < round(s.avg_price, 2) < self.max_price_buy
        ]
        logger.debug(f"Skins to update: {len(skins_to_update)}")
        if not skins_to_update:
            logger.info("No skins to update are available.")
            return
        skins = await self.filter_skins(skins_to_update, self.min_price, self.max_price)
        logger.debug(f"Final filtered skins to update: {len(skins)}")
        self.select_skin.find_by_name(skins)
        logger.info(f"The skin/item database was updated {round((time() - now) / 60, 2)} minutes.")
