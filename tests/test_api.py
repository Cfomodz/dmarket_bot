"""Tests for DMarketApi client."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from api.dmarketapi import DMarketApi
from api.exceptions import (
    BadAPIKeyException,
    BadGatewayError,
    BadRequestError,
    TooManyRequests,
    WrongResponseException,
)
from api.schemas import (
    AggregatedPrice,
    CreateOffers,
    CreateTarget,
    CreateTargets,
    DeleteOffers,
    EditOffers,
    Games,
    LastPrice,
    Target,
)


class TestGenerateHeaders:
    @pytest.mark.asyncio
    async def test_headers_contain_required_keys(self):
        api = DMarketApi("pub_key", "0" * 128)
        headers = api.generate_headers("GET", "/test/path")
        assert "X-Api-Key" in headers
        assert "X-Request-Sign" in headers
        assert "X-Sign-Date" in headers
        assert headers["X-Api-Key"] == "pub_key"
        await api.close()

    @pytest.mark.asyncio
    async def test_signature_starts_with_prefix(self):
        api = DMarketApi("pub_key", "0" * 128)
        headers = api.generate_headers("GET", "/test/path")
        assert headers["X-Request-Sign"].startswith("dmar ed25519 ")
        await api.close()

    @pytest.mark.asyncio
    async def test_body_included_in_signature(self):
        api = DMarketApi("pub_key", "0" * 128)
        headers_no_body = api.generate_headers("POST", "/test/path")
        headers_with_body = api.generate_headers("POST", "/test/path", body={"key": "val"})
        assert headers_no_body["X-Request-Sign"] != headers_with_body["X-Request-Sign"]
        await api.close()

    @pytest.mark.asyncio
    async def test_params_included_in_signature(self):
        api = DMarketApi("pub_key", "0" * 128)
        headers_no_params = api.generate_headers("GET", "/test/path")
        headers_with_params = api.generate_headers("GET", "/test/path", params={"q": "test"})
        assert headers_no_params["X-Request-Sign"] != headers_with_params["X-Request-Sign"]
        await api.close()


class TestCatchException:
    def test_400_raises_bad_request(self):
        with pytest.raises(BadRequestError):
            DMarketApi.catch_exception(400, {}, "")

    def test_500_raises_bad_gateway(self):
        with pytest.raises(BadGatewayError):
            DMarketApi.catch_exception(500, {}, "")

    def test_502_raises_bad_gateway(self):
        with pytest.raises(BadGatewayError):
            DMarketApi.catch_exception(502, {}, "")

    def test_429_raises_too_many_requests(self):
        with pytest.raises(TooManyRequests):
            DMarketApi.catch_exception(429, {}, "")

    def test_401_raises_bad_api_key(self):
        with pytest.raises(BadAPIKeyException):
            DMarketApi.catch_exception(401, {}, "")

    def test_non_json_error_raises_wrong_response(self):
        with pytest.raises(WrongResponseException):
            DMarketApi.catch_exception(403, {"content-type": "text/html"}, "error")

    def test_200_does_not_raise(self):
        DMarketApi.catch_exception(200, {"content-type": "application/json"}, "")

    def test_non_200_json_does_not_raise_wrong_response(self):
        # If content-type is JSON, WrongResponseException should NOT be raised
        DMarketApi.catch_exception(403, {"content-type": "application/json"}, "{}")


class TestAggregatedPricesEndpoint:
    """Verify aggregated_prices uses POST and correct path."""

    @pytest.mark.asyncio
    async def test_uses_post_method(self):
        api = DMarketApi("pub_key", "0" * 128)
        api.api_call = AsyncMock(
            return_value={
                "aggregatedPrices": [
                    {
                        "title": "Skin A",
                        "orderBestPrice": 1.5,
                        "orderCount": 3,
                        "offerBestPrice": 1.8,
                        "offerCount": 10,
                    }
                ],
                "nextCursor": None,
            }
        )

        await api.aggregated_prices(["Skin A"])

        api.api_call.assert_called_once()
        call_args = api.api_call.call_args
        url = call_args[0][0]
        method = call_args[0][1]
        assert method == "POST"
        assert "/marketplace-api/v1/aggregated-prices" in url

    @pytest.mark.asyncio
    async def test_sends_correct_body(self):
        api = DMarketApi("pub_key", "0" * 128)
        api.api_call = AsyncMock(return_value={"aggregatedPrices": [], "nextCursor": None})

        await api.aggregated_prices(["Skin A", "Skin B"], game="rust")

        call_args = api.api_call.call_args
        body = call_args[1]["body"]
        assert "filter" in body
        assert body["filter"]["game"] == "rust"
        assert body["filter"]["titles"] == ["Skin A", "Skin B"]

    @pytest.mark.asyncio
    async def test_batches_over_100(self):
        api = DMarketApi("pub_key", "0" * 128)
        api.api_call = AsyncMock(return_value={"aggregatedPrices": [], "nextCursor": None})

        names = [f"Skin {i}" for i in range(150)]
        await api.aggregated_prices(names)

        assert api.api_call.call_count == 2

    @pytest.mark.asyncio
    async def test_returns_aggregated_prices(self):
        api = DMarketApi("pub_key", "0" * 128)
        api.api_call = AsyncMock(
            return_value={
                "aggregatedPrices": [
                    {
                        "title": "A",
                        "orderBestPrice": 1.0,
                        "orderCount": 1,
                        "offerBestPrice": 2.0,
                        "offerCount": 5,
                    }
                ],
                "nextCursor": None,
            }
        )

        result = await api.aggregated_prices(["A"])
        assert len(result) == 1
        assert isinstance(result[0], AggregatedPrice)
        assert result[0].title == "A"


class TestDeleteTarget:
    @pytest.mark.asyncio
    async def test_batches_over_150(self):
        api = DMarketApi("pub_key", "0" * 128)
        api.api_call = AsyncMock(return_value={"Result": []})

        targets = [
            Target(
                TargetID=f"t{i}",
                Title="Test",
                Amount="1",
                Status="Active",
                GameID=Games.RUST,
                Attributes=[],
                Price=LastPrice(Currency="USD", Amount=1.0),
            )
            for i in range(200)
        ]

        await api.delete_target(targets)
        assert api.api_call.call_count == 2


class TestCreateTarget:
    @pytest.mark.asyncio
    async def test_sends_model_dump(self):
        api = DMarketApi("pub_key", "0" * 128)
        api.api_call = AsyncMock(return_value={"Result": []})

        body = CreateTargets(
            GameID="rust",
            Targets=[
                CreateTarget(
                    Amount="1", Price=LastPrice(Currency="USD", Amount=1.5), Title="Test Skin"
                )
            ],
        )
        await api.create_target(body)

        call_args = api.api_call.call_args
        sent_body = call_args[1]["body"]
        assert sent_body["GameID"] == "rust"
        assert sent_body["Targets"][0]["Title"] == "Test Skin"


class TestLastSalesEndpoint:
    @pytest.mark.asyncio
    async def test_uses_correct_path(self):
        api = DMarketApi("pub_key", "0" * 128)
        api.api_call = AsyncMock(return_value={"sales": []})

        await api.last_sales("Test Skin", Games.RUST)

        call_args = api.api_call.call_args
        url = call_args[0][0]
        assert "/trade-aggregator/v1/last-sales" in url


class TestDryRun:
    @pytest.mark.asyncio
    async def test_create_target_skips_api(self):
        api = DMarketApi("pub_key", "0" * 128, dry_run=True)
        api.api_call = AsyncMock()
        body = CreateTargets(
            GameID="rust",
            Targets=[
                CreateTarget(Amount="1", Price=LastPrice(Currency="USD", Amount=1.5), Title="T")
            ],
        )
        result = await api.create_target(body)
        api.api_call.assert_not_called()
        assert result == {"Result": []}
        await api.close()

    @pytest.mark.asyncio
    async def test_delete_target_skips_api(self):
        api = DMarketApi("pub_key", "0" * 128, dry_run=True)
        api.api_call = AsyncMock()
        target = Target(
            TargetID="t1",
            Title="T",
            Amount="1",
            Status="Active",
            GameID=Games.RUST,
            Attributes=[],
            Price=LastPrice(Currency="USD", Amount=1.0),
        )
        result = await api.delete_target([target])
        api.api_call.assert_not_called()
        assert result == []
        await api.close()

    @pytest.mark.asyncio
    async def test_offer_mutations_skip_api(self):
        api = DMarketApi("pub_key", "0" * 128, dry_run=True)
        api.api_call = AsyncMock()
        created = await api.user_offers_create(CreateOffers(Offers=[]))
        edited = await api.user_offers_edit(EditOffers(Offers=[]))
        deleted = await api.user_offers_delete(DeleteOffers(objects=[]))
        api.api_call.assert_not_called()
        assert created.Result == []
        assert edited.Result == []
        assert deleted == {}
        await api.close()

    @pytest.mark.asyncio
    async def test_disabled_by_default(self):
        api = DMarketApi("pub_key", "0" * 128)
        assert api.dry_run is False
        await api.close()


class TestRetries:
    @pytest.mark.asyncio
    async def test_retries_on_429_then_succeeds(self):
        api = DMarketApi("pub_key", "0" * 128)
        api.RETRY_BACKOFF = 0
        api._request = AsyncMock(side_effect=[TooManyRequests(), {"ok": True}])
        result = await api.api_call("http://test.com", "GET", {})
        assert result == {"ok": True}
        assert api._request.call_count == 2
        await api.close()

    @pytest.mark.asyncio
    async def test_raises_after_max_retries(self):
        api = DMarketApi("pub_key", "0" * 128)
        api.RETRY_BACKOFF = 0
        api._request = AsyncMock(side_effect=BadGatewayError())
        with pytest.raises(BadGatewayError):
            await api.api_call("http://test.com", "GET", {})
        assert api._request.call_count == api.MAX_RETRIES + 1
        await api.close()

    @pytest.mark.asyncio
    async def test_no_retry_on_bad_request(self):
        api = DMarketApi("pub_key", "0" * 128)
        api.RETRY_BACKOFF = 0
        api._request = AsyncMock(side_effect=BadRequestError())
        with pytest.raises(BadRequestError):
            await api.api_call("http://test.com", "GET", {})
        assert api._request.call_count == 1
        await api.close()


class TestRateLimitSleep:
    @pytest.mark.asyncio
    async def test_no_sleep_when_remaining_high(self, monkeypatch):
        api = DMarketApi("pub_key", "0" * 128)
        sleeps = []

        async def fake_sleep(s):
            sleeps.append(s)

        monkeypatch.setattr("api.dmarketapi.asyncio.sleep", fake_sleep)
        await api._rate_limit_sleep({"RateLimit-Remaining": "50", "RateLimit-Reset": "10"})
        assert sleeps == []
        await api.close()

    @pytest.mark.asyncio
    async def test_sleep_clamped_for_epoch_timestamps(self, monkeypatch):
        api = DMarketApi("pub_key", "0" * 128)
        sleeps = []

        async def fake_sleep(s):
            sleeps.append(s)

        monkeypatch.setattr("api.dmarketapi.asyncio.sleep", fake_sleep)
        # An epoch timestamp far in the future must not cause a decades-long sleep
        await api._rate_limit_sleep({"RateLimit-Remaining": "0", "RateLimit-Reset": "99999999999"})
        assert sleeps and sleeps[0] <= api.MAX_RATE_LIMIT_SLEEP
        await api.close()

    @pytest.mark.asyncio
    async def test_missing_header_does_not_sleep(self, monkeypatch):
        api = DMarketApi("pub_key", "0" * 128)
        sleeps = []

        async def fake_sleep(s):
            sleeps.append(s)

        monkeypatch.setattr("api.dmarketapi.asyncio.sleep", fake_sleep)
        await api._rate_limit_sleep({})
        assert sleeps == []
        await api.close()


class TestApiCallRouting:
    @pytest.mark.asyncio
    async def test_get_uses_session_get(self):
        api = DMarketApi("pub_key", "0" * 128)
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.headers = {"content-type": "application/json", "RateLimit-Remaining": "10"}
        mock_response.text = AsyncMock(return_value="{}")
        mock_response.json = AsyncMock(return_value={})

        mock_cm = AsyncMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_response)
        mock_cm.__aexit__ = AsyncMock(return_value=False)
        api.session.get = MagicMock(return_value=mock_cm)

        await api.api_call("http://test.com", "GET", {})
        api.session.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_post_uses_session_post(self):
        api = DMarketApi("pub_key", "0" * 128)
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.headers = {"content-type": "application/json", "RateLimit-Remaining": "10"}
        mock_response.text = AsyncMock(return_value="{}")
        mock_response.json = AsyncMock(return_value={})

        mock_cm = AsyncMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_response)
        mock_cm.__aexit__ = AsyncMock(return_value=False)
        api.session.post = MagicMock(return_value=mock_cm)

        await api.api_call("http://test.com", "POST", {}, body={"key": "val"})
        api.session.post.assert_called_once()
