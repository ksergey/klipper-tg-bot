import asyncio
import aiohttp
import ujson
import logging

from typing import Optional

from app.moonraker_session import MoonrakerSession
from app.printer import Printer

logger = logging.getLogger(__name__)

class Moonraker:
    def __init__(self, endpoint: str) -> None:
        self._url = f'http://{endpoint}'
        self._session = MoonrakerSession(endpoint)
        self._session.add_listener(self._update)
        self.printer = Printer()

    def online(self) -> bool:
        return self._session.online()

    async def open(self):
        await self._session.open()

    async def close(self):
        await self._session.close()

    async def emergency_stop(self) -> dict:
        return await self._session.request('printer.emergency_stop')

    async def gcode_script(self, script: str) -> dict:
        return await self._session.request('printer.gcode.script', {'script': script})

    async def get_file_dir(self, path: str) -> dict:
        return await self._session.request('server.files.list', {'path': path})

    async def get_file_list(self) -> dict:
        return await self._session.request('server.files.list')

    async def get_file_metadata(self, filename: str) -> dict:
        return await self._session.request('server.files.metadata', {'filename': filename})

    async def print_cancel(self) -> dict:
        return await self._session.request('printer.print.cancel')

    async def print_pause(self) -> dict:
        return await self._session.request('printer.print.pause')

    async def print_resume(self) -> dict:
        return await self._session.request('printer.print.resume')

    async def print_start(self, filename: str) -> dict:
        return await self._session.request('printer.print.start', {'filename': filename})

    async def restart(self) -> dict:
        return await self._session.request('printer.restart')

    async def firmware_restart(self) -> dict:
        return await self._session.request('printer.firmware_restart')

    async def objects_query(self, objects: dict) -> dict:
        return await self._session.request('printer.objects.query', {'objects': objects})

    async def history_list(self, limit: int = 10, start: int = 0, order: str = 'desc') -> dict:
        return await self._session.request('server.history.list', { 'limit': limit, 'start': start, 'order': order })

    async def gcode_script(self, script: str) -> dict:
        return await self._session.request('printer.gcode.script', { 'script': script })

    async def get_thumbnail(self, path: str) -> Optional[bytes]:
        return await self._http_get(f'/server/files/gcodes/{path}')

    async def _update(self, method: str, params: Optional[dict]) -> None:
        if method == 'notify_status_update':
            self.printer.update(params)
        elif method == 'notify_gcode_response':
            logger.debug(ujson.dumps(params, 2)) # TODO
        elif method in ['connected', 'notify_klippy_ready']:
            self.printer.reset()
            logger.info(f'subscribing printer objects (method: "{method}")')
            await self._subscribe_printer_objects()
        elif method == 'notify_klippy_disconnected':
            self.printer.change_state('disconnected')
        elif method == 'notify_klippy_shutdown':
            self.printer.change_state('shutdown')

    async def _subscribe_printer_objects(self) -> None:
        data = await self._session.request('printer.objects.subscribe', {
            'objects': {
                'bed_mesh': None,
                # 'configfile': None,
                'display_status': None,
                'extruder': None,
                'fan': None,
                'gcode_move': None,
                'heater_bed': None,
                'idle_timeout': None,
                'pause_resume': None,
                'print_stats': None,
                'toolhead': None,
                'virtual_sdcard': None,
                'webhooks': None,
                'motion_report': None,
                'firmware_retraction': None,
                'exclude_object': None
            }
        })
        self.printer.update(data['status'])

    async def _http_get(self, path: str) -> Optional[bytes]:
        if path.startswith('/'):
            url = f'{self._url}{path}'
        else:
            url = f'{self._url}/{path}'

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        return await response.read()
                    else:
                        raise Exception(f'invalid response code {response.status}')
        except Exception as e:
            logger.error(f'failed to get "{url}" ({e})')
        return None
