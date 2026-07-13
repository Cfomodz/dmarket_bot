---
name: verify
description: End-to-end verification recipe for the DMarket bot — run the real main.py against a local fake DMarket server in DRY_RUN mode and observe the full buy/track/sell pipeline without credentials or spend.
---

# Verifying the bot end-to-end

The bot's surface is `python main.py`: concurrent asyncio loops hitting the
DMarket HTTP API. Real credentials spend real money, so verification uses the
local fake server in this directory plus `DRY_RUN=true`.

## Recipe

```bash
SP=$(mktemp -d)
cp .claude/skills/verify/{fake_dmarket.py,run_bot.py} "$SP"

# 1. Start the fake DMarket API on 127.0.0.1:8787
uv run --project . python "$SP/fake_dmarket.py" > "$SP/server.log" 2>&1 &

# 2. Run the REAL entrypoint against it for ~25s (run_bot.py patches
#    config.API_URL and the DB path, seeds one purchased item, sets DRY_RUN)
timeout 25 env PYTHONPATH=$PWD uv run python "$SP/run_bot.py" > "$SP/bot.log" 2>&1

# 3. Observe
grep "DRY RUN" "$SP/bot.log"          # create_target / offers_create / offers_edit lines
grep -E "WARNING|ERROR" "$SP/bot.log" # should only show the deliberate 429 retry
curl -s --noproxy 127.0.0.1 http://127.0.0.1:8787/__state  # MUTATION HIT must be absent
```

## What a passing run shows

- Startup banner: "launching in DRY RUN … mode"
- `[DRY RUN] create_target` for both fake items, Price.Amount in dollars
  (internal cents / 100 — e.g. best target 120 cents → `1.2`)
- `[DRY RUN] user_offers_create` / `user_offers_edit` for the seeded item
- One "Retrying GET …/last-sales" warning (fake server 429s the first call)
- `__state` shows no `MUTATION HIT` entries — dry-run kept writes off the wire
- The Skin table has rows with `avg_price` in cents; SkinOffer gains `asset1`
  from the fake closed target with `buyPrice` in cents

## Gotchas

- All money is INTEGER CENTS internally; only wire formats use dollars.
  See the "Money conversion" section at the top of `api/schemas.py`.
- Tables are created when `db.crud` is imported — import it before touching models.
- `config.API_URL` / `config.DATABASE_NAME` must be patched after `import config`
  but before importing `api.dmarketapi` / `db.database` (they bind at import).
- Flip `DRY_RUN=false` in a copy of run_bot.py to prove mutations DO reach the
  fake server in live mode (they appear as `!!! MUTATION HIT` in `__state`).
