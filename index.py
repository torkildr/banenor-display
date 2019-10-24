import aiohttp
import asyncio
import json

from datetime import datetime
from pytz import timezone

from banenor import Banenor
from display import Display

async def display_departures(config):
    banenor = Banenor(
        config['station'],
        timezone(config['timezone'])
    )
    display = Display(displayUrl=config['displayUrl'])

    track = config['track']
    previous = None

    while True:
        async for departures in banenor.watch_departures():
            if track in departures:
                departure = departures[track]
                if departure != previous:
                    print(f"{datetime.now().isoformat()}: {departure}")
                    previous = departure
                    display.show(departure)

if __name__ == "__main__":
    with open('config.json') as f:
        config = json.load(f)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(display_departures(config))

