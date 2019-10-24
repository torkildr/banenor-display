import aiohttp
import asyncio
import threading

from datetime import datetime
from queue import Queue

class Display():
    def __init__(self, time=2.0, displayUrl=None):
        self.displayUrl = displayUrl
        self.time = time
        self._display_loop = None

        if self.displayUrl:
            self._show = self._display
        else:
            self._show = self._console

    async def _display_line(self, lines):
        current_line = 0

        while True:
            if current_line >= len(lines):
                current_line = 0

            text = lines[current_line]

            await self._show(text)
            await asyncio.sleep(self.time)

            current_line += 1

    def show(self, lines):
        if self._display_loop:
            self._display_loop.cancel()

        self._display_loop = asyncio.create_task(self._display_line(lines))

    async def _console(self, text):
        print(f"{datetime.now().isoformat()}: {text}")

    async def _display(self, text):
        async with aiohttp.ClientSession(raise_for_status=True) as s:
            await s.post(f"{self.displayUrl}/text", json={
                'text': text,
                'time': True,
            })
            await s.post(f"{self.displayUrl}/scroll", json={
                'arg': 'auto',
            })
