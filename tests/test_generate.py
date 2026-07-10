from lrparser import NoMatchException, Token, ReToken, Nonterminal, generate

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
    

