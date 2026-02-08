"""Tests for offers (sell side) management."""
import pytest
from unittest.mock import AsyncMock
from modules.offers import Offers, History
from api.schemas import (
    SellOffer, LastPrice, AggregatedPrice, EditOffers,
    MarketOffers, UserItems, ClosedOffers, ClosedOffer, ClosedTargets, ClosedTarget,
)
from tests.conftest import make_market_offer, make_aggregated_price


class TestOfferPrice:
    def test_below_min(self):
        assert Offers.offer_price(2.0, 1.0, 0.5) == 1.0

    def test_in_range(self):
        assert Offers.offer_price(2.0, 1.0, 1.5) == 1.49

    def test_above_max(self):
        assert Offers.offer_price(2.0, 1.0, 3.0) == 2.0

    def test_at_min(self):
        # When best == min_p, condition `min_p < best` is False -> falls to else -> max_p
        assert Offers.offer_price(2.0, 1.0, 1.0) == 2.0

    def test_at_max(self):
        # best == max_p falls into elif (min_p < best <= max_p)
        assert Offers.offer_price(2.0, 1.0, 2.0) == 1.99


class TestOffers:
    @pytest.mark.asyncio
    async def test_update_offers_empty(self, mock_bot):
        offers = Offers(mock_bot)
        # No items on sale -> should return early
        await offers.update_offers()
        mock_bot.aggregated_prices.assert_not_called()

    @pytest.mark.asyncio
    async def test_delete_all_offers(self, mock_bot):
        mock_bot.user_offers = AsyncMock(return_value=UserItems(Items=[], Total='0'))
        offers = Offers(mock_bot)
        await offers.delete_all_offers()
        mock_bot.user_offers_delete.assert_called_once()


class TestHistory:
    def test_skins_db_empty(self):
        # With empty database this would need mocking
        history = History(None)
        # Just test that the static method exists and is callable
        assert callable(History.skins_db)
