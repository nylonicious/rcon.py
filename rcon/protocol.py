import asyncio
from typing import Dict, List

from . import exceptions
from .packet import Packet


class Protocol(asyncio.Protocol):
    def __init__(self, loop, timeout: float):
        self.loop = loop
        self.timeout = timeout
        self.transport = None
        self.client_sequence = 0
        self.receive_buffer = bytearray()
        self.requests: Dict[int, asyncio.Future] = {}
        self.events = asyncio.Queue()

    async def send(self, words) -> List[str]:
        request = Packet(self.client_sequence, False, False, words)
        if self.transport.is_closing():
            raise exceptions.RCONException
        self.transport.write(request.encode())
        sequence_to_match = self.client_sequence
        self.client_sequence += 1
        return await self._recv(sequence_to_match)

    async def listen(self) -> List[str]:
        return await asyncio.wait_for(self.events.get(), self.timeout)

    async def _recv(self, sequence: int) -> List[str]:
        self.requests[sequence] = self.loop.create_future()
        try:
            return await asyncio.wait_for(self.requests[sequence], self.timeout)
        except asyncio.TimeoutError:
            # we reached timeout waiting for a response from the server, cancel the future
            self.requests[sequence].cancel()
            raise exceptions.RCONException
        finally:
            del self.requests[sequence]

    def _parse(self):
        while Packet.is_complete(self.receive_buffer):
            packet, packet_size = Packet.decode(self.receive_buffer)
            # remove bytes we already processed and decoded into Packet
            del self.receive_buffer[:packet_size]
            if packet.is_response and packet.sequence in self.requests:
                # set result to a request as soon it becomes available
                self.requests[packet.sequence].set_result(packet.words)
            elif not packet.is_response and packet.is_from_server:
                # put event packet into queue
                self.events.put_nowait(packet.words)
                # acknowledge that we received event packet by sending it back
                response = Packet(packet.sequence, True, True, packet.words)
                if not self.transport.is_closing():
                    self.transport.write(response.encode())

    def connection_made(self, transport):
        self.transport = transport

    def data_received(self, data):
        self.receive_buffer.extend(data)
        self._parse()

    def connection_lost(self, exc):
        pass
