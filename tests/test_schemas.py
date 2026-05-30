"""Tests for API schema models."""
import pytest
from datetime import datetime
from api.schemas import (
    Games, Balance, LastPrice, LastSale, LastSales,
    MarketOfferPrice, MarketOfferExtra, MarketOffer, MarketOffers,
    AggregatedPriceFilter, AggregatedPricesRequest, AggregatedPrice, AggregatedPricesResponse,
    Target, TargetAttributes, UserTargets, ClosedTarget, ClosedTargets,
    CreateTarget, CreateTargets,
    UserItem, UserItems, Offer, ClosedOffer, ClosedOffers,
    CreateOffer, EditOffer, CreateOffers, EditOffers,
    DeleteOffer, DeleteOffers,
    SkinHistory, SkinOrder, SellOffer,
    CumulativePrice, CumulativePrices,
)


class TestGames:
    def test_game_values(self):
        assert Games.CS.value == 'a8db'
        assert Games.DOTA.value == '9a92'
        assert Games.RUST.value == 'rust'
        assert Games.TF2.value == 'tf2'

    def test_game_from_value(self):
        assert Games('rust') == Games.RUST
        assert Games('a8db') == Games.CS


class TestBalance:
    def test_balance_parse(self):
        b = Balance(usd=1500)
        assert b.usd == 1500

    def test_balance_from_dict(self):
        b = Balance(**{'usd': 2500})
        assert b.usd == 2500


class TestLastSales:
    def test_last_sale(self):
        sale = LastSale(date=datetime(2024, 1, 1), price='1.50')
        assert sale.price == '1.50'

    def test_last_sales_list(self):
        sales = LastSales(sales=[
            LastSale(date=datetime(2024, 1, 1), price='1.50'),
            LastSale(date=datetime(2024, 1, 2), price='1.60'),
        ])
        assert len(sales.sales) == 2


class TestAggregatedPrices:
    def test_request_model(self):
        req = AggregatedPricesRequest(
            limit=50,
            filter=AggregatedPriceFilter(game='rust', titles=['Skin A', 'Skin B'])
        )
        d = req.model_dump()
        assert d['limit'] == 50
        assert d['filter']['game'] == 'rust'
        assert len(d['filter']['titles']) == 2

    def test_response_model(self):
        resp = AggregatedPricesResponse(
            aggregatedPrices=[
                AggregatedPrice(title='Skin A', orderBestPrice=1.5, orderCount=3,
                                offerBestPrice=1.8, offerCount=10)
            ],
            nextCursor='abc'
        )
        assert len(resp.aggregatedPrices) == 1
        assert resp.aggregatedPrices[0].title == 'Skin A'
        assert resp.nextCursor == 'abc'

    def test_aggregated_price_defaults(self):
        ap = AggregatedPrice(title='Test')
        assert ap.orderBestPrice == 0
        assert ap.offerCount == 0


class TestCreateTargets:
    def test_create_target_has_title(self):
        ct = CreateTarget(
            Amount='1',
            Price=LastPrice(Currency='USD', Amount=1.50),
            Title='Test Skin'
        )
        assert ct.Title == 'Test Skin'

    def test_create_targets_has_game_id(self):
        ct = CreateTarget(
            Amount='1',
            Price=LastPrice(Currency='USD', Amount=1.50),
            Title='Test Skin'
        )
        cts = CreateTargets(GameID='rust', Targets=[ct])
        d = cts.model_dump()
        assert d['GameID'] == 'rust'
        assert len(d['Targets']) == 1
        assert d['Targets'][0]['Title'] == 'Test Skin'

    def test_create_target_with_attrs(self):
        ct = CreateTarget(
            Amount='1',
            Price=LastPrice(Currency='USD', Amount=1.50),
            Title='Test Skin',
            Attrs=[TargetAttributes(Name='exterior', Value='Factory New')]
        )
        assert len(ct.Attrs) == 1


class TestMarketOffer:
    def test_market_offer_parse(self):
        offer = MarketOffer(
            itemId='id1', type='dmarket', amount=1, image='img.png',
            classId='c1', gameId='rust', inMarket=True, lockStatus=False,
            title='Test', slug='test', status='active', discount=0,
            price=MarketOfferPrice(DMC=0, USD=150),
            suggestedPrice=MarketOfferPrice(DMC=0, USD=150),
            extra=MarketOfferExtra(),
            fees={'dmarket': {'sell': {'percentage': 7}}}
        )
        assert offer.title == 'Test'
        assert offer.gameId == 'rust'


class TestSkinHistory:
    def test_inherits_last_sales(self):
        sh = SkinHistory(
            title='Test', game='rust',
            sales=[LastSale(date=datetime.now(), price='1.5')],
            avg_price=1.5, update_time=datetime.now()
        )
        assert sh.title == 'Test'
        assert len(sh.sales) == 1


class TestSkinOrder:
    def test_optional_fields(self):
        so = SkinOrder(title='Test', game=Games.RUST)
        assert so.bestOrder is None
        assert so.maxPrice is None


class TestSellOffer:
    def test_defaults(self):
        so = SellOffer(AssetID='a1')
        assert so.fee == 7
        assert so.title is None

    def test_from_attributes(self):
        assert SellOffer.model_config.get('from_attributes') is True


class TestDeleteOffers:
    def test_force_default(self):
        do = DeleteOffers(objects=[])
        assert do.force is True


class TestCumulativePrices:
    def test_parse(self):
        cp = CumulativePrices(
            Offers=[CumulativePrice(Price=1.5, Level=1, Amount=3)],
            Targets=[CumulativePrice(Price=1.4, Level=1, Amount=5)],
            UpdatedAt=1000
        )
        assert len(cp.Offers) == 1
        assert cp.Targets[0].Amount == 5
