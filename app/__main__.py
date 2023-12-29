import logging
import asyncio
import ujson

from typing import Optional

from aiogram import Dispatcher, Bot
from aiogram.types import Message, BotCommand, ReplyKeyboardRemove
from aiogram.enums import ParseMode

from app import dp, moonraker, commands, bot_command
from app.args_reader import args
from app.config_reader import config
from app.utils import create_status_text
from app.printer import Printer
from app.webcam import get_webcam_image

logging.basicConfig(
    filename=args.logfile,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=args.loglevel
)

logger = logging.getLogger(__name__)


async def send_status(printer: Printer, bot: Bot) -> None:
    text = create_status_text(printer)
    image = await get_webcam_image()
    if image is not None:
        await bot.send_photo(chat_id=config.telegram.chat_id, photo=image, caption=text)
    else:
        await bot.send_message(chat_id=config.telegram.chat_id, text=text)


async def send_message_from_printer(printer: Printer, bot: Bot) -> None:
    message = printer.data['display_status']['message']
    await bot.send_message(chat_id=config.telegram.chat_id, text=f'printer: <i>{message}</i>')


async def on_startup(dispatcher: Dispatcher, bot: Bot):
    async def callback_progress_changed(printer: Printer) -> None:
        if printer.data is not None:
            await send_status(printer, bot)
    moonraker.printer.add_listener('state_changed', callback_progress_changed)
    moonraker.printer.add_listener('progress_changed', callback_progress_changed)

    async def callback_message(printer: Printer) -> None:
        await send_message_from_printer(printer, bot)
    moonraker.printer.add_listener('message', callback_message)

    await moonraker.open()

    await bot.set_my_commands(commands=commands)
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.send_message(
        config.telegram.chat_id,
        f'\N{Black Right-Pointing Pointer} <i>bot going online</i>', reply_markup=ReplyKeyboardRemove()
    )


async def on_shutdown(dispatcher: Dispatcher, bot: Bot):
    await bot.send_message(config.telegram.chat_id, f'\N{Black Left-Pointing Pointer} <i>bot going offline</i>')
    await moonraker.close()


async def main():
    logger.info(f'config:\n{config}')

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    bot = Bot(token=config.telegram.token, parse_mode=ParseMode.HTML)

    await dp.start_polling(bot)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info('bot stopped!')
