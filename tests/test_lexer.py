import pytest

from lrparser import NoMatchException, Token, ReToken
from lrparser.state import State


def test_line_number():
    state = State(' \n', "123 - 456\nabc = 12\n")

    assert state.line == 0
    assert state.char == 0

    state._state[-1].pos = 10
    assert state.line == 1
    assert state.source[0] == 'a'
    assert state.char == 0

    state._state[-1].pos = 13
    assert state.line == 1
    assert state.source[0] == ' '
    assert state.char == 3


def test_const_match():
    state = State(' \n', "+ 12")
    token = Token('+')

    assert '+' == token.match(state)
    assert state.source == '12'
    assert state.pos == 2
    assert state.line == 0
    assert state.char == 2
    assert 1 == len(state._state)


def test_const_fail():
    state = State(' \n', "+ 12")
    token = Token('@')

    with pytest.raises(NoMatchException):
        token.match(state)
    assert state.source == '+ 12'
    assert state.pos == 0
    assert state.line == 0
    assert state.char == 0
    assert 1 == len(state._state)


def test_regex_match():
    state = State(' \n', "foo = 12")
    token = ReToken('[a-z]+')

    assert 'foo' == token.match(state)
    assert state.source == '= 12'
    assert state.pos == 4
    assert state.line == 0
    assert state.char == 4
    assert 1 == len(state._state)


def test_regex_fail():
    state = State(' \n', "___ = 12")
    token = ReToken('[a-z]+')

    with pytest.raises(NoMatchException):
        token.match(state)
    assert state.source == '___ = 12'
    assert state.pos == 0
    assert state.line == 0
    assert state.char == 0
    assert 1 == len(state._state)
