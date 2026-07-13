from datetime import datetime

from peewee import DoesNotExist
from pydantic import ValidationError

from api.schemas import MarketOffer, SellOffer, SkinHistory
from config import logger
from db.models import Skin, SkinOffer, db

db.connect()
Skin.create_table()
SkinOffer.create_table()
db.close()


class SelectSkin:
    @staticmethod
    def _skin_history_from_model(skin: Skin):
        try:
            return SkinHistory(
                title=skin.title,
                game=skin.game,
                sales=skin.LastSales,
                LastSales=skin.LastSales,
                avg_price=skin.avg_price,
                update_time=skin.update_time,
            )
        except ValidationError as e:
            logger.error(f"Deleting corrupted skin row {skin.title}: {e}")
            skin.delete_instance()
            return None

    @staticmethod
    def create_all_skins(items: list[SkinHistory]):
        for i in items:
            try:
                skin = Skin(
                    title=i.title,
                    game=i.game,
                    LastSales=i.sales,
                    avg_price=i.avg_price,
                    update_time=i.update_time,
                )
                skin.save()
            except Exception as e:
                logger.error(f"Failed to create skin from item {i.title}: {e}")

    @staticmethod
    def skin_existence(item: MarketOffer):
        skin = Skin.select().where(Skin.title == item.title)
        return bool(skin)

    @staticmethod
    def find_by_name(items: list[SkinHistory]):
        skins_to_update = list()
        skin_to_create = list()
        for item in items:
            try:
                skin = Skin.get(Skin.title == item.title)
                it = item.model_dump(mode="json")
                skin.avg_price = it["avg_price"]
                skin.LastSales = it["sales"]
                skin.update_time = it["update_time"]
                skins_to_update.append(skin)
            except DoesNotExist:
                skin_to_create.append(
                    Skin(
                        title=item.title,
                        game=item.game,
                        LastSales=item.sales,
                        avg_price=item.avg_price,
                        update_time=item.update_time,
                    )
                )
        with db.atomic():
            Skin.bulk_update(
                skins_to_update,
                fields=[Skin.avg_price, Skin.LastSales, Skin.update_time],
                batch_size=500,
            )
        with db.atomic():
            Skin.bulk_create(skin_to_create, batch_size=500)

    @staticmethod
    def select_all() -> list[SkinHistory]:
        skins = Skin.select()
        return [
            skin for skin in (SelectSkin._skin_history_from_model(skin) for skin in skins) if skin
        ]

    @staticmethod
    def select_update_time(now, delta) -> list[SkinHistory]:
        skins = Skin.select().where(Skin.update_time < datetime.fromtimestamp(now - delta))
        if skins:
            return [
                skin
                for skin in (SelectSkin._skin_history_from_model(skin) for skin in skins)
                if skin
            ]
        return []


class SelectSkinOffer:
    @staticmethod
    def create_skin(item: SellOffer) -> None:
        new_skin = SkinOffer.create(
            title=item.title,
            game=item.game,
            AssetID=item.AssetID,
            buyPrice=item.buyPrice,
            buyTime=item.buyTime,
            OfferID=item.OfferID,
            sellTime=item.sellTime,
            sellPrice=item.sellPrice,
        )
        new_skin.save()

    @staticmethod
    def update_sold(skins: list[SkinOffer]):
        with db.atomic():
            SkinOffer.bulk_update(
                skins,
                fields=[
                    SkinOffer.title,
                    SkinOffer.sellPrice,
                    SkinOffer.sellTime,
                    SkinOffer.OfferID,
                ],
            )

    @staticmethod
    def select_not_sell() -> list[SellOffer]:
        skins = SkinOffer.select().where(SkinOffer.sellTime == None)  # noqa: E711
        try:
            return [SellOffer.model_validate(s) for s in skins]
        except Exception as e:
            logger.error(f"Exception in select_not_sell: {e}")
            raise

    @staticmethod
    def select_all() -> list[SkinOffer]:
        return SkinOffer.select()

    @staticmethod
    def delete_all():
        skins = SkinOffer.select()
        for s in skins:
            s.delete_instance()

    @staticmethod
    def update_by_asset(skin: SellOffer):
        try:
            item = SkinOffer.get(SkinOffer.AssetID == skin.AssetID)
            item.OfferID = skin.OfferID
            item.sellTime = skin.sellTime
            item.sellPrice = skin.sellPrice
            item.save()
        except DoesNotExist:
            pass

    @staticmethod
    def update_offer_id(skin: SellOffer):
        try:
            item = SkinOffer.get(SkinOffer.AssetID == skin.AssetID)
            item.OfferID = skin.OfferID
            item.title = skin.title
            item.fee = skin.fee
            item.sellPrice = skin.sellPrice
            item.save()
        except DoesNotExist:
            pass
