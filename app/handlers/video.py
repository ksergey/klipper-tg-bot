import logging

from aiogram import Bot, Dispatcher, Router
from aiogram.types import Message, BufferedInputFile
from aiogram.filters import Command

from app.webcam import get_webcam_video

logger = logging.getLogger(__name__)
router = Router()

@router.message(Command('video'))
async def handler_command_video(message: Message, bot: Bot, dispatcher: Dispatcher):
    notification_message = await message.answer('\N{SLEEPING SYMBOL}...')
    try:
        video = await get_webcam_video()
        if video is None:
            raise RuntimeError('failed to capture video (see logs)')
        await message.reply_video(BufferedInputFile(video, 'live.mp4'))
    except Exception as ex:
        await message.reply(f'\N{Heavy Ballot X} failed ({ex})')
        logger.exception(f'exception during process message {message}')
    finally:
        await notification_message.delete()
