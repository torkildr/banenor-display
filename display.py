import aiohttp
import asyncio
import threading

from datetime import datetime
from queue import Queue

class Display():
    def __init__(self, time=2.0, displayUrl=None):
        self.displayUrl = displayUrl
        self.time = time
        self.loop = asyncio.new_event_loop()

        if self.displayUrl:
            self._show = self._display
        else:
            self._show = self._console

    def _set_timer(self, time):
        timer = threading.Timer(time, self._display_line)
        timer.start()

    def _display_line(self):
        if self.current_line >= len(self.lines):
            self.current_line = 0

        text = self.lines[self.current_line]

        self.loop.run_until_complete(self._show(text))

        self.current_line += 1
        self._set_timer(self.time)

    def show(self, lines):
        self.lines = lines
        self.current_line = 0
        self._set_timer(0)

    async def _console(self, text):
        print(f"{datetime.now().isoformat()}: {text}")

    async def _display(self, text):
        async with aiohttp.ClientSession(raise_for_status=True) as s:
            await s.post(f"{self.displayUrl}/text", json={
                'text': text,
                'time': True,
            })
            await s.post(f"{self.displayUrl}/scroll", json={
                'arg': 'none',
            })
