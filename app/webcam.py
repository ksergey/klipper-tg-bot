import logging
import aiohttp
import asyncio

from typing import Optional

from app.config import config

logger = logging.getLogger(__name__)


async def get_webcam_image() -> Optional[bytes]:
    if config.webcam.url is None:
        return None
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(config.webcam.url) as response:
                if response.status == 200:
                    return await response.read()
    except Exception as e:
        logger.error(f'can not capture image from webcam ({e})')
    return None
