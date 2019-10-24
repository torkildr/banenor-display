import aiohttp
import asyncio
import threading

from datetime import datetime
from queue import Queue

class Display():
    def __init__(self, loop, time=2.0, displayUrl=None):
        self.displayUrl = displayUrl
        self.time = time
        self.event_loop = loop
        self._display_loop = None

        if self.displayUrl:
            self._show = self._display
            self._setup = self._display_setup
        else:
            self._show = self._console
            self._setup = lambda: None

    async def _display_lines(self, lines):
        current_line = 0
        await self._display_setup()

        while True:
            if current_line >= len(lines):
                current_line = 0

            text = lines[current_line]

            try:
                await self._show(text)
            except Exception as e:
                print(f"Unable to display: {e}")

            await asyncio.sleep(self.time)

            current_line += 1

    def show(self, lines):
        if self._display_loop:
            self._display_loop.cancel()

        self._display_loop = self.event_loop.create_task(self._display_lines(lines))

        def done(f):
            if f.exception():
                f.print_stack()

        self._display_loop.add_done_callback(done)

    async def _console(self, text):
        print(f"{datetime.now().isoformat()}: {text}")

    async def _display_setup(self):
        async with aiohttp.ClientSession(raise_for_status=True) as s:
            await s.post(f"{self.displayUrl}/scroll", json={
                'arg': 'auto',
            })

    async def _display(self, text):
        async with aiohttp.ClientSession(raise_for_status=True) as s:
            await s.post(f"{self.displayUrl}/text", json={
                'text': text,
                'time': True,
            })
