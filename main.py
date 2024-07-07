import os
from aiogram import Bot, Dispatcher, types
import asyncio

from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.strategy import FSMStrategy
from dotenv import find_dotenv, load_dotenv

from middlewares.db import DataBaseSession

load_dotenv(find_dotenv())

from aiogram.enums import ParseMode
from database.engine import create_db, drop_db, session_marker
from Hand.user_private import user_private_router
from common.bot_cmds_list import private
from Hand.user_group import user_group_router
from Hand.admin_private import admin_router

#ALLOWED_UPDATES = ['message, edited_message', 'callback_query']

bot = Bot(token=os.getenv('TELEGRAM_TOKEN'), default=DefaultBotProperties(parse_mode=ParseMode.HTML))
bot.my_admins_list = []

dp = Dispatcher()

#admin_router.message.outer_middleware(CounterMiddleware())

dp.include_router(user_group_router)
dp.include_router(user_private_router)
dp.include_router(admin_router)


async def on_startup(bot):
    run_param = False
    if run_param:
        await drop_db()
    await create_db()


async def on_shutdown(bot):
    print("бот лег")


async def main():
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    dp.update.middleware(DataBaseSession(session_pool=session_marker))
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_my_commands(commands=private, scope=types.BotCommandScopeAllPrivateChats())
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


asyncio.run(main())
