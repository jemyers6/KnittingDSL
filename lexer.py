from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

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
    KNIT = 10      # K
    PURL = 11      # P
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
    def __init__(self, input_buffer):
        self.input = input_buffer
        self.line_no = 1
        self.index = 0
        self.tokenList: list[Token] = []
        self.tmp = Token("", TokenType.ERROR, 1)

        # Keyword tables
        self.keyword_map = {
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

        # Stitch operators (case-sensitive)
        self.stitch_op_map = {
            "K": TokenType.KNIT,
            "P": TokenType.PURL,
            "KFB": TokenType.KFB,
            "M1L": TokenType.M1L,
            "M1R": TokenType.M1R,
            "SSK": TokenType.SSK,
            "K2TOG": TokenType.K2TOG,
        }

        # Single-character tokens
        self.single_char = {
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

        # Pre-tokenize 
        tok = self.get_token_main()
        while tok.token_type != TokenType.EOF:
            self.tokenList.append(tok)
            tok = self.get_token_main()
    
    def get_token(self) -> Token:
        if self.index < len(self.tokenList):
            tok = self.tokenList[self.index]
            self.index += 1
            return tok
        else:
            return Token("", TokenType.EOF, self.line_no)
        
    def peek(self, howFar: int) -> Token:
        if howFar <= 0:
            raise ValueError("howFar must be a positive integer")
        peek_index = self.index + howFar - 1
        if peek_index >= len(self.tokenList):
            return Token("", TokenType.EOF, self.line_no)
        return self.tokenList[peek_index]
    
    def skip_space(self) -> bool:
        space_seen = False

        ch = self.input.get_char()
        if ch == "":
            return False

        if ch == "\n":
            self.line_no += 1

        while ch != "" and ch.isspace():
            space_seen = True
            ch = self.input.get_char()
            if ch == "\n":
                self.line_no += 1

        if ch != "":
            self.input.unget_char(ch)
        return space_seen

    def scan_number(self) -> Token:
        ch = self.input.get_char()

        if ch == "" or not ch.isdigit():
            if ch != "":
                self.input.unget_char(ch)
            return Token("", TokenType.ERROR, self.line_no)

        if ch == "0":
            return Token("0", TokenType.NUM, self.line_no)

        lex = []
        while ch != "" and ch.isdigit():
            lex.append(ch)
            ch = self.input.get_char()

        if ch != "":
            self.input.unget_char(ch)

        return Token("".join(lex), TokenType.NUM, self.line_no)

    def scan_id_or_keyword(self) -> Token:
        ch = self.input.get_char()

        if ch == "" or not (ch.isalpha() or ch == "_"):
            if ch != "":
                self.input.unget_char(ch)
            return Token("", TokenType.ERROR, self.line_no)

        lex = []
        while ch != "" and (ch.isalnum() or ch == "_"):
            lex.append(ch)
            ch = self.input.get_char()

        if ch != "":
            self.input.unget_char(ch)

        text = "".join(lex)

        # stitch operators first (K, P, KFB, ...)
        if text in self.stitch_op_map:
            return Token(text, self.stitch_op_map[text], self.line_no)

        # keywords are lowercase in your terminal dictionary; accept case-insensitive
        low = text.lower()
        if low in self.keyword_map:
            return Token(text, self.keyword_map[low], self.line_no)

        return Token(text, TokenType.ID, self.line_no)

    def scan_quoted_string(self) -> Token:
        quote = self.input.get_char()
        if quote not in ("'", '"'):
            if quote != "":
                self.input.unget_char(quote)
            return Token("", TokenType.ERROR, self.line_no)

        lex = [quote]
        while True:
            ch = self.input.get_char()
            if ch == "":
                return Token("".join(lex), TokenType.ERROR, self.line_no)

            lex.append(ch)

            if ch == "\n":
                self.line_no += 1

            if ch == "\\":
                nxt = self.input.get_char()
                if nxt == "":
                    return Token("".join(lex), TokenType.ERROR, self.line_no)
                lex.append(nxt)
                if nxt == "\n":
                    self.line_no += 1
                continue

            if ch == quote:
                break

        return Token("".join(lex), TokenType.QUOTED_STRING, self.line_no)

    def get_token_main(self) -> Token:
        self.skip_space()

        # Prepare default
        self.tmp = Token("", TokenType.EOF, self.line_no)

        ch = self.input.get_char()
        if ch == "":
            return self.tmp

        # Single-character tokens
        if ch in self.single_char:
            return Token(ch, self.single_char[ch], self.line_no)

        # String
        if ch in ("'", '"'):
            self.input.unget_char(ch)
            return self.scan_quoted_string()

        # Number
        if ch.isdigit():
            self.input.unget_char(ch)
            return self.scan_number()

        # Identifier/keyword/stitch-op
        if ch.isalpha() or ch == "_":
            self.input.unget_char(ch)
            return self.scan_id_or_keyword()

        # Unknown
        return Token(ch, TokenType.ERROR, self.line_no)


if __name__ == "__main__":
    import io

    src = io.StringIO("""
    stitch rib = (K 1 P 1) * 5;
    pattern Hat(n); { cast_on n; repeat 3 { K n; } bind_off n; }
    execute(Hat(10));
    print("done");
    """)

    from inputbuf import InputBuffer
    print("IN MAIN", flush=True)
    ib = InputBuffer(src)
    print("BEFORE LEXER INIT", flush=True)
    lexer = Lexer(ib)
    print("AFTER LEXER INIT", flush=True)

    while True:
        tok = lexer.get_token()
        print(tok)
        if tok.token_type == TokenType.EOF:
            break