import logging

from aiogram import Bot, Dispatcher, Router
from aiogram.types import Message
from aiogram.filters import Command

from app.moonraker import Moonraker

logger = logging.getLogger(__name__)
router = Router()

@router.message(Command('gcode'))
async def handler_command_gcode(message: Message, bot: Bot, dispatcher: Dispatcher, moonraker: Moonraker):
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
