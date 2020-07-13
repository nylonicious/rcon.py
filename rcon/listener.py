import asyncio

from loguru import logger

from . import exceptions
from .client import Client


class Listener(Client):
    def __init__(self, ip, port, password):
        super().__init__(ip, port, password)

    def run(self):
        try:
            self._loop.run_until_complete(self.main())
        except KeyboardInterrupt:
            raise SystemExit

    async def main(self):
        await self.connect()
        tasks = [
            asyncio.create_task(self.server_event_loop()),
            asyncio.create_task(self.server_info_loop()),
        ]
        await asyncio.gather(*tasks)

    async def server_event_loop(self):
        while True:
            try:
                event = await self._protocol.listen()
                logger.debug(event)
            except asyncio.TimeoutError:
                pass

    async def server_info_loop(self):
        while True:
            try:
                server_info = await self.send_command(["serverInfo"])  # noqa
                await asyncio.sleep(10)
            except exceptions.RCONException:
                await self.reconnect()
