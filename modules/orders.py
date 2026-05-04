from itertools import groupby
from api.dmarketapi import DMarketApi
from time import time
from db.crud import SelectSkin
from config import logger, BuyParams, Timers, GAMES, BAD_ITEMS, SELL_FEE
from typing import List, Tuple
from api.schemas import SkinHistory, SkinOrder, Target, CreateTarget, \
    CreateTargets, LastPrice, TargetAttributes, CumulativePrice
import math
import re
from pyti.simple_moving_average import simple_moving_average as sma


def sale_price_amount(price: str) -> float:
    value = re.sub(r"[^\d.,-]", "", price or "").replace(",", ".")
    if not value:
        return 0.0
    amount = float(value)
    if "." in value:
        return amount * 100
    return amount


def sale_timestamp(sale) -> int:
    return int(sale.date.timestamp())


def moving_average_5(history) -> list:
    prices = [sale_price_amount(i.price) for i in history]
    prices.reverse()
    result = list(sma(prices, 5))
    result.reverse()
    return result


class OrderAnalytics:
    def __init__(self, bot: DMarketApi):
        self.bot = bot
        self.repeat = Timers.ORDERS_BASE
        self.frequency = BuyParams.FREQUENCY

        self.max_price = BuyParams.MAX_PRICE
        self.min_price = BuyParams.MIN_PRICE
        self.all_sales = BuyParams.ALL_SALES

        self.avg_price_count = BuyParams.AVG_PRICE_COUNT
        self.profit_percent = BuyParams.PROFIT_PERCENT
        self.good_points_percent = BuyParams.GOOD_POINTS_PERCENT
        self.first_sale = BuyParams.FIRST_SALE
        self.last_sale = BuyParams.LAST_SALE
        self.days_count = BuyParams.DAYS_COUNT
        self.sale_count = BuyParams.SALE_COUNT
        self.max_count_offers = BuyParams.MAX_COUNT_SELL_OFFERS

        self.boost_percent = BuyParams.BOOST_PERCENT
        self.boost_points = BuyParams.BOOST_POINTS

        self.max_threshold = BuyParams.MAX_THRESHOLD
        self.min_threshold = BuyParams.MIN_THRESHOLD

    def popularity_control(self, skins: List[SkinHistory]) -> List[SkinHistory]:
        items = list()
        for skin in skins:
            if not skin.sales:
                continue
            sales = list()
            first_sale = sale_timestamp(skin.sales[-1])
            last_sale = sale_timestamp(skin.sales[0])
            if first_sale < (time() - self.first_sale * 60 * 60 * 24):
                if last_sale > (time() - self.last_sale * 60 * 60 * 24):
                    for sale in skin.sales:
                        if sale_timestamp(sale) > (time() - self.days_count * 60 * 60 * 24):
                            sales.append(sale)
                    if len(sales) >= self.sale_count:
                        items.append(skin)
        return items

    def boost_control(self, skins: List[SkinHistory]) -> List[SkinHistory]:
        new_skins = list()
        for item in skins:
            mov_av = moving_average_5(item.sales)
            delete_points = 0
            try:
                for i in range(len(mov_av[:-4])):
                    if sale_price_amount(item.sales[i].price) > \
                            mov_av[i] * (1 + self.boost_percent / 100):
                        item.sales.pop(i)
                        delete_points += 1
                if delete_points <= self.boost_points:
                    new_skins.append(item)
            except IndexError:
                pass
        return new_skins

    async def good_skins(self, skins: List[SkinHistory]) -> List[SkinOrder]:
        items = list()
        skins = sorted(skins, key=lambda x: x.title)
        names = [i.title for i in skins]
        aggregated = await self.bot.aggregated_prices(names)
        aggregated = sorted(aggregated, key=lambda x: x.title)

        for skin, agr in zip(skins, aggregated):
            best_order = agr.orderBestPrice * 100
            points_count = math.ceil(len(skin.sales) / 100 * self.good_points_percent)
            count = 0
            for i in skin.sales:
                price_with_fee = sale_price_amount(i.price) * (1 - SELL_FEE / 100)
                if price_with_fee > best_order * (1 + self.profit_percent / 100):
                    count += 1
            if count >= points_count:
                if agr.offerCount <= self.max_count_offers:
                    items.append(SkinOrder(title=skin.title, bestOrder=int(best_order), game=skin.game))
        return items

    async def frequency_skins(self, skins: List[SkinHistory]) -> List[SkinOrder]:
        items = list()
        skins = sorted(skins, key=lambda x: x.title)
        names = [i.title for i in skins]
        aggregated = await self.bot.aggregated_prices(names)
        aggregated = sorted(aggregated, key=lambda x: x.title)
        for skin, agr in zip(skins, aggregated):
            best_order = agr.orderBestPrice * 100
            my_sell_price = best_order * (1 + self.profit_percent / 100)

            count = 0
            points_count = math.ceil(len(skin.LastSales) / 100 * self.good_points_percent)
            for i in skin.LastSales:
                price_with_fee = i.Price.Amount * (1 - SELL_FEE / 100)
                if price_with_fee > my_sell_price:
                    count += 1
            if count >= points_count:
                if agr.offerCount <= self.max_count_offers:
                    items.append(SkinOrder(title=skin.title, bestOrder=int(best_order), game=skin.game))
        return items

    @staticmethod
    def first_second_offer(info: List[CumulativePrice]) -> tuple:
        len_offers = len(info)
        if len_offers == 0:
            best_offer_price = 0
            second_offer_price = 0
        else:
            best_offer = info[0]
            if len_offers == 1:
                second_offer = best_offer
            else:
                if best_offer.Amount == 1:
                    second_offer = info[1]
                else:
                    second_offer = best_offer
            best_offer_price = best_offer.Price
            second_offer_price = second_offer.Price
        return best_offer_price, second_offer_price, len_offers

    async def analyze_market_offers(self, skin: SkinHistory):
        market_info = await self.bot.cumulative_price(skin.title, skin.game)
        len_avg = skin.sales[0:self.avg_price_count]
        avg_price_10 = sum(float(s.price) for s in len_avg) / len(len_avg)
        best_offer, second_offer, offers_count = self.first_second_offer(market_info.Offers)
        best_target, second_target, targets_count = self.first_second_offer(market_info.Targets)
        if best_offer == 0 or (best_target - second_target) / best_offer * 100 > 3:
            best_target = second_target
        if second_offer == 0 or (second_offer - best_offer) / second_offer * 100 > 3:
            best_offer = second_offer
        profit = -(best_target - (1 - SELL_FEE / 100) * best_offer) / best_target * 100
        profit_by_avg = -(best_target - (1 - SELL_FEE / 100) * avg_price_10) / best_target * 100
        return best_offer, best_target, offers_count, targets_count, profit, round(profit_by_avg, 2)

    async def frequency2(self, skins: List[SkinHistory]) -> List[SkinOrder]:
        items = list()
        skins = sorted(skins, key=lambda x: x.title)
        for skin in skins:
            best_offer, best_target, offers_count, targets_count, profit, profit_2 = \
                await self.analyze_market_offers(skin)

            if profit_2 > self.profit_percent and profit > self.profit_percent:
                my_sell_price = best_target * (1 + self.profit_percent / 100)
                count = 0
                points_count = math.ceil(len(skin.LastSales) / 100 * self.good_points_percent)
                for i in skin.LastSales:
                    price_with_fee = i.Price.Amount * (1 - SELL_FEE / 100)
                    if price_with_fee > my_sell_price:
                        count += 1
                if count >= points_count:
                    if offers_count <= self.max_count_offers:
                        items.append(SkinOrder(title=skin.title, bestOrder=int(best_target * 100), game=skin.game))
        return items

    async def skins_to_buy(self) -> List[SkinOrder]:
        t = time()
        new_skins = list()
        skins = []
        for game in GAMES:
            all_skins = SelectSkin.select_all()
            logger.debug(f'ALL SKINS {len(all_skins)}')
            skins += [i for i in all_skins if self.min_price < i.avg_price < self.max_price
                      and i.game == game.value]
        logger.info(f'SKINS {len(skins)}')
        if skins:
            skins = self.popularity_control(skins)
            logger.info(f'POP CONTROL {len(skins)}')
            skins = self.boost_control(skins)
            logger.info(f'BOOST CONTROL {len(skins)}')
            if self.frequency:
                skins = await self.frequency2(skins)
            else:
                skins = await self.good_skins(skins)
            logger.info(f'GOOD CONTROL {len(skins)}')
            for skin in skins:
                skin.maxPrice = int(skin.bestOrder * (1 + self.max_threshold / 100))
                skin.minPrice = int(skin.bestOrder * (1 - self.min_threshold / 100))
                new_skins.append(skin)
        logger.debug(f'Database of orders was updated {round(time() - t, 2)} sec.')
        return new_skins


