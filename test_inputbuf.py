import io
from typing import TextIO

class InputBuffer:
    def __init__(self, input_stream: TextIO):
        self.input_stream = input_stream
        # using stack to store characters to peek or consume later
        self.buffer: list[str] = []

    def get_char(self) -> str:
        if self.buffer:
            return self.buffer.pop()
        else:
            ch = self.input_stream.read(1)
            return ch if ch else '' # return the character read or an empty string if end of file is reached
        
    def unget_char(self, char: str) -> str:
        if char != '':
            self.buffer.append(char) # add the character back to the buffer for future retrieval
        return char 
    
    def unget_string(self, string: str) -> str:
        for char in reversed(string): # reverse the string to maintain correct order when ungetting
            self.unget_char(char) # unget each character back to the buffer
        return string

    def end_of_input(self) -> bool:
        if self.buffer:
            return False # if there are characters in the buffer, we are not at the end of input
        char = self.input_stream.read(1)
        if char == '':
            return True # if reading a character returns an empty string, we are at the end of input
        self.unget_char(char) # put the character back into the buffer
        return False


# ---- TESTS ----

def test_basic_read():
    print("TEST 1: Basic read")
    data = io.StringIO("abc")
    ib = InputBuffer(data)

    result = ""
    while not ib.end_of_input():
        result += ib.get_char()

    print("Expected: abc")
    print("Got     :", result)
    print()


def test_unget_char():
    print("TEST 2: Unget single char")
    data = io.StringIO("abc")
    ib = InputBuffer(data)

    ch1 = ib.get_char()  # 'a'
    ib.unget_char(ch1)
    ch2 = ib.get_char()

    print("Expected: a")
    print("Got     :", ch2)
    print()


def test_unget_string():
    print("TEST 3: Unget string")
    data = io.StringIO("xyz")
    ib = InputBuffer(data)

    ib.unget_string("abc")

    result = ""
    while not ib.end_of_input():
        result += ib.get_char()

    print("Expected: abcxyz")
    print("Got     :", result)
    print()


def test_interleaving():
    print("TEST 4: Interleaving get/unget")
    data = io.StringIO("123")
    ib = InputBuffer(data)

    print("Reading first char:", ib.get_char())  # 1
    ib.unget_string("AB")
    print("Next chars should be A B 2 3")

    while not ib.end_of_input():
        print(ib.get_char(), end=" ")

    print("\n")


def test_eof_behavior():
    print("TEST 5: EOF behavior")
    data = io.StringIO("hi")
    ib = InputBuffer(data)

    print("h:", ib.get_char())
    print("i:", ib.get_char())
    print("EOF should be empty string ->", repr(ib.get_char()))
    print("end_of_input():", ib.end_of_input())
    print()


# ---- RUN ALL TESTS ----

if __name__ == "__main__":
    test_basic_read()
    test_unget_char()
    test_unget_string()
    test_interleaving()
    test_eof_behavior()
