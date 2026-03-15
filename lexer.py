from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from enum import Enum
from typing import Deque


class TokenType(Enum):
    EOF = 0

    # keywords
    STITCH = 1
    PATTERN = 2
    REPEAT = 3
    WORK = 4
    EXECUTE = 5
    PRINT = 6
    CAST_ON = 7
    BIND_OFF = 8
    FILL = 9

    # stitch operators
    KNIT = 10
    PURL = 11
    KFB = 12
    M1L = 13
    M1R = 14
    SSK = 15
    K2TOG = 16

    # literals
    ID = 20
    NUM = 21
    QUOTED_STRING = 22

    # punctuation / operators
    SEMICOLON = 30
    LCBRAC = 31
    RCBRAC = 32
    LPAREN = 33
    RPAREN = 34
    LBRAC = 35
    RBRAC = 36
    COMMA = 37
    EQUALS = 38
    PLUS = 39
    MINUS = 40
    MULT = 41
    DIVIDE = 42

    ERROR = 99


@dataclass
class Token:
    lexeme: str
    token_type: TokenType
    line_no: int

    def print(self) -> None:
        print(f"{self.token_type.name:12}  {self.lexeme!r:16}  line={self.line_no}")


class Lexer:
    KEYWORDS = {
        "stitch": TokenType.STITCH,
        "pattern": TokenType.PATTERN,
        "repeat": TokenType.REPEAT,
        "work": TokenType.WORK,
        "execute": TokenType.EXECUTE,
        "print": TokenType.PRINT,
        "cast_on": TokenType.CAST_ON,
        "bind_off": TokenType.BIND_OFF,
        "fill": TokenType.FILL,
    }

    STITCH_OPERATORS = {
        "K": TokenType.KNIT,
        "P": TokenType.PURL,
        "KFB": TokenType.KFB,
        "M1L": TokenType.M1L,
        "M1R": TokenType.M1R,
        "SSK": TokenType.SSK,
        "K2TOG": TokenType.K2TOG,
    }

    SINGLE_CHAR_TOKENS = {
        ";": TokenType.SEMICOLON,
        "+": TokenType.PLUS,
        "-": TokenType.MINUS,
        "*": TokenType.MULT,
        "/": TokenType.DIVIDE,
        "=": TokenType.EQUALS,
        "(": TokenType.LPAREN,
        ")": TokenType.RPAREN,
        "[": TokenType.LBRAC,
        "]": TokenType.RBRAC,
        "{": TokenType.LCBRAC,
        "}": TokenType.RCBRAC,
        ",": TokenType.COMMA,
    }

    def __init__(self, input_buffer):
        self.input = input_buffer
        self.line_no = 1
        self.lookahead: Deque[Token] = deque()

    def next_token(self) -> Token:
        if self.lookahead:
            return self.lookahead.popleft()
        return self._scan_token()

    def get_token(self) -> Token:
        return self.next_token()

    def peek(self, distance: int = 1) -> Token:
        if distance <= 0:
            raise ValueError("distance must be a positive integer")

        while len(self.lookahead) < distance:
            self.lookahead.append(self._scan_token())

        return self.lookahead[distance - 1]

    def _consume_char(self) -> str:
        ch = self.input.read_char()
        if ch == "\n":
            self.line_no += 1
        return ch

    def _peek_char(self) -> str:
        return self.input.peek_char()

    def _skip_whitespace(self) -> None:
        while True:
            ch = self._peek_char()
            if ch == "" or not ch.isspace():
                return
            self._consume_char()

    def _read_number(self) -> Token:
        start_line = self.line_no
        digits: list[str] = []

        first = self._consume_char()
        digits.append(first)

        if first == "0":
            return Token("0", TokenType.NUM, start_line)

        while self._peek_char().isdigit():
            digits.append(self._consume_char())

        return Token("".join(digits), TokenType.NUM, start_line)

    def _classify_identifier(self, text: str) -> TokenType:
        if text in self.STITCH_OPERATORS:
            return self.STITCH_OPERATORS[text]

        keyword_type = self.KEYWORDS.get(text.lower())
        if keyword_type is not None:
            return keyword_type

        return TokenType.ID

    def _read_identifier(self) -> Token:
        start_line = self.line_no
        chars: list[str] = [self._consume_char()]

        while True:
            ch = self._peek_char()
            if not (ch.isalnum() or ch == "_"):
                break
            chars.append(self._consume_char())

        text = "".join(chars)
        return Token(text, self._classify_identifier(text), start_line)

    def _read_string_literal(self) -> Token:
        start_line = self.line_no
        quote = self._consume_char()
        chars = [quote]

        while True:
            ch = self._consume_char()
            if ch == "":
                return Token("".join(chars), TokenType.ERROR, start_line)

            chars.append(ch)

            if ch == "\\":
                escaped = self._consume_char()
                if escaped == "":
                    return Token("".join(chars), TokenType.ERROR, start_line)
                chars.append(escaped)
                continue

            if ch == quote:
                return Token("".join(chars), TokenType.QUOTED_STRING, start_line)

    def _scan_token(self) -> Token:
        self._skip_whitespace()
        ch = self._peek_char()

        if ch == "":
            return Token("", TokenType.EOF, self.line_no)

        if ch in self.SINGLE_CHAR_TOKENS:
            token_char = self._consume_char()
            return Token(token_char, self.SINGLE_CHAR_TOKENS[token_char], self.line_no)

        if ch in ("'", '"'):
            return self._read_string_literal()

        if ch.isdigit():
            return self._read_number()

        if ch.isalpha() or ch == "_":
            return self._read_identifier()

        bad_char = self._consume_char()
        return Token(bad_char, TokenType.ERROR, self.line_no)


if __name__ == "__main__":
    import io
    from input_buffer import InputBuffer

    src = io.StringIO(
        """
        stitch rib = (K 1, P 1) * 5;
        pattern Hat(n) { cast_on n; repeat 3 { K 1, P 1; } bind_off n; }
        execute(Hat(10));
        print(\"done\");
        """
    )

    lexer = Lexer(InputBuffer(src))
    while True:
        tok = lexer.next_token()
        tok.print()
        if tok.token_type == TokenType.EOF:
            break
