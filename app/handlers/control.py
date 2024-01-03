import logging

from aiogram import Bot, Dispatcher, Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardMarkup
from aiogram.filters.callback_data import CallbackData

from app.moonraker import Moonraker

logger = logging.getLogger(__name__)
router = Router()

class ControlCallback(CallbackData, prefix='ctrl'):
    gcode: str

def make_control_keyboard(distance: int = 50) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text='Home All',
        callback_data=ControlCallback(gcode='G28')
    )
    builder.button(
        text='Y+',
        callback_data=ControlCallback(gcode=f'G1 Y{distance}')
    )
    builder.button(
        text='Home XY',
        callback_data=ControlCallback(gcode='G28 X Y')
    )
    builder.button(
        text='Z+',
        callback_data=ControlCallback(gcode=f'G1 Z{distance}')
    )
    builder.button(
        text='X-',
        callback_data=ControlCallback(gcode=f'G1 X-{distance}')
    )
    builder.button(
        text='Y-',
        callback_data=ControlCallback(gcode=f'G1 Y-{distance}')
    )
    builder.button(
        text='X+',
        callback_data=ControlCallback(gcode=f'G1 X{distance}')
    )
    builder.button(
        text='Z-',
        callback_data=ControlCallback(gcode=f'G1 Z-{distance}')
    )
    builder.adjust(4)
    return builder.as_markup(resize_keyboard=True)

@router.callback_query(ControlCallback.filter())
async def callback_control(callback: CallbackQuery, callback_data: ControlCallback, bot: Bot, moonraker: Moonraker):
    # TODO
    await callback.answer(show_alert=True, text=callback_data.gcode)

@router.message(Command('control'))
async def handler_command_control(message: Message):
    try:
        await message.answer('toolbox', reply_markup=make_control_keyboard(50))
    except Exception as ex:
        await message.reply(f'\N{Heavy Ballot X} failed ({ex})')
        logger.exception(f'exception during process message {message}')
