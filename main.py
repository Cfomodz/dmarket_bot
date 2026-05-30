import asyncio

from api.dmarketapi import DMarketApi
from config import PUBLIC_KEY, SECRET_KEY, logger, Timers, BuyParams
from modules.skinbase import SkinBase
from modules.orders import Orders
from modules.offers import History, Offers


bot = None
skin_base = None
orders = None
history = None
offers = None


async def create_pre_base():
    """Creating a primary database of items"""
    while True:
        logger.info('Skin database processing')
        try:
            await skin_base.update()
            await asyncio.sleep(skin_base.repeat)
        except Exception as e:
            logger.exception(f'Failed to update primary: {e}. Sleep for 5 seconds.')
            await asyncio.sleep(5)


async def orders_loop():
    await asyncio.sleep(5)
    while True:
        try:
            logger.debug(f'Balance: {bot.balance}')
            if bot.balance > orders.order_list.min_price + BuyParams.STOP_ORDERS_BALANCE:
                await orders.update_orders()
                await asyncio.sleep(Timers.ORDERS_BASE)
            else:
                targets = await orders.bot.user_targets(limit='1000')
                targets_inactive = await orders.bot.user_targets(limit='1000', status='TargetStatusInactive')
                await orders.bot.delete_target(targets.Items + targets_inactive.Items)
                logger.debug('Not enough balance to place orders, postponing')
                await asyncio.sleep(60 * 5)
        except Exception as e:
            logger.error(f'Failed to update orders: {e}. Sleep for 5 seconds.')
            await asyncio.sleep(5)


async def history_loop():
    while True:
        try:
            await history.save_skins()
            await asyncio.sleep(60 * 15)
        except Exception as e:
            logger.error(f'Failed to fetch history: {e}. Sleep for 30 seconds.')
            await asyncio.sleep(30)


async def add_to_sell_loop():
    while True:
        try:
            await offers.add_to_sell()
            await asyncio.sleep(60 * 10)
        except Exception as e:
            logger.error(f'Failed to list for sale: {e}. Sleep for 10 seconds.')
            await asyncio.sleep(10)


async def update_offers_loop():
    while True:
        try:
            await offers.update_offers()
            await asyncio.sleep(60 * 15)
        except Exception as e:
            logger.error(f'Failed to update offers: {e}. Sleep for 30 seconds.')
            await asyncio.sleep(30)


async def delete_offers_loop():
    while True:
        try:
            await asyncio.sleep(60 * 60 * 24 * 2)
            await offers.delete_all_offers()
        except Exception as e:
            logger.error(f'Failed to delete offers: {e}')
            await asyncio.sleep(30)


async def main_loop():
    global bot, skin_base, orders, history, offers

    bot = DMarketApi(PUBLIC_KEY, SECRET_KEY)
    skin_base = SkinBase(bot)
    orders = Orders(bot)
    history = History(bot)
    offers = Offers(bot)

    try:
        return await asyncio.gather(
            bot.get_money_loop(),
            # delete_offers_loop(),
            # history_loop(),
            orders_loop(),
            # add_to_sell_loop(),
            # update_offers_loop(),
            create_pre_base(),
            return_exceptions=True
        )
    finally:
        await bot.close()


def main():
    try:
        logger.info('The bot is launching')
        asyncio.run(main_loop())
    except KeyboardInterrupt:
        logger.info('The bot is shutting down')


if __name__ == '__main__':
    main()
