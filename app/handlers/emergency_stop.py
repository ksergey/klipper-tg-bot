import logging

from aiogram import Bot, Dispatcher, Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardMarkup

from app.moonraker import Moonraker

logger = logging.getLogger(__name__)
router = Router()

class EmergencyStopCallback(CallbackData, prefix='es'):
    action: str

def make_confirmation_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text='Confirm',
        callback_data=EmergencyStopCallback(action='confirm')
    )
    builder.button(
        text='Cancel',
        callback_data=EmergencyStopCallback(action='cancel')
    )
    return builder.as_markup()

@router.callback_query(EmergencyStopCallback.filter())
async def callback_emergency_stop(callback: CallbackQuery, callback_data: EmergencyStopCallback, bot: Bot, moonraker: Moonraker):
    await callback.answer()

    message = callback.message.reply_to_message
    await callback.message.delete()

    try:
        if callback_data.action == 'confirm':
            await moonraker.emergency_stop()
            await message.reply('done')
        else:
            await message.reply('cancelled')
    except Exception as ex:
        await message.edit_text(f'\N{Heavy Ballot X} error: {ex}')

@router.message(Command('emergency_stop'))
async def handler_command_emergency_stop(message: Message, bot: Bot, dispatcher: Dispatcher, moonraker: Moonraker):
    await message.reply('are you shure?', reply_markup=make_confirmation_keyboard())
