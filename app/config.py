__all__ = ('config')

from configparser import ConfigParser
from dataclasses import dataclass, field
from typing import List, Dict

from .args import args


@dataclass
class TelegramConfig:
    token: str = field(repr=False)
    chat_id: int = field(repr=False)


@dataclass
class MoonrakerConfig:
    endpoint: str


@dataclass
class WebcamConfig:
    url: str = None


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
            url=parser.get('webcam', 'url', fallback=None)
        )
    )

    return config


config = load_config()
