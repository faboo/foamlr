import pytest

from lrparser import NoMatchException, Token, ReToken
from lrparser.state import State


def test_line_number():
    state = State(' \n', "123 - 456\nabc = 12\n")

    assert state.line == 0
    assert state.char == 0

    state._pos = 10
    assert state.line == 1
    assert state.source[0] == 'a'
    assert state.char == 0

    state._pos = 13
    assert state.line == 1
    assert state.source[0] == ' '
    assert state.char == 3


