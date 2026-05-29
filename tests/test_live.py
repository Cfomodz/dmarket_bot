"""Read-only live API tests — require real DMarket credentials.

Run with:  uv run pytest -m live
Skipped automatically when credentials are the dummy values set by conftest.py.
"""

import os

import pytest

from api.dmarketapi import DMarketApi
from api.schemas import Games, LastSales, MarketOffers

_DUMMY_KEY = "test_public_key"


def _real_creds() -> tuple[str, str] | None:
    pub = os.environ.get("DMARKET_PUBLIC_KEY", "")
    sec = os.environ.get("DMARKET_SECRET_KEY", "")
    if pub == _DUMMY_KEY or not pub or not sec:
        return None
    return pub, sec


@pytest.fixture
def live_bot():
    creds = _real_creds()
    if creds is None:
        pytest.skip(
            "No real DMarket credentials found — set DMARKET_PUBLIC_KEY and DMARKET_SECRET_KEY"
        )
    pub, sec = creds
    return DMarketApi(pub, sec)


@pytest.mark.live
async def test_get_balance(live_bot):
    balance = await live_bot.get_balance()
    await live_bot.close()
    assert isinstance(balance, int)
    assert balance >= 0


@pytest.mark.live
async def test_market_offers_returns_data(live_bot):
    result = await live_bot.market_offers(game=Games.RUST, limit=5)
    await live_bot.close()
    assert isinstance(result, MarketOffers)
    # DMarket always has Rust items; if the market is empty something is wrong
    assert len(result.objects) > 0


@pytest.mark.live
async def test_last_sales_common_item(live_bot):
    # "Wood" is one of the most common Rust items and should always have sales
    result = await live_bot.last_sales("Wood", game=Games.RUST)
    await live_bot.close()
    assert isinstance(result, LastSales)
    assert len(result.sales) > 0
