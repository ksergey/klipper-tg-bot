import logging

from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command, CommandObject

from app.moonraker import Moonraker

logger = logging.getLogger(__name__)
router = Router()

@router.message(Command('gcode'))
async def handler_command_gcode(message: Message, command: CommandObject, moonraker: Moonraker):
    notification_message = await message.answer('\N{SLEEPING SYMBOL}...')
    try:
        script = command.args or ''
        if script == '':
            raise RuntimeError('empty script')
        await moonraker.gcode_script(script)
        await message.reply('done')
    except Exception as ex:
        await message.reply(f'\N{Heavy Ballot X} error: {ex}')
        logger.exception(f'exception during process message {message}')
    finally:
        await notification_message.delete()
