"""Minimal fake DMarket API server for end-to-end dry-run verification."""

from datetime import datetime, timedelta

from aiohttp import web

RL = {"RateLimit-Remaining": "100", "RateLimit-Reset": "10"}

state = {"last_sales_calls": 0, "requests": []}


def offer(item_id, title, usd_cents):
    return {
        "itemId": item_id,
        "type": "dmarket",
        "amount": 1,
        "image": "img.png",
        "classId": "cls-" + item_id,
        "gameId": "rust",
        "inMarket": True,
        "lockStatus": False,
        "title": title,
        "slug": title.lower().replace(" ", "-"),
        "status": "active",
        "discount": 0,
        "price": {"DMC": "0", "USD": str(usd_cents)},
        "suggestedPrice": {"DMC": "0", "USD": str(usd_cents)},
        "extra": {
            "categoryPath": "misc",
            "name": title,
            "title": title,
            "category": "misc",
            "gameId": "rust",
        },
        "fees": {"dmarket": {"sell": {"custom": {"percentage": "5"}}}},
    }


ITEMS = [offer("asset0", "Test Skin", 150), offer("assetB", "Another Skin", 200)]


def track(request):
    state["requests"].append(f"{request.method} {request.path}")


async def market_items(request):
    track(request)
    title = request.query.get("title", "")
    objects = [o for o in ITEMS if o["title"] == title] if title else ITEMS
    return web.json_response({"cursor": "", "objects": objects}, headers=RL)


async def last_sales(request):
    track(request)
    state["last_sales_calls"] += 1
    if state["last_sales_calls"] == 1:
        # First call gets rate-limited to exercise the client's 429 retry
        return web.json_response(
            {"error": "too many"},
            status=429,
            headers={"RateLimit-Remaining": "0", "RateLimit-Reset": "1"},
        )
    now = datetime.now()
    price = "1.50" if request.query.get("title") == "Test Skin" else "2.00"
    sales = [
        {"date": (now - timedelta(hours=1 + i * 26)).isoformat(), "price": price} for i in range(20)
    ]
    return web.json_response({"sales": sales}, headers=RL)


async def balance(request):
    track(request)
    # Deliberately no RateLimit headers: old code stalled 5s on every such response
    return web.json_response({"usd": 5000})


async def user_targets(request):
    track(request)
    return web.json_response({"Items": [], "Total": 0, "Cursor": ""}, headers=RL)


async def closed_targets(request):
    track(request)
    return web.json_response(
        {
            "Trades": [
                {
                    "OfferID": "offer1",
                    "TargetID": "t1",
                    "AssetID": "asset1",
                    "Price": {"Currency": "USD", "Amount": 1.2},
                    "Amount": 1,
                }
            ],
            "Total": 1,
        },
        headers=RL,
    )


async def aggregated_prices(request):
    track(request)
    body = await request.json()
    prices = [
        {
            "title": t,
            "orderBestPrice": 1.4,
            "orderCount": 3,
            "offerBestPrice": 1.5,
            "offerCount": 5,
        }
        for t in body["filter"]["titles"]
    ]
    return web.json_response({"aggregatedPrices": prices, "nextCursor": None}, headers=RL)


async def cumulative(request):
    track(request)
    return web.json_response(
        {
            "Offers": [{"Price": 1.8, "Level": 1, "Amount": 3}],
            "Targets": [{"Price": 1.2, "Level": 1, "Amount": 3}],
            "UpdatedAt": 0,
        },
        headers=RL,
    )


async def offers_by_title(request):
    track(request)
    return web.json_response(
        {"cursor": "", "objects": [offer("comp1", request.query.get("Title", ""), 180)]},
        headers=RL,
    )


async def user_items(request):
    track(request)
    return web.json_response({"cursor": "", "objects": ITEMS[:1]}, headers=RL)


async def user_offers_closed(request):
    track(request)
    return web.json_response({"Trades": [], "Total": "0", "Cursor": None}, headers=RL)


async def mutation_guard(request):
    # DRY_RUN must prevent any mutating call from ever reaching the server
    track(request)
    state["requests"].append(f"!!! MUTATION HIT: {request.method} {request.path}")
    return web.json_response({"Result": []}, headers=RL)


async def dump_state(request):
    return web.json_response(state)


app = web.Application()
app.router.add_get("/exchange/v1/market/items", market_items)
app.router.add_get("/trade-aggregator/v1/last-sales", last_sales)
app.router.add_get("/account/v1/balance", balance)
app.router.add_get("/marketplace-api/v1/user-targets", user_targets)
app.router.add_get("/marketplace-api/v1/user-targets/closed", closed_targets)
app.router.add_post("/marketplace-api/v1/aggregated-prices", aggregated_prices)
app.router.add_get("/marketplace-api/v1/cumulative-price-levels", cumulative)
app.router.add_get("/exchange/v1/offers-by-title", offers_by_title)
app.router.add_get("/exchange/v1/user/items", user_items)
app.router.add_get("/marketplace-api/v1/user-offers/closed", user_offers_closed)
app.router.add_post("/marketplace-api/v1/user-targets/create", mutation_guard)
app.router.add_post("/marketplace-api/v1/user-targets/delete", mutation_guard)
app.router.add_post("/marketplace-api/v1/user-offers/create", mutation_guard)
app.router.add_post("/marketplace-api/v1/user-offers/edit", mutation_guard)
app.router.add_delete("/exchange/v1/offers", mutation_guard)
app.router.add_get("/__state", dump_state)

if __name__ == "__main__":
    web.run_app(app, host="127.0.0.1", port=8787, print=None)
