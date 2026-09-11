from lrparser import NoMatchException, Token, ReToken, Nonterminal, generate

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

def test_parse_shiftreduce_reduce():
    parser = generate(shiftReduceGrammar)
    result = parser.parseString('a')
    assert result == ['a']

def test_parse_shiftreduce_shift():
    parser = generate(shiftReduceGrammar)
    result = parser.parseString('ab')
    assert result == ['a', 'b']
