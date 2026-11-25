import pytest

from foamlr import NoMatchException, Token, ReToken
from foamlr.state import State


def test_line_number():
    state = State(' \n', "123 - 456\nabc = 12\n", "file.txt")

    assert state.line == 1
    assert state.char == 1

    state._pos = 10
    assert state.line == 2
    assert state.source[0] == 'a'
    assert state.char == 1

    state._pos = 13
    assert state.line == 2
    assert state.source[0] == ' '
    assert state.char == 4


