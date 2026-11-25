import pytest
from foamlr import GenerationError, NoMatchException, Token, ReToken
from foamlr.rule import Production, Nonterminal

def test_simple_token():
    rule = Token('a')

    assert rule.match('a') == 'a'
    with pytest.raises(NoMatchException):
        assert rule.match('b')


def test_simple_re_token():
    rule = ReToken('token', 'a')

    assert rule.match('a') == 'a'
    with pytest.raises(NoMatchException):
        assert rule.match('b')


def test_compound_re_token():
    rule = ReToken('token', '[a-z]+')

    assert rule.match('a') == 'a'
    assert rule.match('b') == 'b'
    assert rule.match('cab') == 'cab'

    with pytest.raises(NoMatchException):
        assert rule.match('8')


def test_exclude_re_token():
    rule = ReToken('token', '[ab]+', 'bb')

    assert rule.match('ab') == 'ab'
    with pytest.raises(NoMatchException):
        assert rule.match('bb')
