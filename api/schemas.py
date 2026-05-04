import enum
from datetime import datetime
from typing import List, Optional, Union
from pydantic import BaseModel, ConfigDict, Field


class Games(enum.Enum):
    CS = 'a8db'
    DOTA = '9a92'
    RUST = 'rust'
    TF2 = 'tf2'


class Balance(BaseModel):
    usd: int


class LastPrice(BaseModel):
    Currency: str
    Amount: float


class LastSale(BaseModel):
    date: datetime
    price: str


class LastSales(BaseModel):
    sales: List[LastSale]


class MarketOfferPrice(BaseModel):
    DMC: Union[int, str] = 0
    USD: Union[int, str] = 0


class MarketOfferExtra(BaseModel):
    categoryPath: Optional[str] = None
    name: Optional[str] = None
    title: Optional[str] = None
    category: Optional[str] = None
    gameId: Optional[Games] = None
    groupId: Optional[int] = None
    tradeLock: Optional[int] = None
    rarity: Optional[str] = None
    exterior: Optional[str] = None
    type: Optional[str] = None
    stickers: Optional[list] = None


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
    cursor: Optional[str] = None
    objects: List[MarketOffer]


# --- Aggregated Prices (POST /marketplace-api/v1/aggregated-prices) ---

class AggregatedPriceFilter(BaseModel):
    game: str
    titles: List[str]


class AggregatedPricesRequest(BaseModel):
    cursor: Optional[str] = None
    limit: int = 100
    filter: AggregatedPriceFilter


class AggregatedPrice(BaseModel):
    title: str
    orderBestPrice: Optional[float] = 0
    orderCount: Optional[int] = 0
    offerBestPrice: Optional[float] = 0
    offerCount: Optional[int] = 0


class AggregatedPricesResponse(BaseModel):
    aggregatedPrices: List[AggregatedPrice]
    nextCursor: Optional[str] = None


# --- Targets (Buy Orders) ---

class TargetAttributes(BaseModel):
    Name: Optional[str] = None
    Value: Optional[str] = None


class Target(BaseModel):
    TargetID: str
    Title: str
    Amount: str
    Status: str
    GameID: Games
    GameType: Optional[str] = None
    Attributes: List[TargetAttributes]
    Price: LastPrice


class UserTargets(BaseModel):
    Items: List[Target]
    Total: int
    Cursor: str


class ClosedTarget(BaseModel):
    OfferID: str
    TargetID: str
    AssetID: str
    Price: LastPrice
    Amount: int


class ClosedTargets(BaseModel):
    Trades: List[ClosedTarget]
    Total: int


class CreateTarget(BaseModel):
    Amount: str
    Price: LastPrice
    Title: str
    Attrs: Optional[List[TargetAttributes]] = None


class CreateTargets(BaseModel):
    GameID: str
    Targets: List[CreateTarget]


# --- User Items / Inventory ---

class Offer(BaseModel):
    OfferID: str
    Price: LastPrice
    Fee: Optional[LastPrice] = None
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
    Attributes: List[TargetAttributes]
    Offer: Offer
    Fee: Optional[LastPrice] = None
    MarketPrice: Optional[LastPrice] = None
    ClassID: str


class ClosedOffers(BaseModel):
    Trades: List[ClosedOffer]
    Total: str
    Cursor: Optional[str] = None


class UserItems(BaseModel):
    Items: List[UserItem]
    Total: str
    Cursor: Optional[str] = None


# --- Create / Edit / Delete Offers ---

class CreateOffer(BaseModel):
    AssetID: str
    Price: LastPrice


class EditOffer(CreateOffer):
    OfferID: str


class CreateOffers(BaseModel):
    Offers: List[CreateOffer]


class CreateOfferResponse(BaseModel):
    CreateOffer: CreateOffer
    OfferID: str
    Successful: bool


class CreateOffersResponse(BaseModel):
    Result: List[CreateOfferResponse]


class EditOffers(BaseModel):
    Offers: List[EditOffer]


class EditOfferResponse(BaseModel):
    EditOffer: CreateOffer
    Successful: bool
    NewOfferID: str


class EditOffersResponse(BaseModel):
    Result: List[EditOfferResponse]


class DeleteOffer(BaseModel):
    itemId: str
    offerId: str
    price: LastPrice


class DeleteOffers(BaseModel):
    force: bool = True
    objects: List[DeleteOffer]


# --- Internal bot models ---

class SkinHistory(LastSales):
    game: str
    title: str
    sales: List[LastSale]
    avg_price: float
    update_time: datetime


class SkinOrder(BaseModel):
    title: str
    game: Games
    bestOrder: Optional[int] = None
    maxPrice: Optional[int] = None
    minPrice: Optional[int] = None
    targetId: Optional[str] = None


class SellOffer(BaseModel):
    AssetID: str
    title: Optional[str] = None
    game: Optional[str] = None
    OfferID: Optional[str] = None
    sellTime: Optional[datetime] = None
    buyPrice: Optional[float] = None
    sellPrice: Optional[float] = None
    buyTime: datetime = Field(default_factory=datetime.now)
    fee: int = 7

    model_config = ConfigDict(from_attributes=True)


# --- Cumulative Prices ---

class CumulativePrice(BaseModel):
    Price: float
    Level: int
    Amount: int


class CumulativePrices(BaseModel):
    Offers: List[CumulativePrice]
    Targets: List[CumulativePrice]
    UpdatedAt: int
