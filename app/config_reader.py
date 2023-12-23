__all__ = ('config')

from configparser import ConfigParser
from dataclasses import dataclass, field
from typing import List, Dict

from app.args_reader import args


@dataclass
class TelegramConfig:
    token: str = field(repr=False)
    chat_id: int = field(repr=False)


@dataclass
class MoonrakerConfig:
    endpoint: str


@dataclass
class WebcamConfig:
    input: str = None
    crf: int = 26


@dataclass
class Config:
    telegram: TelegramConfig
    moonraker: MoonrakerConfig
    webcam: WebcamConfig


def load_config() -> Config:
    parser = ConfigParser()
    parser.read(args.config)

    config = Config(
        telegram=TelegramConfig(
            token=parser.get('telegram', 'token'),
            chat_id=int(parser.get('telegram', 'chat_id'))
        ),
        moonraker=MoonrakerConfig(
            endpoint=parser.get('moonraker', 'endpoint')
        ),
        webcam=WebcamConfig(
            input=parser.get('webcam', 'input', fallback=None),
            crf=int(parser.get('webcam', 'crf', fallback=26))
        )
    )

    return config


config = load_config()
