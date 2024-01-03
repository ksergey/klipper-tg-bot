import logging

from aiogram import Bot, Dispatcher, Router
from aiogram.types import Message, BufferedInputFile
from aiogram.filters import Command

from app.moonraker import Moonraker
from app.utils import create_status_text
from app.webcam import get_webcam_image

logger = logging.getLogger(__name__)
router = Router()

@router.message(Command('status'))
async def handler_command_status(message: Message, bot: Bot, dispatcher: Dispatcher, moonraker: Moonraker):
    notification_message = await message.answer('\N{SLEEPING SYMBOL}...')
    try:
        if not moonraker.online():
            raise RuntimeError('moonraker not connected')

        text = create_status_text(moonraker.printer)
        image = await get_webcam_image()
        if image is not None:
            await message.reply_photo(BufferedInputFile(image, 'live_view.png'), caption=text)
        else:
            await message.reply(text)
    except Exception as ex:
        await message.reply(f'\N{Heavy Ballot X} failed ({ex})')
        logger.exception(f'exception during process message {message}')
    finally:
        await notification_message.delete()
