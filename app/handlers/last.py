import logging

from aiogram import Router
from aiogram.types import Message, BufferedInputFile
from aiogram.filters import Command

from app.moonraker import Moonraker
from app.utils import format_time

logger = logging.getLogger(__name__)
router = Router()

@router.message(Command('last'))
async def handler_command_last(message: Message, moonraker: Moonraker):
    notification_message = await message.answer('\N{SLEEPING SYMBOL}...')
    try:
        data = await moonraker.history_list(limit=1, order='desc')
        jobs = data['jobs']
        if not jobs:
            await message.reply('no jobs')
        else:
            job = jobs[0]
            text = (
                f'\N{Memo} <i>filename:</i> <b>{job["filename"]}</b>\n'
                f'\N{White Heavy Check Mark} <i>status:</i> <b>{job["status"]}</b>\n'
                f'\N{Stopwatch} <i>print duration:</i> <b>{format_time(job["print_duration"])}</b>\n'
            )

            thumbnails = job['metadata']['thumbnails']
            if thumbnails:
                image = await moonraker.get_thumbnail(thumbnails[-1]['relative_path'])
                if image:
                    await message.reply_photo(BufferedInputFile(image, thumbnails[-1]['relative_path']), caption=text)
                else:
                    await message.reply(text)
            else:
                await message.reply(text)
    except Exception as ex:
        await message.reply(f'\N{Heavy Ballot X} error: {ex}')
        logger.exception(f'exception during process message {message}')
    finally:
        await notification_message.delete()
