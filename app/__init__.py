from aiogram import Bot, Dispatcher
from aiogram.types import ParseMode, BotCommand
from app.config import config
from app.moonraker import Moonraker

dp = Dispatcher(
    Bot(token=config.telegram.token, parse_mode=ParseMode.HTML)
)

moonraker = Moonraker(
    endpoint=config.moonraker.endpoint
)

commands = []


# decorator for register bot commands in telegram
def bot_command(name: str, description: str):
    def decorator(func):
        commands.append(BotCommand(name, description))
        dp.register_message_handler(func, commands=[name], chat_id=config.telegram.chat_id)
        return func
    return decorator
