from api.dmarketapi import DMarketApi
from api.schemas import (
    CreateOffer,
    CreateOffers,
    DeleteOffer,
    DeleteOffers,
    EditOffer,
    EditOffers,
    LastPrice,
    SellOffer,
)
from config import GAMES, SellParams, logger
from db.crud import SelectSkinOffer, SkinOffer


class History:
    def __init__(self, bot: DMarketApi):
        self.bot = bot

    @staticmethod
    def skins_db() -> list[SkinOffer]:
        skins = SelectSkinOffer.select_all()
        if skins:
            return [i for i in skins if not i.sellTime]
        return list()

    async def save_skins(self):
        logger.debug("Save skins")
        buy = await self.bot.closed_targets(limit="100")
        logger.debug(f"Buys: {len(buy.Trades)}")
        buy = buy.Trades
        buy = [
            SellOffer(
                OfferID=i.OfferID,
                TargetID=i.TargetID,
                AssetID=i.AssetID,
                buyPrice=i.Price.amount_cents,
                Amount=i.Amount,
            )
            for i in buy
        ]
        sold = []
        for game in GAMES:
            sell = await self.bot.user_offers_closed(game=game, limit="100")
            sold += sell.Trades
        sell = [
            SellOffer(
                AssetID=i.AssetID,
                OfferID=i.OfferID,
                sellPrice=i.Price.amount_cents,
                sellTime=i.OfferClosedAt,
                title=i.Title,
                game="rust",
            )
            for i in sold
        ]
        buy_asset_ids = [s.AssetID for s in SelectSkinOffer.select_all()]
        for b in buy:
            if b.AssetID not in buy_asset_ids:
                SelectSkinOffer.create_skin(b)
        skins = self.skins_db()

        for s in skins:
            for i in sell:
                if s.AssetID == i.AssetID:
                    s.title = i.title
                    s.sellPrice = i.sellPrice * (1 - s.fee / 100)
                    s.OfferID = i.OfferID
                    s.sellTime = i.sellTime
                    s.game = i.game
                    break
        SelectSkinOffer.update_sold(skins)


class Offers:
    def __init__(self, bot: DMarketApi):
        self.bot = bot
        self.max_percent = SellParams.MAX_PERCENT
        self.min_percent = SellParams.MIN_PERCENT

    async def add_to_sell(self):
        logger.debug("Add to sell")
        skins = SelectSkinOffer.select_not_sell()
        inv_skins = []
        invent = []
        for game in GAMES:
            inv = await self.bot.user_items(game=game)
            inv_skins += inv.objects
        for i in inv_skins:
            fee = 7
            if "custom" in i.fees["dmarket"]["sell"]:
                fee = int(i.fees["dmarket"]["sell"]["custom"]["percentage"])
            if i.inMarket:
                invent.append(SellOffer(AssetID=i.itemId, title=i.title, game=i.gameId, fee=fee))
        logger.debug(f"Invent: {len(invent)}")
        create_offers = []
        for i in invent:
            for j in skins:
                if i.AssetID == j.AssetID and j.buyPrice is not None:
                    i.sellPrice = j.buyPrice * (1 + self.max_percent / 100 + i.fee / 100)
            if i.sellPrice is None or i.sellPrice < 5:  # never list below 5 cents
                continue
            create_offers.append(
                CreateOffer(AssetID=i.AssetID, Price=LastPrice.from_cents(i.sellPrice))
            )

        add = await self.bot.user_offers_create(CreateOffers(Offers=create_offers))
        if add.Result:
            for i in add.Result:
                for j in invent:
                    if i.CreateOffer.AssetID == j.AssetID:
                        j.sellPrice = i.CreateOffer.Price.amount_cents
                        j.OfferID = i.OfferID
                        SelectSkinOffer.update_offer_id(j)
        logger.debug(f"Add to sell: {add}")

    @staticmethod
    def offer_price(max_p, min_p, best) -> float:
        """All arguments and the result are cents; undercut the best offer by one cent."""
        if best < min_p:
            return min_p
        elif min_p < best <= max_p:
            return best - 1
        else:
            return max_p

    async def update_offers(self):
        logger.debug("Update offers")
        on_sale = sorted(
            [i for i in SelectSkinOffer.select_not_sell() if i.OfferID], key=lambda x: x.title
        )
        logger.debug(f"On sale: {len(on_sale)}")
        names = [i.title for i in on_sale if i.title]
        if not names:
            return
        aggregated = await self.bot.aggregated_prices(names=names)
        agr_by_title = {a.title: a for a in aggregated}

        items_to_update = list()
        for i in on_sale:
            if not i.title or i.title not in agr_by_title or i.buyPrice is None:
                continue
            best_price = agr_by_title[i.title].offer_best_price_cents
            max_sell_price = i.buyPrice * (1 + self.max_percent / 100 + i.fee / 100)
            min_sell_price = i.buyPrice * (1 + self.min_percent / 100 + i.fee / 100)
            price = self.offer_price(max_sell_price, min_sell_price, best_price)
            if i.sellPrice is None or round(price) != round(i.sellPrice):
                i.sellPrice = price
                items_to_update.append(
                    EditOffer(
                        OfferID=i.OfferID,
                        AssetID=i.AssetID,
                        Price=LastPrice.from_cents(i.sellPrice),
                    )
                )

        if not items_to_update:
            return
        updated = await self.bot.user_offers_edit(EditOffers(Offers=items_to_update))
        for i in updated.Result:
            for j in on_sale:
                if i.EditOffer.AssetID == j.AssetID:
                    j.sellPrice = i.EditOffer.Price.amount_cents
                    j.OfferID = i.NewOfferID
                    SelectSkinOffer.update_offer_id(j)
        logger.debug(f"UPDATE OFFERS: {updated}")

    async def delete_all_offers(self):
        offers = await self.bot.user_offers(status="OfferStatusActive")
        do = [
            DeleteOffer(itemId=o.AssetID, offerId=o.Offer.OfferID, price=o.Offer.Price)
            for o in offers.Items
        ]
        await self.bot.user_offers_delete(DeleteOffers(objects=do))
