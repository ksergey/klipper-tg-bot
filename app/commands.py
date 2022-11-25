import logging

from aiogram.types import Message

from app import dp, moonraker, bot_command, commands
from app.config import config
from app.webcam import get_webcam_image
from app.utils import create_status_text, format_time, format_fillament_length

logger = logging.getLogger(__name__)


@bot_command('status', 'show current printer status')
async def command_status(message: Message):
    try:
        if not moonraker.is_opened():
            raise RuntimeError('moonraker not connected')

        text = create_status_text(moonraker.printer)
        image = await get_webcam_image()
        if image is not None:
            await message.reply_photo(image, caption=text)
        else:
            await message.reply(text)
    except Exception as ex:
        await message.reply(f'\N{Heavy Ballot X} failed ({ex})')
        logger.exception(f'exception during process message {message}')


@bot_command('restart', 'restart printer')
async def command_restart(message: Message):
    notification_message = await message.answer('\N{SLEEPING SYMBOL}...')
    try:
        await moonraker.restart()
        await message.reply('done')
    except Exception as ex:
        await message.reply(f'\N{Heavy Ballot X} failed ({ex})')
        logger.exception(f'exception during process message {message}')
    finally:
        await notification_message.delete()


@bot_command('firmware_restart', 'restart printer firmware')
async def command_firmware_restart(message: Message):
    notification_message = await message.answer('\N{SLEEPING SYMBOL}...')
    try:
        await moonraker.firmware_restart()
        await message.reply('done')
    except Exception as ex:
        await message.reply(f'\N{Heavy Ballot X} failed ({ex})')
        logger.exception(f'exception during process message {message}')
    finally:
        await notification_message.delete()


@bot_command('emergency_stop', 'emergency stop printer')
async def command_emergency_stop(message: Message):
    notification_message = await message.answer('\N{SLEEPING SYMBOL}...')
    try:
        await moonraker.emergency_stop()
        await message.reply('done')
    except Exception as ex:
        await message.reply(f'\N{Heavy Ballot X} failed ({ex})')
        logger.exception(f'exception during process message {message}')
    finally:
        await notification_message.delete()

@bot_command('last_job_status', 'print last job status')
async def command_last_job_status(message: Message):
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
                    await message.reply_photo(image, caption=text)
                else:
                    await message.reply(text)
            else:
                await message.reply(text)
    except Exception as ex:
        await message.reply(f'\N{Heavy Ballot X} failed ({ex})')
        logger.exception(f'exception during process message {message}')
    finally:
        await notification_message.delete()


@bot_command('help', 'print this help message')
async def command_help(message: Message):
    help_message = ''.join(
        f'/{command.command} <i>- {command.description}</i>\n' for command in commands
    )
    await message.answer(help_message)
