import asyncio
import aiohttp
import ujson
import logging

from typing import Optional, Callable
from inspect import iscoroutinefunction

logger = logging.getLogger(__name__)


class MoonrakerSession:
    DEFAULT_PORT = 7125
    RECONNECT_INTERVAL = 10.0
    HEARTBEAT_INTERVAL = 5.0


    def __init__(self, endpoint: str) -> None:
        if ':' in endpoint:
            host, port = endpoint.split(':')
        else:
            host, port = (endpoint, str(MoonrakerSession.DEFAULT_PORT))

        self._endpoint = f'{host}:{port}'
        self._task = None
        self._session: Optional[aiohttp.ClientSession] = None
        self._ws: Optional[aiohttp.ClientWebSocketResponse] = None
        self._listeners = []
        self._requests = dict()
        self._next_id = 0
        self._background_tasks = set()


    def add_listener(self, callback: Callable) -> None:
        self._listeners.append(callback)


    def online(self) -> bool:
        return self._ws and not self._ws.closed


    async def open(self) -> None:
        if self._task and not self._task.done():
            raise Exception('moonraker service already running')
        self._task = asyncio.create_task(self._loop_task())


    async def close(self) -> None:
        if not self._task or self._task.done():
            return

        self._task.cancel()
        await self._task


    async def request(self, method: str, params: Optional[dict] = None) -> dict:
        future = asyncio.Future()
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
                loop = asyncio.get_running_loop()
                if next_connect_time > loop.time():
                    await asyncio.sleep(next_connect_time - loop.time())
                next_connect_time = loop.time() + MoonrakerSession.RECONNECT_INTERVAL

                self._clear_requests()

                try:
                    if not self._session or self._session.closed:
                        self._session = aiohttp.ClientSession()

                    oneshot_token = await get_oneshot_token()
                    logger.debug(f'oneshot token: {oneshot_token}')

                    if not self._ws or self._ws.closed:
                        url = f'ws://{self._endpoint}/websocket?token={oneshot_token}'
                        self._ws = await self._session.ws_connect(url, heartbeat=MoonrakerSession.HEARTBEAT_INTERVAL)
                        logger.info(f'connected to {url}')

                except Exception as e:
                    logger.error(f'failed to establish connection ({e})')
                    continue


                self._invoke_callback('connected', {})

                # try:
                #     task = asyncio.create_task(self._invoke_callback('connected', {}))
                # except Exception as e:
                #     logger.warning(f'can\'t invoke callback: {e}')
                # else:
                #     self._background_tasks.add(task)
                #     task.add_done_callback(self._background_tasks.discard)

                async for message in self._ws:
                    logger.debug("received message")
                    if message.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.CLOSE, aiohttp.WSMsgType.ERROR):
                        break
                    if message.type != aiohttp.WSMsgType.TEXT:
                        continue

                    self._process_message(message.json())

                    # try:
                    #     task = asyncio.create_task(self._process_message(message.json()))
                    # except Exception as e:
                    #     logger.warning(f'can\'t process websocket message: {e}')
                    # else:
                    #     self._background_tasks.add(task)
                    #     task.add_done_callback(self._background_tasks.discard)


                logger.warning('closing websocket connection')
                if self._ws and not self._ws.closed:
                    await self._ws.close()

        except asyncio.CancelledError as e:
            pass

        finally:
            if self._ws and not self._ws.closed:
                await self._ws.close()
            if self._session and not self._session.closed:
                await self._session.close()
            self._clear_requests()


    def _process_message(self, data) -> None:
        logger.debug(f'data: {ujson.dumps(data, indent=2)}')

        if 'method' in data:
            method = data['method']
            params = data['params'][0] if 'params' in data else {}
            self._invoke_callback(method, params)
            return

        if 'id' in data:
            id = data['id']
            if id in self._requests:
                future = self._requests[id]
                future.set_result(data)
                del self._requests[id]
            return


    def _invoke_callback(self, method: str, params: dict) -> None:
        for callback in self._listeners:
            try:
                if iscoroutinefunction(callback):
                    task = asyncio.create_task(callback(method, params))
                else:
                    callback(method, params)
            except Exception as e:
                logger.error(f'got exception during invoke callback "{method}": {e}')
            else:
                if task:
                    self._background_tasks.add(task)
                    task.add_done_callback(self._background_tasks.discard)


    def _clear_requests(self):
        for _, request in self._requests.items():
            logger.debug(f'clearing pending request {request}')
            request.cancel()
        self._requests.clear()
