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
        self._loop_task = asyncio.create_task(self._session_loop())

    def __del__(self):
        if self._loop_task and not self._loop_task.done():
            try:
                if self._loop.is_running():
                    self._loop_task.cancel()
                    self._loop.ensure_future(self._loop_task)
                else:
                    self._loop.run_until_complete(self._loop_task)
            except e:
                logger.error(f'destructor err: {e}')


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

                # asyncio.ensure_future(self._invoke_callback('connected', {}), loop=self._loop)

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

    async def _process_message(self, msg):
        logger.debug(f'message: {msg}')
        pass

async def main():
    moonraker = MoonrakerSession('zbolt.home.local')
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
