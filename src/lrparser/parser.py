""" Genearte a new parser """

from io import IOBase
from .rule import Rule, Nonterminal, Production
from .state import State
from .parseTableBuilder import ParseTableBuilder
from .parseTable import DFAState

class CompilationError(Exception):
    """ A compilation error """


class Parser:
    """ The reusable parser """
    def __init__(self, parseTable:list[DFAState], whitespace:str|None=' \t\n') -> None:
        self.whitespace = whitespace
        self.parseTable = parseTable

    def setWhite(self, whitespace:str|None) -> None:
        """ Set the whitespace characters """
        self.whitespace = whitespace

    def parseString(self, source:str) -> object:
        """ Parse a source string """
        state = State(self.whitespace, source)

    def parseFile(self, file:str|IOBase) -> object:
        """ Parse a source file """
        if isinstance(file, IOBase):
            stream = file
        else:
            stream = open(file, 'r', encoding='utf-8')

        with stream:
            source = stream.read()
            return self.parseString(source)


def _flattenRules(productions:dict[int,list[Production]], grammar:Rule) -> None:
    """ Transform arbitrary nested productions into basic production items:

    User writes:   expr = num + '*' + expr | num
    Becomes:       E' → expr (start symbol)
                   expr → num '*' expr
                   expr → num
                   num  → RE[0-9]+

    Incidentally resolve Delayeds
    """

    # Add every top-level production and recurse into each one
    if isinstance(grammar, Nonterminal):
        productions[grammar.ruleId] = grammar.productions

        for production in grammar.productions:
            _flattenRules(productions, production)

    # Check each symbol for nonterminals and recurse if we haven't added it already (avoiding cycles)
    elif isinstance(grammar, Production):
        for symbol in grammar.symbols:
            if isinstance(symbol, Nonterminal) and symbol.ruleId not in productions:
                _flattenRules(productions, symbol)



def generate(grammar:Nonterminal, whitespace=' \t\n') -> Parser:
    """ Create a new parser from a grammar """
    #productions:dict[int,list[Nonterminal]]  = \
    #    { 0: [grammar]
    #    }

    #_flattenRules(productions, grammar)
    tableBuilder = ParseTableBuilder(grammar)
    table = tableBuilder.build()

    parser = Parser(table, whitespace)

    return parser

