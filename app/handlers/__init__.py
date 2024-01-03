from typing import List

from aiogram import Router
from aiogram.types import Message, BotCommand
from aiogram.filters import Command

commands = [
    BotCommand(command='status', description='show current printer status'),
    BotCommand(command='gcode', description='excecute gcode'),
    BotCommand(command='video', description='capture few seconds video'),
    BotCommand(command='last', description='show last print job status'),
    BotCommand(command='control', description='show control toolbox'),
    BotCommand(command='help', description='show help'),
]

router = Router()

@router.message(Command('help'))
async def handler_command_help(message: Message):
    help_message = ''.join(
        f'/{command.command} - {command.description}\n' for command in commands
    )
    await message.answer(help_message)

def setup_router() -> Router:
    from . import status, gcode, video, last, control

    main_router = Router()
    main_router.include_router(status.router)
    main_router.include_router(gcode.router)
    main_router.include_router(video.router)
    main_router.include_router(last.router)
    main_router.include_router(control.router)
    main_router.include_router(router)

    return main_router

def setup_commands() -> List[BotCommand]:
    return commands
