""" Internal state of the parser that is used by Rules
"""
import re

class State:
    """ The state of the parser
    """
    class Internal:
        """ Pushable state
        """
        def __init__(self) -> None:
            self.pos = 0
            self.stackLength = 0
        
    class ParseItem:
        """ A parse stack item
        """
        def __init__(self, symbol:int, value:object) -> None:
            self.symbol = symbol
            self.value = value

    def __init__(self, whitespace:str, source:str) -> None:
        self.fullSource = source
        self._state = [self.Internal()]
        self._stack:list[ParseItem] = []
        self._whiteRe = re.compile('['+ re.escape(whitespace) +']+')

    @property
    def source(self) -> str:
        """ The source string from the current position """
        return self.fullSource[self.pos:]

    @property
    def stack(self) -> list:
        """ The symbol stack """
        return self._stack

    @property
    def pos(self) -> int:
        """ The current position in the full source """
        return self._state[-1].pos

    @property
    def line(self) -> int:
        """ The current line we are on in the source """
        return self.fullSource[:self.pos].count('\n')

    @property
    def char(self) -> int:
        """ The current character of the line we are on in the source """
        consumed = self.fullSource[:self.pos]
        return len(consumed.rpartition('\n')[2])

    def consume(self, count:int) -> None:
        """ Consume characters in the source stream. """
        self._state[-1].pos = self.pos + count

        white = self._whiteRe.match(self.fullSource, self.pos)
        if white:
            self._state[-1].pos += len(white[0])

    def push(self) -> None:
        """ Push state """
        state = self.Internal()
        state.pos = self.pos
        state.stackLength = len(self.stack)
        self._state.append(state)

    def pop(self) -> None:
        """ Return to the state before the last push """
        self._stack = self._stack[:self._state[-1].stackLength]
        self._state.pop()

