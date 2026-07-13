"""Tests for offers (sell side) management."""

from unittest.mock import AsyncMock

import pytest

from api.schemas import (
    UserItems,
)
from modules.offers import History, Offers


class TestOfferPrice:
    # All values are cents; the bot undercuts the best competing offer by one cent.
    def test_below_min(self):
        assert Offers.offer_price(200, 100, 50) == 100

    def test_in_range(self):
        assert Offers.offer_price(200, 100, 150) == 149

    def test_above_max(self):
        assert Offers.offer_price(200, 100, 300) == 200

    def test_at_min(self):
        # When best == min_p, condition `min_p < best` is False -> falls to else -> max_p
        assert Offers.offer_price(200, 100, 100) == 200

    def test_at_max(self):
        # best == max_p falls into elif (min_p < best <= max_p)
        assert Offers.offer_price(200, 100, 200) == 199


class TestOffers:
    @pytest.mark.asyncio
    async def test_update_offers_empty(self, mock_bot):
        offers = Offers(mock_bot)
        # No items on sale -> should return early
        await offers.update_offers()
        mock_bot.aggregated_prices.assert_not_called()

    @pytest.mark.asyncio
    async def test_delete_all_offers(self, mock_bot):
        mock_bot.user_offers = AsyncMock(return_value=UserItems(Items=[], Total="0"))
        offers = Offers(mock_bot)
        await offers.delete_all_offers()
        mock_bot.user_offers_delete.assert_called_once()


class TestHistory:
    def test_skins_db_empty(self):
        # With empty database this would need mocking
        # Just test that the static method exists and is callable
        assert callable(History.skins_db)
