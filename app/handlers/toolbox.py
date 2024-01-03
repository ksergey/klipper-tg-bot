import logging

from aiogram import Bot, Dispatcher, Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardMarkup
from aiogram.filters.callback_data import CallbackData

from app.moonraker import Moonraker

logger = logging.getLogger(__name__)
router = Router()

class ToolboxCallback(CallbackData, prefix='tb'):
    gcode: str

def make_toolbox_keyboard(distance: int = 50) -> InlineKeyboardMarkup:
    def relative_before(gcode: str) -> str:
        return '\n'.join(['G91', gcode])

    builder = InlineKeyboardBuilder()
    builder.button(
        text='Home All',
        callback_data=ToolboxCallback(gcode='G28')
    )
    builder.button(
        text='Y+',
        callback_data=ToolboxCallback(gcode=relative_before(f'G1 Y{distance}'))
    )
    builder.button(
        text='Home XY',
        callback_data=ToolboxCallback(gcode='G28 X Y')
    )
    builder.button(
        text='Z+',
        callback_data=ToolboxCallback(gcode=relative_before(f'G1 Z{distance}'))
    )
    builder.button(
        text='X-',
        callback_data=ToolboxCallback(gcode=relative_before(f'G1 X-{distance}'))
    )
    builder.button(
        text='Y-',
        callback_data=ToolboxCallback(gcode=relative_before(f'G1 Y-{distance}'))
    )
    builder.button(
        text='X+',
        callback_data=ToolboxCallback(gcode=relative_before(f'G1 X{distance}'))
    )
    builder.button(
        text='Z-',
        callback_data=ToolboxCallback(gcode=relative_before(f'G1 Z-{distance}'))
    )
    builder.adjust(4)
    return builder.as_markup(resize_keyboard=True)

@router.callback_query(ToolboxCallback.filter())
async def callback_toolbox(callback: CallbackQuery, callback_data: ToolboxCallback, bot: Bot, moonraker: Moonraker):
    await moonraker.gcode_script(callback_data.gcode)
    await callback.answer(text=f'done')

@router.message(Command('toolbox'))
async def handler_command_toolbox(message: Message):
    try:
        await message.answer(f'\N{Wrench} toolbox', reply_markup=make_toolbox_keyboard(25))
    except Exception as ex:
        await message.reply(f'\N{Heavy Ballot X} failed ({ex})')
        logger.exception(f'exception during process message {message}')
