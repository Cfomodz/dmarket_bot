import enum
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class Games(enum.Enum):
    CS = "a8db"
    DOTA = "9a92"
    RUST = "rust"
    TF2 = "tf2"


class Balance(BaseModel):
    usd: int


class LastPrice(BaseModel):
    Currency: str
    Amount: float


class LastSale(BaseModel):
    date: datetime
    price: str


class LastSales(BaseModel):
    sales: list[LastSale]


class MarketOfferPrice(BaseModel):
    DMC: int | str = 0
    USD: int | str = 0


class MarketOfferExtra(BaseModel):
    categoryPath: str | None = None
    name: str | None = None
    title: str | None = None
    category: str | None = None
    gameId: Games | None = None
    groupId: int | None = None
    tradeLock: int | None = None
    rarity: str | None = None
    exterior: str | None = None
    type: str | None = None
    stickers: list | None = None


class MarketOffer(BaseModel):
    itemId: str
    type: str
    amount: int
    image: str
    classId: str
    gameId: str
    inMarket: bool
    lockStatus: bool
    title: str
    slug: str
    status: str
    discount: int
    price: MarketOfferPrice
    suggestedPrice: MarketOfferPrice
    extra: MarketOfferExtra
    fees: dict


class MarketOffers(BaseModel):
    cursor: str | None = None
    objects: list[MarketOffer]


# --- Aggregated Prices (POST /marketplace-api/v1/aggregated-prices) ---


class AggregatedPriceFilter(BaseModel):
    game: str
    titles: list[str]


class AggregatedPricesRequest(BaseModel):
    cursor: str | None = None
    limit: int = 100
    filter: AggregatedPriceFilter


class AggregatedPrice(BaseModel):
    title: str
    orderBestPrice: float | None = 0
    orderCount: int | None = 0
    offerBestPrice: float | None = 0
    offerCount: int | None = 0


class AggregatedPricesResponse(BaseModel):
    aggregatedPrices: list[AggregatedPrice]
    nextCursor: str | None = None


# --- Targets (Buy Orders) ---


class TargetAttributes(BaseModel):
    Name: str | None = None
    Value: str | None = None


class Target(BaseModel):
    TargetID: str
    Title: str
    Amount: str
    Status: str
    GameID: Games
    GameType: str | None = None
    Attributes: list[TargetAttributes]
    Price: LastPrice


class UserTargets(BaseModel):
    Items: list[Target]
    Total: int
    Cursor: str


class ClosedTarget(BaseModel):
    OfferID: str
    TargetID: str
    AssetID: str
    Price: LastPrice
    Amount: int


class ClosedTargets(BaseModel):
    Trades: list[ClosedTarget]
    Total: int


class CreateTarget(BaseModel):
    Amount: str
    Price: LastPrice
    Title: str
    Attrs: list[TargetAttributes] | None = None


class CreateTargets(BaseModel):
    GameID: str
    Targets: list[CreateTarget]


# --- User Items / Inventory ---


class Offer(BaseModel):
    OfferID: str
    Price: LastPrice
    Fee: LastPrice | None = None
    CreatedDate: str


class ClosedOffer(BaseModel):
    OfferID: str
    TargetID: str
    AssetID: str
    Price: LastPrice
    Amount: int
    Title: str
    Fee: dict
    OfferCreatedAt: str
    OfferClosedAt: str


class UserItem(BaseModel):
    AssetID: str
    VariantID: str
    Title: str
    ImageURL: str
    GameID: str
    GameType: str
    Location: str
    Withdrawable: bool
    Depositable: bool
    Tradable: bool
    Attributes: list[TargetAttributes]
    Offer: Offer
    Fee: LastPrice | None = None
    MarketPrice: LastPrice | None = None
    ClassID: str


class ClosedOffers(BaseModel):
    Trades: list[ClosedOffer]
    Total: str
    Cursor: str | None = None


class UserItems(BaseModel):
    Items: list[UserItem]
    Total: str
    Cursor: str | None = None


# --- Create / Edit / Delete Offers ---


class CreateOffer(BaseModel):
    AssetID: str
    Price: LastPrice


class EditOffer(CreateOffer):
    OfferID: str


class CreateOffers(BaseModel):
    Offers: list[CreateOffer]


class CreateOfferResponse(BaseModel):
    CreateOffer: CreateOffer
    OfferID: str
    Successful: bool


class CreateOffersResponse(BaseModel):
    Result: list[CreateOfferResponse]


class EditOffers(BaseModel):
    Offers: list[EditOffer]


class EditOfferResponse(BaseModel):
    EditOffer: CreateOffer
    Successful: bool
    NewOfferID: str


class EditOffersResponse(BaseModel):
    Result: list[EditOfferResponse]


class DeleteOffer(BaseModel):
    itemId: str
    offerId: str
    price: LastPrice


class DeleteOffers(BaseModel):
    force: bool = True
    objects: list[DeleteOffer]


# --- Internal bot models ---


class SkinHistory(LastSales):
    game: str
    title: str
    sales: list[LastSale]
    avg_price: float
    update_time: datetime


class SkinOrder(BaseModel):
    title: str
    game: Games
    bestOrder: int | None = None
    maxPrice: int | None = None
    minPrice: int | None = None
    targetId: str | None = None


class SellOffer(BaseModel):
    AssetID: str
    title: str | None = None
    game: str | None = None
    OfferID: str | None = None
    sellTime: datetime | None = None
    buyPrice: float | None = None
    sellPrice: float | None = None
    buyTime: datetime = Field(default_factory=datetime.now)
    fee: int = 7

    model_config = ConfigDict(from_attributes=True)


# --- Cumulative Prices ---


class CumulativePrice(BaseModel):
    Price: float
    Level: int
    Amount: int


class CumulativePrices(BaseModel):
    Offers: list[CumulativePrice]
    Targets: list[CumulativePrice]
    UpdatedAt: int
