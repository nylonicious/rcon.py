import asyncio
import hashlib
from typing import List, Optional

from loguru import logger

from . import exceptions
from .protocol import Protocol


class Client:
    def __init__(self, ip: str, port: int, password: str, timeout=5.0):
        self.ip = ip
        self.port = port
        self._password = password
        self._timeout = timeout
        self._loop = asyncio.get_event_loop()
        self._protocol: Optional[Protocol] = None

    def _protocol_factory(self):
        return Protocol(self._loop, self._timeout)

    async def connect(self):
        _, self._protocol = await asyncio.wait_for(
            self._loop.create_connection(self._protocol_factory, self.ip, self.port), self._timeout,
        )
        await self._authenticate()
        await self._enable_events()
        logger.debug(f"Successfully connected to {self.ip}:{self.port}")

    async def reconnect(self):
        logger.error(f"Lost connection to {self.ip}:{self.port}")
        while True:
            try:
                await self.connect()
                logger.info(f"Successfully reconnected to {self.ip}:{self.port}")
                break
            except asyncio.TimeoutError:
                await asyncio.sleep(10)
            except OSError as e:
                if e.errno == 101:
                    await asyncio.sleep(10)

    async def send_command(self, words: List[str]) -> List[str]:
        return await self._protocol.send(words)

    async def _authenticate(self):
        hash_request = await self.send_command(["login.hashed"])
        if hash_request[0] != "OK":
            raise exceptions.LoginFailure
        md5_hash = hash_request[1]
        hashed_password = (
            hashlib.md5(bytes.fromhex(md5_hash) + self._password.encode()).hexdigest().upper()
        )
        login_request = await self.send_command(["login.hashed", hashed_password])
        if login_request[0] != "OK":
            raise exceptions.LoginFailure

    async def _enable_events(self):
        r = await self.send_command(["admin.eventsEnabled", "true"])
        if r[0] != "OK":
            pass
