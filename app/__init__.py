from aiogram import Router, F
from aiogram.types import BotCommand
from aiogram.filters import Command, CommandObject
from app.config_reader import config

all_commands = []

main_router = Router()

# decorator for register bot commands in telegram
def bot_command(name: str, description: str, ignore: bool=False):
    def decorator(func):
        all_commands.append(BotCommand(command=name, description=description))
        main_router.message.register(func, Command(name))
        # main_router.message.register(func, Command(name), F.chat_id==config.telegram.chat_id)
        return func

    def empty(func):
        return func

    if ignore == False:
        return decorator
    else:
        return empty
