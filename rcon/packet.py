from __future__ import annotations

import struct
from typing import List, Tuple


class Packet:
    def __init__(self, sequence: int, is_response: bool, is_from_server: bool, words: List[str]):
        self.sequence = sequence
        self.is_response = is_response
        self.is_from_server = is_from_server
        self.words = words

    @classmethod
    def decode(cls, buffer: bytearray) -> Tuple[Packet, int]:
        header = _decode_uint32(buffer[0:4])
        sequence = header & 0x3FFFFFFF
        is_response = header & 0x40000000 > 0
        is_from_server = header & 0x80000000 > 0
        size = _decode_uint32(buffer[4:8])
        offset = 12
        words: List[str] = []
        while offset < size:
            word_length = _decode_uint32(buffer[offset : (offset + 4)])
            word = buffer[(offset + 4) : (offset + 4 + word_length)]
            words.append(word.decode())
            offset += word_length + 5
        return cls(sequence, is_response, is_from_server, words), size

    def encode(self) -> bytes:
        size = 12
        encoded_words = b""
        for word in self.words:
            word = str(word)
            encoded_words += _encode_uint32(len(word)) + word.encode() + b"\x00"
            size += len(word) + 5
        header = self.sequence & 0x3FFFFFFF
        if self.is_response:
            header += 0x40000000
        if self.is_from_server:
            header += 0x80000000
        return (
            _encode_uint32(header)
            + _encode_uint32(size)
            + _encode_uint32(len(self.words))
            + encoded_words
        )

    @staticmethod
    def is_complete(buffer: bytearray) -> bool:
        if len(buffer) > 8 and len(buffer) >= _decode_uint32(buffer[4:8]):
            return True
        return False


def _encode_uint32(integer: int) -> bytes:
    return struct.pack("<I", integer)


def _decode_uint32(buffer: bytes) -> int:
    return struct.unpack("<I", buffer)[0]
