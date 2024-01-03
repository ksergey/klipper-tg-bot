import logging
import asyncio

from typing import Optional

from app.config_reader import config

logger = logging.getLogger(__name__)


async def ffmpeg_execute_with_args(args: str) -> Optional[bytes]:
    if config.webcam.input is None:
        return None

    cmd_line = f'ffmpeg -hide_banner -loglevel error -y -i {config.webcam.input} {args} -'

    logger.debug(f'ffmpeg_execute_with_args cmd_line: "{cmd_line}"')

    process = await asyncio.create_subprocess_shell(
        cmd_line, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        logger.error(f'ffmpeg spawn error ({stderr})')
        return None

    return stdout


async def get_webcam_image() -> Optional[bytes]:
    return await ffmpeg_execute_with_args('-frames:v 1 -c:v png -f image2pipe')


async def get_webcam_video(duration: int=5) -> Optional[bytes]:
    return await ffmpeg_execute_with_args(
        f'-t {duration} -an -c:v libx264 -crf {config.webcam.crf} -movflags frag_keyframe+empty_moov -f mp4 -pix_fmt yuv420p'
    )
