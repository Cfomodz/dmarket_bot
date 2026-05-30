"""Tests for order analytics and order management."""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock

import pytest

from api.schemas import (
    CreateTargets,
    CumulativePrice,
    CumulativePrices,
    Games,
    LastSale,
    MarketOffers,
    SkinOrder,
)
from modules.orders import OrderAnalytics, Orders, moving_average_5
from tests.conftest import make_aggregated_price, make_market_offer, make_skin_history, make_target


class TestMovingAverage:
    def test_basic_calculation(self):
        sales = [
            LastSale(date=datetime.now() - timedelta(days=i), price=str(float(i + 1)))
            for i in range(10)
        ]
        result = moving_average_5(sales)
        assert len(result) == 10
        # First 4 values should be NaN-like (from SMA with period 5)
        # Values from index 4 onward should be valid averages

    def test_minimum_prices(self):
        # SMA with period 5 requires at least 5 data points
        sales = [
            LastSale(date=datetime.now() - timedelta(days=i), price=str(float(i + 1)))
            for i in range(5)
        ]
        result = moving_average_5(sales)
        assert len(result) == 5


class TestOrderAnalytics:
    def test_first_second_offer_empty(self):
        best, second, count = OrderAnalytics.first_second_offer([])
        assert best == 0
        assert second == 0
        assert count == 0

    def test_first_second_offer_single(self):
        offers = [CumulativePrice(Price=1.5, Level=1, Amount=3)]
        best, second, count = OrderAnalytics.first_second_offer(offers)
        assert best == 1.5
        assert second == 1.5
        assert count == 1

    def test_first_second_offer_single_amount(self):
        offers = [
            CumulativePrice(Price=1.5, Level=1, Amount=1),
            CumulativePrice(Price=1.6, Level=2, Amount=5),
        ]
        best, second, count = OrderAnalytics.first_second_offer(offers)
        assert best == 1.5
        assert second == 1.6  # Amount=1 so second is next level
        assert count == 2

    def test_first_second_offer_multiple_amount(self):
        offers = [
            CumulativePrice(Price=1.5, Level=1, Amount=3),
            CumulativePrice(Price=1.6, Level=2, Amount=5),
        ]
        best, second, count = OrderAnalytics.first_second_offer(offers)
        assert best == 1.5
        assert second == 1.5  # Amount>1 so second=best
        assert count == 2


class TestOrders:
    def test_order_price_above_max(self):
        assert Orders.order_price(200, 100, 250) == 200

    def test_order_price_in_range(self):
        assert Orders.order_price(200, 100, 150) == 151

    def test_order_price_below_min(self):
        assert Orders.order_price(200, 100, 50) == 100

    def test_order_price_at_max(self):
        assert Orders.order_price(200, 100, 200) == 201  # best == max_p, so goes to else

    def test_order_price_at_min(self):
        assert Orders.order_price(200, 100, 100) == 100

    def test_sort_targets_empty(self):
        new, good, bad = Orders.sort_targets([], [])
        assert new == []
        assert good == []
        assert bad == []

    def test_sort_targets_all_new(self):
        skins = [SkinOrder(title="A", game=Games.RUST, bestOrder=100)]
        targets = []
        new, good, bad = Orders.sort_targets(skins, targets)
        assert len(new) == 1
        assert new[0].title == "A"

    def test_sort_targets_all_bad(self):
        skins = []
        targets = [make_target(title="B", target_id="t1")]
        new, good, bad = Orders.sort_targets(skins, targets)
        assert len(bad) == 1
        assert bad[0].Title == "B"

    def test_sort_targets_mixed(self):
        skins = [
            SkinOrder(title="A", game=Games.RUST, bestOrder=100),
            SkinOrder(title="B", game=Games.RUST, bestOrder=200),
        ]
        targets = [
            make_target(title="B", target_id="t1"),
            make_target(title="C", target_id="t2"),
        ]
        new, good, bad = Orders.sort_targets(skins, targets)
        assert len(new) == 1
        assert new[0].title == "A"
        assert len(good) == 1
        assert good[0].Title == "B"
        assert len(bad) == 1
        assert bad[0].Title == "C"

    @pytest.mark.asyncio
    async def test_check_offers_returns_true(self, mock_bot):
        mock_bot.offers_by_title = AsyncMock(
            return_value=MarketOffers(cursor=None, objects=[make_market_offer(price_usd=200)])
        )
        orders = Orders(mock_bot)
        skin = SkinOrder(title="Test", game=Games.RUST, bestOrder=100)
        result = await orders.check_offers(skin)
        assert result is True

    @pytest.mark.asyncio
    async def test_check_offers_returns_false(self, mock_bot):
        mock_bot.offers_by_title = AsyncMock(
            return_value=MarketOffers(cursor=None, objects=[make_market_offer(price_usd=50)])
        )
        orders = Orders(mock_bot)
        skin = SkinOrder(title="Test", game=Games.RUST, bestOrder=100)
        result = await orders.check_offers(skin)
        assert result is False

    @pytest.mark.asyncio
    async def test_create_order_with_valid_offer(self, mock_bot):
        offer = make_market_offer(title="Test Skin", game_id="rust", price_usd=150)
        mock_bot.market_offers = AsyncMock(return_value=MarketOffers(cursor=None, objects=[offer]))
        mock_bot.create_target = AsyncMock(return_value={"Result": []})

        orders = Orders(mock_bot)
        await orders.create_order(SkinOrder(title="Test Skin", game=Games.RUST, bestOrder=140))

        mock_bot.create_target.assert_called_once()
        call_body = mock_bot.create_target.call_args[0][0]
        assert isinstance(call_body, CreateTargets)
        assert call_body.GameID == "rust"
        assert call_body.Targets[0].Title == "Test Skin"

    @pytest.mark.asyncio
    async def test_create_order_no_matching_offer(self, mock_bot):
        mock_bot.market_offers = AsyncMock(return_value=MarketOffers(cursor=None, objects=[]))

        orders = Orders(mock_bot)
        result = await orders.create_order(SkinOrder(title="Test", game=Games.RUST, bestOrder=100))
        assert result == []
        mock_bot.create_target.assert_not_called()


class TestFrequencySkins:
    @pytest.mark.asyncio
    async def test_frequency_skins_uses_skin_sales(self, mock_bot):
        """frequency_skins should use skin.sales, not skin.LastSales."""
        skin = make_skin_history(title="Test Skin", game="rust", avg_price=150, count=20)
        agr = make_aggregated_price(title="Test Skin", order_best=1.40, offer_count=5)
        mock_bot.aggregated_prices = AsyncMock(return_value=[agr])

        analytics = OrderAnalytics(mock_bot)
        result = await analytics.frequency_skins([skin])
        # Should not raise AttributeError; result may be empty or contain items
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_frequency2_uses_skin_sales(self, mock_bot):
        """frequency2 should use skin.sales, not skin.LastSales."""
        skin = make_skin_history(title="Test Skin", game="rust", avg_price=150, count=20)
        mock_bot.cumulative_price = AsyncMock(
            return_value=CumulativePrices(
                Offers=[CumulativePrice(Price=1.6, Level=1, Amount=3)],
                Targets=[CumulativePrice(Price=1.4, Level=1, Amount=3)],
                UpdatedAt=0,
            )
        )

        analytics = OrderAnalytics(mock_bot)
        result = await analytics.frequency2([skin])
        # Should not raise AttributeError; result may be empty or contain items
        assert isinstance(result, list)
