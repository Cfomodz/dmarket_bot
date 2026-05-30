<div align="center">
  
# dmarket_bot
![GitHub Sponsors](https://img.shields.io/github/sponsors/Cfomodz)
![Discord](https://img.shields.io/discord/425182625032962049)

<img src="https://github.com/user-attachments/assets/3c1f0f54-8ede-4d5d-9b4f-352f3b23da21" alt="dmarket bot icon" width="300"/>

Bot for automatic trading on dmarket 

</div>

## Quick Setup

Requirements: Python 3.10+, [uv](https://docs.astral.sh/uv/getting-started/installation/), DMarket API keys.

```bash
git clone https://github.com/Cfomodz/dmarket_bot.git
cd dmarket_bot
uv sync
cp .env.example .env   # then edit .env and add your keys
uv run python main.py
```

Set your API keys in `.env`:

```dotenv
DMARKET_PUBLIC_KEY=your_public_api_key_here
DMARKET_SECRET_KEY=your_secret_api_key_here
```

Run tests:

```bash
uv run pytest                  # unit tests (no credentials needed)
uv run pytest -m live          # read-only live API tests (requires .env)
```

## Features

- Supports all games available on DMarket (CS2, Dota 2, Rust, TF2)
- Automatic analysis of skins/items for each game
- Placing orders determined by 15 different parameters
- Automatic listing of purchased items for sale with dynamic price adjustment

## Configuration

All parameters are in `config.py`.

### Logger

```python
logger_config = {
    "handlers": [
        {"sink": sys.stderr, 'colorize': True, 'level': 'INFO'},
        {"sink": "log/info.log", "serialize": False, 'level': 'INFO'},
    ]
}
```

`'level'` accepts: `TRACE`, `DEBUG`, `INFO`, `SUCCESS`, `WARNING`, `ERROR`, `CRITICAL`.

### Bot parameters

- `GAMES` — list of games to trade. Available: `Games.CS`, `Games.DOTA`, `Games.RUST`, `Games.TF2`
- `PREV_BASE` — how often (seconds) to refresh the skin database
- `ORDERS_BASE` — how often (seconds) to refresh buy orders
- `BAD_ITEMS` — word blacklist; items whose names contain any of these words are skipped

### BuyParams — buy order placement

| Parameter | Default | Description |
|---|---|---|
| `STOP_ORDERS_BALANCE` | 500 | Stop placing orders when balance falls below this (cents) + minimum order price |
| `MIN_PRICE` / `MAX_PRICE` | 90 / 225 | Price range for orders (cents) |
| `PROFIT_PERCENT` | 15 | Minimum profit % required |
| `GOOD_POINTS_PERCENT` | 30 | Minimum % of sales that must exceed `PROFIT_PERCENT` |
| `AVG_PRICE_COUNT` | 7 | Number of recent sales used to compute average price |
| `ALL_SALES` | 80 | Minimum total sales count across all time |
| `DAYS_COUNT` / `SALE_COUNT` | 23 / 11 | At least `SALE_COUNT` sales in the last `DAYS_COUNT` days |
| `LAST_SALE` | 3 | Last sale must be within this many days |
| `FIRST_SALE` | 20 | First sale must be at least this many days ago |
| `MAX_COUNT_SELL_OFFERS` | 20 | Skip item if more than this many sell offers exist |
| `BOOST_PERCENT` / `BOOST_POINTS` | 24 / 3 | Remove outlier price points above `BOOST_PERCENT`% of average |
| `MAX_THRESHOLD` / `MIN_THRESHOLD` | 0.1 / 3 | Price adjustment bounds (%) relative to current best order |

### SellParams — sell offer placement

| Parameter | Default | Description |
|---|---|---|
| `MIN_PERCENT` | 7 | Minimum profit % on sale |
| `MAX_PERCENT` | 15 | Maximum profit % on sale |
