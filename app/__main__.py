import logging
import asyncio
import ujson

from typing import Optional

from aiogram import Dispatcher
from aiogram.types import Message, BotCommand, ReplyKeyboardRemove
from aiogram.utils import executor

from app import dp, moonraker, commands, bot_command
from app.args import args
from app.config import config
from app.utils import create_status_text
from app.printer import Printer
from app.webcam import get_webcam_image

logging.basicConfig(
    filename=args.logfile,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=args.loglevel
)

logger = logging.getLogger(__name__)


async def send_status(printer: Printer) -> None:
    text = create_status_text(printer)
    image = await get_webcam_image()
    if image is not None:
        await dp.bot.send_photo(chat_id=config.telegram.chat_id, photo=image, caption=text)
    else:
        await dp.bot.send_message(chat_id=config.telegram.chat_id, text=text)


async def send_message_from_printer(printer: Printer) -> None:
    message = printer.data['display_status']['message']
    await dp.bot.send_message(chat_id=config.telegram.chat_id, text=f'printer: <i>{message}</i>')


async def startup(dp: Dispatcher):
    async def callback_progress_changed(printer: Printer) -> None:
        await send_status(printer)
    moonraker.printer.add_listener('state_changed', callback_progress_changed)
    moonraker.printer.add_listener('progress_changed', callback_progress_changed)

    async def callback_message(printer: Printer) -> None:
        await send_message_from_printer(printer)
    moonraker.printer.add_listener('message', callback_message)

    await moonraker.open()

    await dp.bot.set_my_commands(commands=commands)
    await dp.skip_updates()
    await dp.bot.send_message(
        config.telegram.chat_id,
        f'\N{Black Right-Pointing Pointer} <i>bot going online</i>', reply_markup=ReplyKeyboardRemove()
    )


async def shutdown(dp: Dispatcher):
    await dp.bot.send_message(config.telegram.chat_id, f'\N{Black Left-Pointing Pointer} <i>bot going offline</i>')
    await moonraker.close()


if __name__ == '__main__':
    try:
        logger.info(f'config:\n{config}')

        import app.commands
        loop = asyncio.new_event_loop()
        executor.start_polling(dp, skip_updates=True, on_startup=startup, on_shutdown=shutdown, loop=loop)
    except (KeyboardInterrupt, SystemExit):
        logger.info('bot stopped!')
