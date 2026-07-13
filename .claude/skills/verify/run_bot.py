"""Launch the real bot entrypoint against the local fake DMarket server."""

import os

os.environ["DMARKET_PUBLIC_KEY"] = "e2e_public"
os.environ["DMARKET_SECRET_KEY"] = "0" * 128
os.environ["DRY_RUN"] = "true"

import config  # noqa: E402

config.API_URL = "http://127.0.0.1:8787"
config.DATABASE_NAME = os.path.join(os.path.dirname(__file__), "e2e_skins.db")

import db.crud  # noqa: E402, F401  (creates tables at import)
from db.models import SkinOffer  # noqa: E402

# Seed one previously-bought, listed item so update_offers has work on its first pass
if not SkinOffer.select().where(SkinOffer.AssetID == "asset0").exists():
    SkinOffer.create(AssetID="asset0", title="Test Skin", buyPrice=120, OfferID="offer0", fee=7)

import main  # noqa: E402

main.main()
