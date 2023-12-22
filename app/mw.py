import asyncio
import aiohttp
import ujson
import logging

from typing import Optional, Callable

logger = logging.getLogger(__name__)


class MoonrakerSession:
    DEFAULT_PORT = 7125
    RECONNECT_INTERVAL = 10.0
    HEARTBEAT_INTERVAL = 5.0

    def __init__(
        self,
        endpoint: str,
        loop: Optional[asyncio.AbstractEventLoop] = None,
    ):
        # construct connection address
        if ':' in endpoint:
            host, port = endpoint.split(':')
        else:
            host, port = (endpoint, str(MoonrakerSession.DEFAULT_PORT))

        self._endpoint = f'{host}:{port}'
        self._loop = loop or asyncio.get_event_loop()
        self._session = None
        self._socket = None
        self._loop_task = None
        self._callbacks = set()
        self._requests = dict()
        self._next_req_id = 1


    async def start(self) -> None:
        if self._loop_task and not self._loop_task.done():
            raise Exception('moonraker session already started')
        self._loop_task = asyncio.create_task(self._session_loop())


    async def stop(self) -> None:
        if not self._loop_task or self._loop_task.done():
            return
        self._loop_task.cancel()
        await self._loop_task


    def add_callback(self, callback: Callable):
        self._callbacks.add(callback)


    def remove_callback(self, callback: Callable):
        self._callbacks.discard(callback)


    # send async request
    async def request(self, method: str, params: Optional[dict] = None) -> dict:
        future = asyncio.Future()
        id = self._get_req_id()
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
        if self._socket is None or self._socket.closed:
            raise RuntimeError('moonraker not connected')

        if id is None:
            id = self._get_req_id()

        request_str = ujson.dumps({
            'jsonrpc': '2.0',
            'method': method,
            'params': params or {},
            'id': id
        })
        logger.debug(f'send_request: {request_str}')

        await self._socket.send_str(request_str)


    def _get_req_id(self) -> int:
        value = self._next_req_id
        self._next_req_id += 1
        return value


    async def _session_loop(self):
        async def get_oneshot_token() -> str:
            url = f'http://{self._endpoint}/access/oneshot_token'
            async with self._session.get(url) as response:
                if response.status != 200:
                    raise Exception('unable to get oneshot token')
                data = await response.json()
                return data['result']

        try:
            # next connect attempt time
            next_connect_time = 0.0

            while True:
                now = self._loop.time()
                if next_connect_time > now:
                    await asyncio.sleep(next_connect_time - now)
                next_connect_time = self._loop.time() + MoonrakerSession.RECONNECT_INTERVAL

                self._clear_requests()

                try:
                    if not self._session or self._session.closed:
                        self._session = aiohttp.ClientSession()

                    oneshot_token = await get_oneshot_token()

                    if not self._socket or self._socket.closed:
                        url = f'ws://{self._endpoint}/websocket?token={oneshot_token}'
                        self._socket = await self._session.ws_connect(url, heartbeat=MoonrakerSession.HEARTBEAT_INTERVAL)
                        logger.info(f'connected to {url}')

                except Exception as e:
                    logger.error(f'failed to establish connection ({e})')
                    continue

                self._invoke_callback('connected', {})

                async for message in self._socket:
                    if message.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.CLOSE, aiohttp.WSMsgType.ERROR):
                        break
                    if message.type == aiohttp.WSMsgType.TEXT:
                        await self._process_message(message.json())

                logger.warning('closing websocket connection')
                if self._socket and not self._socket.closed:
                    await self._socket.close()

        except asyncio.CancelledError as e:
            pass

        finally:
            if self._socket and not self._socket.closed:
                logger.info("closing socket")
                await self._socket.close()
            if self._session and not self._session.closed:
                logger.info("closing session")
                await self._session.close()
            self._clear_requests()


    async def _process_message(self, data):
        if 'method' in data:
            method = data['method']
            params = data['params'][0] if 'params' in data else {}
            self._invoke_callback(method, params)
            return

        if 'id' in data:
            id = data['id']
            if id in self._requests:
                future = self._requests[id]
                del self._requests[id]
                future.set_result(data)
            return


    def _clear_requests(self):
        for _, request in self._requests.items():
            logger.debug(f'clearing pending request {request}')
            request.cancel()
        self._requests.clear()


    def _invoke_callback(self, method, params):
        for callback in list(self._callbacks):
            try:
                callback(method, params)
            except Exception as e:
                logger.warning(f'failed to invoke callback: {e}')


async def main():
    moonraker = MoonrakerSession('zbolt.home.local')

    def on_data(method, params):
        print(f'{method}: {params}')

    moonraker.add_callback(on_data)

    await moonraker.start()
    await asyncio.sleep(5)

    moonraker.remove_callback(on_data)

    await asyncio.sleep(100)

if __name__ == '__main__':
    try:
        logging.basicConfig(
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            level=logging.DEBUG
        )

        asyncio.run(main())

    except (KeyboardInterrupt, SystemExit):
        logger.info('stopped!')
