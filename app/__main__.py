import logging
import asyncio
import ujson

from typing import Any

from aiogram import Bot, Dispatcher, Router
from aiogram.enums import ParseMode
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.fsm.storage.memory import MemoryStorage

from app import moonraker
from app.config import config
from app.args import args
from app.printer import Printer

logger = logging.getLogger(__name__)

router = Router()

@router.message(CommandStart())
async def commad_start(message: Message, command: CommandObject, bot: Bot) -> Any:
    pass

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

    # await bot.set_my_commands(commands=commands)

    # await dispatcher.skip_updates()
    await bot.send_message(
        config.telegram.chat_id,
        f'\N{Black Right-Pointing Pointer} <i>bot going online</i>', reply_markup=ReplyKeyboardRemove()
    )


async def on_shutdown(dispatcher: Dispatcher, bot: Bot):
    await bot.send_message(config.telegram.chat_id, f'\N{Black Left-Pointing Pointer} <i>bot going offline</i>')
    await moonraker.close()


async def main():
    logging.basicConfig(
        filename=args.logfile,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=args.loglevel
    )

    bot_settings = {
        'session': AiohttpSession(),
        'parse_mode': ParseMode.HTML
    }

    bot = Bot(token=config.telegram.token, **bot_settings)

    dispatcher = Dispatcher(storage=MemoryStorage())
    dispatcher.include_router(router)
    dispatcher.startup.register(on_startup)
    dispatcher.shutdown.register(on_shutdown)

    await dispatcher.start_polling(bot)


if __name__ == '__main__':
    try:
        logger.info(f'config:\n{config}')

        asyncio.run(main())

    except (KeyboardInterrupt, SystemExit):
        logger.info('bot stopped!')
