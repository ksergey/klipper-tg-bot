import logging
import asyncio

from inspect import iscoroutinefunction
from typing import Optional, Callable

logger = logging.getLogger(__name__)


class Printer:
    PROGRESS_STEP_SIZE = 0.05

    def __init__(self, data: Optional[dict] = None) -> None:
        self.data = data or {}
        self.state = 'disconnected'
        self.progress = None
        self._listeners = {}


    def add_listener(self, event: str, callback: Callable) -> None:
        if event in self._listeners:
            self._listeners[event].append(callback)
        else:
            self._listeners[event] = [callback]


    def update(self, data: dict) -> None:
        for entry in data:
            if entry == 'configfile':
                continue
            if entry not in self.data:
                self.data[entry] = {}
            self.data[entry].update(data[entry])

        if 'print_stats' in data:
            if 'state' in data['print_stats']:
                self.change_state(data['print_stats']['state'])

        if 'display_status' in data:
            self._process_progress_update()

            if 'message' in data['display_status'] and data['display_status']['message'] is not None:
                self._process_message()


    def change_state(self, state: str) -> None:
        if self.state != state:
            self.state = state
            self._invoke_callback('state_changed', self)


    def reset(self) -> None:
        self.data = {}
        self.state = 'disconnected'
        self.progress = None


    def _process_message(self) -> None:
        self._invoke_callback('message', self)


    def _process_progress_update(self) -> None:
        progress = int(self.data['display_status']['progress'] / Printer.PROGRESS_STEP_SIZE) * Printer.PROGRESS_STEP_SIZE

        if self.progress is None or self.progress > progress:
            self.progress = progress
        if self.state != 'printing':
            return
        if self.progress < progress:
            self.progress = progress
            self._invoke_callback('progress_changed', self)


    def _invoke_callback(self, event: str, *args, **kwargs) -> None:
        if event not in self._listeners:
            return

        async def invoke() -> None:
            for callback in self._listeners[event]:
                try:
                    if iscoroutinefunction(callback):
                        await callback(*args, **kwargs)
                    else:
                        callback(*args, **kwargs)
                except Exception as e:
                    logger.error(f'got exception during invoke callback ({e})')

        asyncio.ensure_future(invoke())