class Orders:
    def __init__(self, bot: DMarketApi):
        self.bot = bot
        self.order_list = OrderAnalytics(self.bot)

    @staticmethod
    def order_price(max_p, min_p, best):
        if best > max_p:
            return max_p
        elif min_p < best <= max_p:
            return best + 1
        else:
            return min_p

    @staticmethod
    def sort_targets(skins: List[SkinOrder], targets: List[Target]) -> Tuple[List[SkinOrder], List[Target], List[Target]]:
        good_targets = [i for i in targets if i.Title in [s.title for s in skins]]
        bad_targets = [i for i in targets if i.Title not in [s.title for s in skins]]
        new_skins = [i for i in skins if i.title not in [s.Title for s in targets]]
        return new_skins, good_targets, bad_targets

    async def create_order(self, item: SkinOrder):
        offer = await self.bot.market_offers(name=item.title, limit=1, game=item.game)
        if offer.objects and offer.objects[0].title == item.title:
            offer = offer.objects[0]
            price = LastPrice(Currency='USD', Amount=item.bestOrder / 100)
            attributes = [TargetAttributes(Name='name', Value=offer.extra.name),
                          TargetAttributes(Name='title', Value=offer.title),
                          TargetAttributes(Name='category', Value=offer.extra.category),
                          TargetAttributes(Name='gameId', Value=offer.gameId),
                          TargetAttributes(Name='categoryPath', Value=offer.extra.categoryPath),
                          TargetAttributes(Name='image', Value=offer.image)]
            if offer.extra.exterior:
                attributes.append(TargetAttributes(Name='exterior', Value=offer.extra.exterior))
            target = CreateTarget(Amount='1', Price=price, Title=offer.title, Attrs=attributes)
            targets = CreateTargets(GameID=offer.gameId, Targets=[target])
            order = await self.bot.create_target(targets)
            return order
        return []

    async def check_offers(self, item: SkinOrder):
        offers = await self.bot.offers_by_title(name=item.title, limit=3)
        offers = sorted(offers.objects, key=lambda x: int(x.price.USD))
        offer_prices = [o.price.USD for o in offers]
        my_sell_price = item.bestOrder * (1 + self.order_list.profit_percent / 100)
        return any(my_sell_price <= p for p in offer_prices)

    async def update_orders(self):
        t = time()
        logger.debug('Update orders')
        skins = await self.order_list.skins_to_buy()
        logger.debug(f'Skins to buy: {len(skins)}')
        targets = await self.bot.user_targets(limit='1000')
        name_group = [list(j) for _, j in groupby(targets.Items, key=lambda x: x.Title)]
        targets_inactive = await self.bot.user_targets(limit='1000', status='TargetStatusInactive')
        logger.debug(f'Inactive {len(targets_inactive.Items)}')
        new, good, bad = self.sort_targets(skins, targets.Items)
        for name in name_group:
            if len(name) > 1:
                bad += name[1:]
        logger.debug(f'Bad {len(bad)}')
        await self.bot.delete_target(bad + targets_inactive.Items)
        for skin in new:
            logger.info(f'{skin.title} {skin.bestOrder} {skin.minPrice} {skin.maxPrice}')
            if self.bot.balance > skin.bestOrder:
                if any(i in skin.title.lower() for i in BAD_ITEMS):
                    continue
                if await self.check_offers(skin):
                    await self.create_order(skin)
        if good:
            logger.debug(f'Good {len(good)}')
            for i in good:
                for j in skins:
                    if i.Title == j.title:
                        if i.Price.Amount * 100 != j.bestOrder:
                            order_price = self.order_price(j.maxPrice, j.minPrice, j.bestOrder)
                            j.bestOrder = order_price
                            if await self.check_offers(j):
                                await self.bot.delete_target([i])
                                await self.create_order(j)

        logger.debug(f'Orders were updated {round(time() - t, 2)} sec.')
