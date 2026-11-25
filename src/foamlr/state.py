""" Internal state of the parser that is used by Rules
"""
from typing import cast
import re
from .rule import Terminal, Symbol, NoMatchException

class ParseItem:
    """ A parsing symbol """
    def __init__(self, symbol:Symbol, value:object) -> None:
        self.symbol = symbol
        self.value = value

    def __repr__(self) -> str:
        return f'Item({self.symbol}, {self.value})'

class State:
    """ The state of the parser
    """
    def __init__(self, whitespace:str|None, source:str, filename:str) -> None:
        self.fullSource = source
        self.filename = filename
        self._token:ParseItem|None = None
        self._state:list[int] = [0]
        self._stack:list[ParseItem] = []
        self._pos:int = 0
        self._whiteRe = re.compile('['+ re.escape(whitespace) +']+') if whitespace else None

    @property
    def source(self) -> str:
        """ The source string from the current position """
        return self.fullSource[self.pos:]

    @property
    def state(self) -> int:
        """ Current parser state """
        return self._state[-1]

    @property
    def stack(self) -> list:
        """ The symbol stack """
        return self._stack

    @property
    def token(self) -> ParseItem:
        if self._token is None:
            raise TypeError('No token read yet')
        return self._token

    @property
    def symbol(self) -> Symbol:
        return self._stack[-1].symbol

    @property
    def pos(self) -> int:
        """ The current position in the full source """
        return self._pos

    @property
    def line(self) -> int:
        """ The current line we are on in the source """
        return self.fullSource[:self.pos].count('\n') + 1

    @property
    def char(self) -> int:
        """ The current character of the line we are on in the source """
        consumed = self.fullSource[:self.pos]
        return len(consumed.rpartition('\n')[2]) + 1

    def _eatWhite(self) -> re.Match|None:
        if not self._whiteRe:
            return None
        return self._whiteRe.match(self.fullSource, self.pos)

    def consume(self, count:int) -> None:
        """ Consume characters in the source stream. """
        self._pos = self.pos + count

        white = self._eatWhite()
        if white:
            self._pos += len(white[0])

    def pushState(self, stateId:int) -> None:
        """ Set current parser state """
        self._state.append(stateId)

    def popState(self, count:int) -> None:
        self._state = self._state[:-count]

    def pushItem(self, parseItem:ParseItem) -> ParseItem:
        self._stack.append(parseItem)
        return parseItem

    def popItems(self, count:int) -> list[ParseItem]:
        items = self._stack[-count:]
        self._stack = self._stack[:-count]
        return items

    def readToken(self, terminals:list[Terminal]) -> None:
        token:None|str = None
        matched:None|Terminal = None
        value:None|object = None

        for terminal in terminals:
            try:
                possible = terminal.match(self.source)
                if token is None or len(possible) > len(token):
                    token = possible
                    matched = terminal
                    value = terminal.produce(token)
            except NoMatchException:
                pass

        if token is None:
            raise NoMatchException('Expected one of: '+', '.join(
                str(term) for term in sorted(terminals, key=lambda r: r.name)))

        self.consume(len(token))
        self._token = ParseItem(cast(Symbol, matched), value)
