from __future__ import annotations

from typing import TextIO


class InputBuffer:

    def __init__(self, input_stream: TextIO):
        self.input_stream = input_stream
        self._pushback: list[str] = []

    def read_char(self) -> str:
        if self._pushback:
            return self._pushback.pop()

        ch = self.input_stream.read(1)
        return ch if ch else ""

    def peek_char(self) -> str:
        ch = self.read_char()
        if ch:
            self._pushback.append(ch)
        return ch

    def push_back(self, text: str) -> None:
        for ch in reversed(text):
            if ch:
                self._pushback.append(ch)

    def eof(self) -> bool:
        return self.peek_char() == ""