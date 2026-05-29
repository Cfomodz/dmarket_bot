# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install all dependencies (runtime + dev)
uv sync

# Run the bot
uv run python main.py

# Run unit tests (no credentials needed)
uv run pytest

# Run live read-only API tests (requires .env with real keys)
uv run pytest -m live

# Run a single test file
uv run pytest tests/test_api.py

# Run a single test by name
uv run pytest tests/test_api.py::TestGenerateHeaders::test_headers_contain_required_keys

# Lint
uv run ruff check .

# Format
uv run ruff format .
```

## Architecture

This is an async trading bot for the [DMarket](https://dmarket.com) marketplace. It runs several concurrent `asyncio` loops and requires `DMARKET_PUBLIC_KEY` / `DMARKET_SECRET_KEY` in a `.env` file.

### Entry point

`main.py` — starts `asyncio.gather(...)` over several independent loops: balance polling, order placement, skin database refresh, and offer management. Most loops are commented out; only `orders_loop` and `create_pre_base` run by default.

### Layers

- **`api/`** — DMarket HTTP client and data models
  - `dmarketapi.py`: `DMarketApi` class. All requests go through `api_call()` → `validate_response()`, which handles rate-limit headers. Auth is Ed25519 request signing via `generate_headers()`.
  - `schemas.py`: Pydantic v2 models for every API request/response type, plus internal bot models (`SkinHistory`, `SkinOrder`, `SellOffer`).
  - `exceptions.py`: Typed exceptions mapped from HTTP status codes. Note: exception constructors call `logger.error()` as a side effect — tests must account for this.

- **`db/`** — SQLite persistence via Peewee ORM
  - `database.py`: creates the `SqliteDatabase` instance
  - `models.py`: `Skin` (price history cache) and `SkinOffer` (purchased items awaiting sale). `JSONField` serialises Pydantic models.
  - `crud.py`: helper functions for the above models

- **`modules/`** — Trading logic
  - `skinbase.py`: `SkinBase` — fetches market data, filters items against `config.py` parameters, builds the local skin database
  - `orders.py`: `Orders` — compares current buy orders against the skin database, creates/cancels targets on DMarket
  - `offers.py`: `History` + `Offers` — tracks closed targets, lists purchased items for sale, adjusts prices

- **`config.py`** — All tunable parameters live here as class attributes (`BuyParams`, `SellParams`, `PrevParams`, `Timers`). `GAMES`, `BAD_ITEMS`, and API credentials are also here.

### Key data flow

1. `SkinBase.update()` pulls last-sale history for all items in each configured game, applies `BuyParams` filters, and stores passing items in the `Skin` table.
2. `Orders.update_orders()` reads `Skin`, fetches current DMarket buy orders, and creates/modifies `Target` objects via the API.
3. When a target closes (item purchased), `History.save_skins()` reads closed targets and writes a `SkinOffer` row.
4. `Offers.add_to_sell()` reads `SkinOffer`, creates sell offers at `BuyParams`-derived prices; `Offers.update_offers()` adjusts prices based on current market.

### Testing

Tests use `pytest-asyncio`. The `conftest.py` fixture `mock_bot` provides a `MagicMock(spec=DMarketApi)` with all async methods pre-stubbed. Helper factories (`make_market_offer`, `make_last_sales`, `make_skin_history`, etc.) live in `conftest.py`.

The test suite is unit-only — no live API calls, no database writes.
