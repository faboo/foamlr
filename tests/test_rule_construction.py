import pytest
from foamlr import GenerationError, NoMatchException, Token, ReToken
from foamlr.rule import Production, Nonterminal

def test_token():
    rule = Token('a')
    rule = ReToken('[0-9]+', 'integer')


def test_production():
    rule = Token('a') * 'b' * 'c'

    assert isinstance(rule, Production)
    assert 3 == len(rule.symbols)
    assert rule.symbols[0].name == 'a'
    assert rule.symbols[1].name == 'b'
    assert rule.symbols[2].name == 'c'

def test_nonterminal():
    rule = Nonterminal('foo', 'a', 'b')

    assert isinstance(rule, Nonterminal)
    assert 2 == len(rule.productions)
    assert isinstance(rule.productions[0], Production)
    assert isinstance(rule.productions[0].symbols[0], Token)


def test_non_symbol_in_production():
    with pytest.raises(GenerationError):
        Nonterminal('foo', Token('a') * None)
