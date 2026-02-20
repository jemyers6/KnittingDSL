from collections import deque 
from typing import TextIO # libary for handling textual input/output operations

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