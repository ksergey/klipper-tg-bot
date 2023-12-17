import logging

from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.utils.callback_data import CallbackData

from app import dp, moonraker, bot_command, commands
from app.config import config
from app.webcam import get_webcam_image, get_webcam_video
from app.utils import create_status_text, format_time, format_fillament_length

logger = logging.getLogger(__name__)

action_cb = CallbackData('action', 'action', 'ack')


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


@bot_command('gcode', 'execute gcode command')
async def command_gcode(message: Message):
    notification_message = await message.answer('\N{SLEEPING SYMBOL}...')
    try:
        script = message.get_args()
        if script == '':
            raise RuntimeError('empty script')
        await moonraker.gcode_script(script)
        await message.reply('done')
    except Exception as ex:
        await message.reply(f'\N{Heavy Ballot X} failed ({ex})')
        logger.exception(f'exception during process message {message}')
    finally:
        await notification_message.delete()


# TODO: in case of no device don't add to commands
@bot_command('video', 'capture few seconds of video', config.webcam.input is None)
async def command_video(message: Message):
    notification_message = await message.answer('\N{SLEEPING SYMBOL}...')
    try:
        video = await get_webcam_video()
        if video is None:
            raise RuntimeError('failed to capture video (see logs)')
        await message.reply_video(video)
    except Exception as ex:
        await message.reply(f'\N{Heavy Ballot X} failed ({ex})')
        logger.exception(f'exception during process message {message}')
    finally:
        await notification_message.delete()


@bot_command('last', 'print last job status')
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


def get_action_ack_markup(action: str) -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup(row_width=2)
    markup.row(*[
        InlineKeyboardButton('OK', callback_data=action_cb.new(action=action, ack='ok')),
        InlineKeyboardButton('Cancel', callback_data=action_cb.new(action=action, ack='cancel'))
    ])
    return markup


@dp.callback_query_handler(action_cb.filter())
async def callback_action(query: CallbackQuery, callback_data: dict[str,str]):
    action = callback_data['action']
    ack = callback_data['ack']

    if ack == 'ok':
        try:
            if action == 'restart':
                await moonraker.restart()
            if action == 'firmware_restart':
                await moonraker.firmware_restart()
            if action == 'emergency_stop':
                await moonraker.emergency_stop()

            await query.message.edit_text('done')
        except Exception as ex:
            await query.message.edit_text(f'\N{Heavy Ballot X} failed ({ex})')
            logger.exception(f'exception during process action {action}')
    else:
        await query.message.edit_text('cancelled')


@bot_command('restart', 'restart printer')
async def command_restart(message: Message):
    await message.reply('confirm', reply_markup=get_action_ack_markup('restart'))


@bot_command('firmware_restart', 'restart printer firmware')
async def command_firmware_restart(message: Message):
    await message.reply('confirm', reply_markup=get_action_ack_markup('firmware_restart'))


@bot_command('emergency_stop', 'emergency stop printer')
async def command_emergency_stop(message: Message):
    await message.reply('confirm', reply_markup=get_action_ack_markup('emergency_stop'))


# @dp.callback_query_handler(chat_id=config.telegram.chat_id)
# async def callback_handler(query: CallbackQuery):
#     action, params = query.data.split(',')
#
#     try:
#         if action == 'hotend_temp':
#             await moonraker.gcode_script(f'SET_HEATER_TEMPERATURE HEATER=extruder TARGET={params}')
#     except Exception as ex:
#         logger.exception(f'exception during process callback (action="{action}", params="{params}"): {ex}')
#
#     await query.answer('done')
#
#
# @bot_command('hotend_temp', 'set hotend temperature')
# async def command_hotend_temp(message: Message):
#     notification_message = await message.answer('\N{SLEEPING SYMBOL}...')
#     try:
#         keyboard = InlineKeyboardMarkup()
#         for temp in [ 200, 210, 230, 240, 250 ]:
#             keyboard.row(InlineKeyboardButton(f'{temp} C', callback_data=f'hotend_temp,{temp}'))
#         await message.answer(text='choose temp', reply_markup=keyboard)
#     except Exception as ex:
#         await message.reply(f'\N{Heavy Ballot X} failed ({ex})')
#         logger.exception(f'exception during process message {message}')
#     finally:
#         await notification_message.delete()


@bot_command('help', 'print this help message')
async def command_help(message: Message):
    help_message = ''.join(
        f'/{command.command} <i>- {command.description}</i>\n' for command in commands
    )
    await message.answer(help_message)
