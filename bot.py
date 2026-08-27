"""
Telegram Ботни ишга тушириш асосий файли (Main Entry Point).
"""

import asyncio
import logging
import sys

# Windows консолида UTF-8 белгиларини тўғри кўрсатиш ва хатосиз ишлаш учун
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

from config import settings
from handlers import main_router

# Логларни созлаш
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


async def set_main_menu_commands(bot: Bot):
    """Телеграм ботнинг пастки буйруқлар менюсини созлаш."""
    commands = [
        BotCommand(command="start", description="Ботни ишга тушириш / Бош меню"),
        BotCommand(command="help", description="Қўлланма ва маълумот"),
        BotCommand(command="cancel", description="Ҳисоблашни бекор қилиш"),
    ]
    await bot.set_my_commands(commands)


async def main():
    """Ботни ишга туширувчи асосий асинхрон функция."""
    token = settings.bot_token
    if not token or token == "YOUR_BOT_TOKEN_HERE":
        logger.warning(
            "\n"
            "============================================================\n"
            "⚠️  ДИҚҚАТ! BOT_TOKEN ҳали кўрсатилмаган!\n"
            "1. .env файлини яратинг ёки очинг.\n"
            "2. BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ кўринишида киритинг.\n"
            "   (Токенни Telegram да @BotFather орқали олиш мумкин)\n"
            "============================================================\n"
        )

    bot = Bot(token=token)
    dp = Dispatcher(storage=MemoryStorage())

    # Асосий роутерларни қўшиш
    dp.include_router(main_router)

    # Буйруқлар менюсини ўрнатиш
    try:
        await set_main_menu_commands(bot)
    except Exception as e:
        logger.error(f"Буйруқларни ўрнатишда хатолик: {e}")

    me = await bot.get_me()
    logger.info(f"Бот муваффақиятли уланди: @{me.username} ({me.first_name})")

    # Эски кутилмаган хабарларни тозалаб янгиларини қабул қилиш
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот тўхтатилди.")
