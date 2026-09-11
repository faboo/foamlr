from lrparser import NoMatchException, Token, ReToken, Nonterminal, generate

# S -> X$
# X -> ( X )
# X -> ( )

simpleGrammar = Nonterminal('X')
simpleGrammar.fill(
    Token('(') * simpleGrammar * ')',
    Token('(') * ')'
    )

def test_generate_simple():
    parser = generate(simpleGrammar)
    result = parser.parseString('()')
    assert result == ['(', ')']

