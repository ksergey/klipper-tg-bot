import asyncio
import aiohttp
import ujson
import logging

from typing import Optional, Callable
from inspect import iscoroutinefunction

logger = logging.getLogger(__name__)


class MoonrakerWebsocket:
    DEFAULT_PORT = 7125
    RECONNECT_INTERVAL = 5.0
    HEARTBEAT_INTERVAL = 5.0

    def __init__(self, endpoint: str, loop: asyncio.AbstractEventLoop = None) -> None:
        if loop is None:
            loop = asyncio.get_event_loop()

        if ':' in endpoint:
            host, port = endpoint.split(':')
        else:
            host, port = (endpoint, str(MoonrakerWebsocket.DEFAULT_PORT))

        self._endpoint = f'{host}:{port}'
        self._loop = loop
        self._task = None
        self._session: Optional[aiohttp.ClientSession] = None
        self._ws: Optional[aiohttp.ClientWebSocketResponse] = None
        self._listeners = []
        self._requests = dict()
        self._next_id = 0

    def add_listener(self, callback: Callable) -> None:
        self._listeners.append(callback)

    def is_opened(self) -> bool:
        return self._ws is not None and not self._ws.closed

    async def open(self) -> None:
        if self._task is not None and self._task.done() is not False:
            raise Exception('moonraker service already running')
        self._task = asyncio.create_task(self._loop_task())

    async def close(self) -> None:
        if self._task is not None or self._task.done() is True:
            return

        self._task.cancel()
        await self._task

    async def request(self, method: str, params: Optional[dict] = None) -> dict:
        future = self._loop.create_future()
        id = self._get_next_id()
        self._requests[id] = future

        try:
            await self._send_request(method, params=params, id=id)
        except Exception:
            del self._requests[id]
            raise

        await future
        if future.exception():
            raise future.exception()

        data = future.result()
        if 'error' in data:
            raise RuntimeError(data['error']['message'])

        return data['result']

    async def _send_request(self, method: str, params: Optional[dict] = None, id: Optional[int] = None) -> None:
        if self._ws is None or self._ws.closed:
            raise RuntimeError('moonraker not connected')

        if id is None:
            id = self._get_next_id()

        request_str = ujson.dumps({
            'jsonrpc': '2.0',
            'method': method,
            'params': params or {},
            'id': id
        })
        logger.debug(f'send_request: {request_str}')

        await self._ws.send_str(request_str)

    def _get_next_id(self) -> int:
        id = self._next_id
        self._next_id += 1
        return id

    async def _loop_task(self) -> None:
        async def get_oneshot_token() -> str:
            url = f'http://{self._endpoint}/access/oneshot_token'
            async with self._session.get(url) as response:
                if response.status != 200:
                    raise Exception('unable to get oneshot token')
                data = await response.json()
                return data['result']

        try:
            next_connect_time = 0.0

            while True:
                if next_connect_time > self._loop.time():
                    await asyncio.sleep(next_connect_time - self._loop.time())
                next_connect_time = self._loop.time() + MoonrakerWebsocket.RECONNECT_INTERVAL

                self._requests.clear()

                try:
                    if not self._session or self._session.closed:
                        self._session = aiohttp.ClientSession(loop=self._loop)

                    oneshot_token = await get_oneshot_token()
                    logger.debug(f'oneshot token: {oneshot_token}')

                    if not self._ws or self._ws.closed:
                        url = f'ws://{self._endpoint}/websocket?token={oneshot_token}'
                        self._ws = await self._session.ws_connect(url, heartbeat=MoonrakerWebsocket.HEARTBEAT_INTERVAL)
                        logger.info(f'connected to {url}')

                except Exception as e:
                    logger.error(f'failed to establish connection ({e})')
                    continue

                asyncio.ensure_future(self._invoke_callback('connected', {}), loop=self._loop)

                async for message in self._ws:
                    if message.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.CLOSE, aiohttp.WSMsgType.ERROR):
                        break
                    if message.type == aiohttp.WSMsgType.TEXT:
                        await self._process_message(message.json())

        except asyncio.CancelledError as e:
            pass

        finally:
            if self._ws and not self._ws.closed:
                await self._ws.close()
            if self._session and not self._session.closed:
                await self._session.close()

    async def _process_message(self, data) -> None:
        logger.debug(f'data: {ujson.dumps(data, indent=2)}')

        if 'method' in data:
            method = data['method']
            params = data['params'][0] if 'params' in data else {}
            asyncio.ensure_future(self._invoke_callback(method, params), loop=self._loop)
            return

        if 'id' in data:
            id = data['id']
            if id in self._requests:
                future = self._requests[id]
                future.set_result(data)
                del self._requests[id]
            return

    async def _invoke_callback(self, method: str, params: dict) -> None:
        for callback in self._listeners:
            try:
                if iscoroutinefunction(callback):
                    await callback(method, params)
                else:
                    callback(method, params)
            except Exception as e:
                logger.error(f'got exception during invoke callback ({e})')
