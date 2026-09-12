from lrparser import generate, Nonterminal, Token, ReToken, EOI
from lrparser.parseTable import ParseTable

class Add:
    def __init__(self, left, plus, right) -> None:
        self.left = left
        self.right = right

    def __eq__(self, right) -> bool:
        return self.left == right.left and self.right == right.right

class Group:
    def __init__(self, lp, expr, rp) -> None:
        self.expr = expr

    def __eq__(self, right) -> bool:
        return self.expr == right.expr

arith = Nonterminal('arith')
arith.fill(
    (arith * '+' * arith) @ Add,
    (Token('(') * arith * ')') @ Group,
    ReToken('[0-9]+', 'int')@int)


def test_produce_arithmetic_int():
    parser = generate(arith)
    result = parser.parseString('12')
    assert result == 12

def test_produce_arithmetic_add():
    parser = generate(arith)
    result = parser.parseString('12 + 2')
    assert result == Add(12, '+', 2)

def test_produce_arithmetic_group():
    parser = generate(arith)
    result = parser.parseString('(12 + 2) + (3 + 5)')
    expected = Add(Group('(', Add(12, '+', 2), ')'), '+', Group('(', Add(3, '+', 5), ')'))
    assert result == expected



