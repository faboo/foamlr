import pytest
from lrparser import NoMatchException, Token, R, Nonterminal, P, generate, CompilationError

# S -> X$
# X -> ( X )
# X -> ( )

def test_generate_simple():
    grammar = Nonterminal('X')
    grammar.fill(
        Token('(') * grammar * ')',
        Token('(') * ')'
        )

    parser = generate(grammar)
    

def test_anonymous_nonterminal():
    grammar = Nonterminal('X',
        P*'(' * (R('num', '[0-3]') | R('let', '[a-z]') * '!' | '@') * ')',
        P*'(' * ')',
        )

    parser = generate(grammar)
    parser.parseString('(0)')
    parser.parseString('(a!)')
    parser.parseString('(@)')
    parser.parseString('()')

    with pytest.raises(CompilationError) as exinfo:
        parser.parseString('(a)')
    assert exinfo.value.msg == 'Expected one of: !'
