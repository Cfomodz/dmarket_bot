"""Tests for the cents-based money conversion layer in api/schemas.py."""

from datetime import datetime

from api.schemas import (
    AggregatedPrice,
    CumulativePrice,
    LastPrice,
    LastSale,
    MarketOfferPrice,
    dollars_to_cents,
    parse_money_cents,
)


class TestDollarsToCents:
    def test_float_dollars(self):
        assert dollars_to_cents(1.5) == 150

    def test_string_dollars(self):
        assert dollars_to_cents("2.09") == 209

    def test_none(self):
        assert dollars_to_cents(None) == 0

    def test_rounding(self):
        # 1.005 * 100 = 100.49999... in binary floats; round() handles it
        assert dollars_to_cents(0.07) == 7


class TestParseMoneyCents:
    def test_dollar_string(self):
        assert parse_money_cents("1.50") == 150

    def test_cents_string(self):
        assert parse_money_cents("150") == 150

    def test_comma_decimal(self):
        assert parse_money_cents("1,50") == 150

    def test_currency_symbols_stripped(self):
        assert parse_money_cents("$1.50") == 150

    def test_empty_string(self):
        assert parse_money_cents("") == 0

    def test_none(self):
        assert parse_money_cents(None) == 0

    def test_int(self):
        assert parse_money_cents(150) == 150

    def test_fractional_float_is_dollars(self):
        assert parse_money_cents(1.5) == 150


class TestModelAccessors:
    def test_last_price_amount_cents(self):
        assert LastPrice(Currency="USD", Amount=2.09).amount_cents == 209

    def test_last_price_from_cents_round_trip(self):
        price = LastPrice.from_cents(209)
        assert price.Amount == 2.09
        assert price.amount_cents == 209

    def test_last_price_from_cents_rounds_fractional_cents(self):
        assert LastPrice.from_cents(149.6).amount_cents == 150

    def test_last_sale_price_cents(self):
        sale = LastSale(date=datetime.now(), price="1.50")
        assert sale.price_cents == 150

    def test_market_offer_price_cent_string(self):
        assert MarketOfferPrice(DMC=0, USD="150").usd_cents == 150

    def test_market_offer_price_int(self):
        assert MarketOfferPrice(DMC=0, USD=150).usd_cents == 150

    def test_aggregated_price_cents(self):
        agr = AggregatedPrice(title="A", orderBestPrice=1.4, offerBestPrice=1.6)
        assert agr.order_best_price_cents == 140
        assert agr.offer_best_price_cents == 160

    def test_aggregated_price_none_defaults_to_zero(self):
        agr = AggregatedPrice(title="A", orderBestPrice=None, offerBestPrice=None)
        assert agr.order_best_price_cents == 0
        assert agr.offer_best_price_cents == 0

    def test_cumulative_price_cents(self):
        assert CumulativePrice(Price=1.5, Level=1, Amount=3).price_cents == 150
