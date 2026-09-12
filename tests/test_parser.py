import pytest
from lrparser import Token, ReToken, Nonterminal, generate, CompilationError

# S -> X$
# X -> ( X )
# X -> ( )

simpleGrammar = Nonterminal('X')
simpleGrammar.fill(
    Token('(') * simpleGrammar * ')',
    Token('(') * ')'
    )

shiftReduceGrammar = Nonterminal('X', Token('a'), Token('a') * 'b')

def test_parse_simple():
    parser = generate(simpleGrammar)
    result = parser.parseString('()')
    assert result == ['(', ')']


def test_parse_simple_recurse():
    parser = generate(simpleGrammar)
    result = parser.parseString('( () )')
    assert result == ['(', ['(', ')'], ')']

def test_parse_simple_error():
    parser = generate(simpleGrammar)

    with pytest.raises(CompilationError) as exinfo:
        result = parser.parseString('[ )')
    assert exinfo.value.msg == 'Expected one of: ('
    assert exinfo.value.line == 1
    assert exinfo.value.char == 1

    with pytest.raises(CompilationError) as exinfo:
        result = parser.parseString('( ]')
    assert exinfo.value.msg == 'Expected one of: (, )'
    assert exinfo.value.line == 1
    assert exinfo.value.char == 3

def test_parse_shiftreduce_reduce():
    parser = generate(shiftReduceGrammar)
    result = parser.parseString('a')
    assert result == 'a'

def test_parse_shiftreduce_shift():
    parser = generate(shiftReduceGrammar)
    result = parser.parseString('ab')
    assert result == ['a', 'b']


