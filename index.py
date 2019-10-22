import aiohttp
import asyncio
import json

from datetime import datetime
from jsonrpc import JSONRPCResponseManager, dispatcher
from pytz import timezone
from typing import Callable
from urllib.parse import urlencode

class Banenor(object):
    def __init__(self, station, tz):
        self.station = station
        self.timezone = tz
        self.formatted_departures = {}

        base_url = "http://rtd.opm.jbv.no:8080/web_client/ws"
        params = {
            "display": "rtd",
            "hideNotice": "false",
            "id": f"{self.station}/Departure",
            "noPassengerDisplay": "false",
            "wrapperName": "landscape",
        }
        self.ws_url = f"{base_url}?{urlencode(params)}"

    async def _handle_messages(self, ws):
        dispatcher['update'] = self.update
        dispatcher['keepAlive'] = lambda timestamp: None
        dispatcher['loadUrl'] = lambda urls: None

        async for msg in ws:
            res = JSONRPCResponseManager.handle(msg.data, dispatcher)
            await ws.send_str(res.json)
            yield self.formatted_departures

    async def watch_departures(self):
        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(self.ws_url) as ws:
                async for message in self._handle_messages(ws):
                    yield message

    def update(self, data):
        date_format = "%Y-%m-%dT%H:%M:%S%z"
        tracks = {}
        for departure in data["departures"]:
            track = departure['track']
            if track not in tracks:
                tracks[track] = []

            if 'remarks' in departure:
                deviation = next((True for x in departure['remarks'] if x['type'] == "DEVIATION"), False)
            else:
                deviation = False

            tracks[track].append({
                'line': departure['line'] if 'line' in departure else '',
                'to': departure['destination']['default'],
                'scheduled': datetime.strptime(departure['scheduled'], date_format),
                'expected': datetime.strptime(departure['expected'], date_format),
                'deviation': deviation,
            })

        def format_expected(dep):
            diff_minutes = (dep['expected'] - dep['scheduled']).seconds // 60
            formatted = dep['expected'].astimezone(self.timezone).strftime('%H:%M')
            deviation = '(!)' if dep['deviation'] else ''
            formatted = f"{formatted}{deviation}"

            if diff_minutes > 0:
                return f"{formatted} (+{diff_minutes} min)"
            return formatted

        self.formatted_departures = {x: [] for x in tracks.keys()}
        for track, departures in tracks.items():
            trains = [
                f"{x['to']} {format_expected(x)}"
                for x in departures[:2]
            ]
            self.formatted_departures[track] = ', '.join(trains)

async def display_departures(config):
    banenor = Banenor(
        config['station'],
        timezone(config['timezone'])
    )
    track = config['track']

    previous = None

    while True:
        async for departures in banenor.watch_departures():
            if track in departures:
                departure = departures[track]
                if departure != previous:
                    print(f"{datetime.now().isoformat()}: {departure}")
                    previous = departure

if __name__ == "__main__":
    with open('config.json') as f:
        config = json.load(f)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(display_departures(config))
