import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from api.dmarketapi import DMarketApi
from api.schemas import (
    Games, MarketOffer, MarketOffers, MarketOfferPrice, MarketOfferExtra,
    LastSale, LastSales, AggregatedPrice, CumulativePrices, CumulativePrice,
    UserTargets, Target, LastPrice, TargetAttributes, ClosedTargets, ClosedTarget,
    UserItems, UserItem, Offer, ClosedOffers, ClosedOffer, SkinHistory,
    CreateOffersResponse, CreateOfferResponse, CreateOffer,
    EditOffersResponse, EditOfferResponse,
)
from datetime import datetime, timedelta


@pytest.fixture
def mock_bot():
    bot = MagicMock(spec=DMarketApi)
    bot.balance = 10000
    bot.PUBLIC_KEY = 'test_public_key'
    bot.SECRET_KEY = '0' * 128

    # Default mock returns
    bot.market_offers = AsyncMock(return_value=MarketOffers(cursor=None, objects=[]))
    bot.last_sales = AsyncMock(return_value=LastSales(sales=[]))
    bot.aggregated_prices = AsyncMock(return_value=[])
    bot.cumulative_price = AsyncMock(return_value=CumulativePrices(
        Offers=[], Targets=[], UpdatedAt=0))
    bot.offers_by_title = AsyncMock(return_value=MarketOffers(cursor=None, objects=[]))
    bot.user_targets = AsyncMock(return_value=UserTargets(Items=[], Total=0, Cursor=''))
    bot.closed_targets = AsyncMock(return_value=ClosedTargets(Trades=[], Total=0))
    bot.create_target = AsyncMock(return_value={})
    bot.delete_target = AsyncMock(return_value=[])
    bot.user_items = AsyncMock(return_value=MarketOffers(cursor=None, objects=[]))
    bot.user_offers = AsyncMock(return_value=UserItems(Items=[], Total='0'))
    bot.user_offers_closed = AsyncMock(return_value=ClosedOffers(Trades=[], Total='0'))
    bot.user_offers_create = AsyncMock(return_value=CreateOffersResponse(Result=[]))
    bot.user_offers_edit = AsyncMock(return_value=EditOffersResponse(Result=[]))
    bot.user_offers_delete = AsyncMock(return_value={})
    bot.get_balance = AsyncMock(return_value=10000)
    return bot


def make_market_offer(title='Test Skin', game_id='rust', price_usd=150, item_id='item1',
                      exterior=None):
    extra = MarketOfferExtra(
        categoryPath='path', name=title, title=title, category='weapon',
        gameId=Games(game_id), exterior=exterior
    )
    return MarketOffer(
        itemId=item_id, type='dmarket', amount=1, image='img.png',
        classId='cls1', gameId=game_id, inMarket=True, lockStatus=False,
        title=title, slug='test-skin', status='active', discount=0,
        price=MarketOfferPrice(DMC=0, USD=price_usd),
        suggestedPrice=MarketOfferPrice(DMC=0, USD=price_usd),
        extra=extra,
        fees={'dmarket': {'sell': {'percentage': 7}}}
    )


def make_last_sales(count=20, base_price=1.50):
    now = datetime.now()
    return LastSales(sales=[
        LastSale(date=now - timedelta(days=i), price=str(round(base_price + (i % 5) * 0.1, 2)))
        for i in range(count)
    ])


def make_skin_history(title='Test Skin', game='rust', avg_price=150, count=20):
    now = datetime.now()
    sales = [
        LastSale(date=now - timedelta(days=i), price=str(round(avg_price / 100 + (i % 5) * 0.1, 2)))
        for i in range(count)
    ]
    return SkinHistory(
        title=title, game=game, sales=sales,
        avg_price=avg_price, update_time=now
    )


def make_aggregated_price(title='Test Skin', order_best=1.40, order_count=5,
                           offer_best=1.60, offer_count=10):
    return AggregatedPrice(
        title=title, orderBestPrice=order_best, orderCount=order_count,
        offerBestPrice=offer_best, offerCount=offer_count
    )


def make_target(title='Test Skin', target_id='t1', amount='1', price=1.50):
    return Target(
        TargetID=target_id, Title=title, Amount=amount, Status='TargetStatusActive',
        GameID=Games.RUST, Attributes=[],
        Price=LastPrice(Currency='USD', Amount=price)
    )
