from lrparser import generate, Nonterminal, Token, EOI
from lrparser.parseTable import ParseTable
from lrparser.parseTableBuilder import ParseTableBuilder, Item

simpleGrammar = Nonterminal('X')
simpleGrammar.fill(
    Token('(') * simpleGrammar * ')',
    Token('(') * ')')

shiftReduceGrammar = Nonterminal('X', Token('a'), Token('a') * 'b')


def test_extractTerminals_recursive():
    pt = ParseTable(simpleGrammar)
    assert '(' == pt.tokens[0].name
    assert ')' == pt.tokens[1].name


def test_expandClosure():
    ptb = ParseTableBuilder(simpleGrammar)
    items = ptb.expandClosure({Item(simpleGrammar.productions[0], 0)})

    assert len(items) == 1


def test_expandClosure_recurse():
    ptb = ParseTableBuilder(simpleGrammar)
    items = ptb.expandClosure({Item(simpleGrammar.productions[0], 1)})

    assert len(items) == 3


def test_table_build_simple():
    ptb = ParseTableBuilder(simpleGrammar)
    pt = ptb.build()

    assert len(pt.tokens) == 3
    assert pt.tokens[2] == EOI()
    assert len(pt.rules) == 2
    assert len(pt.actionTable) == 6
    assert len(pt.gotoTable) == 6
    

def test_table_build_shift_reduce_conflict():
    ptb = ParseTableBuilder(shiftReduceGrammar)
    pt = ptb.build()

    assert len(pt.tokens) == 3
    assert pt.tokens[2] == EOI()
    assert len(pt.rules) == 2
    assert len(pt.actionTable) == 4
    assert len(pt.gotoTable) == 4
