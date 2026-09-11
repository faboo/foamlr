""" Genearte a new parser """

from typing import cast
from io import IOBase
from .rule import Nonterminal, Terminal, Symbol, NoMatchException
from .state import State, ParseItem
from .parseTableBuilder import ParseTableBuilder
from .parseTable import ParseTable, Shift, Reduce, Accept

class CompilationError(Exception):
    """ A compilation error """


class Parser:
    """ The reusable parser """
    def __init__(self, parseTable:ParseTable, whitespace:str|None=' \t\n') -> None:
        self.whitespace = whitespace
        self.parseTable = parseTable

    def setWhite(self, whitespace:str|None) -> None:
        """ Set the whitespace characters """
        self.whitespace = whitespace

    def expectedTokens(self, state:State) -> list[Terminal]:
        return list(self.parseTable.actionTable[state.state].keys())

    def readToken(self, state:State) -> None:
        terminals = self.expectedTokens(state)
        token:None|str = None
        matched:None|Terminal = None
        value:None|object = None

        for terminal in terminals:
            try:
                possible = terminal.match(state.source)
                if token is None or len(possible) > len(token):
                    token = possible
                    matched = terminal
                    value = terminal.produce(token)
            except NoMatchException:
                pass

        if token is None:
            raise NoMatchException('Expected one of: '+', '.join(str(term) for term in terminals))
            
        state.consume(len(token))
        state.pushItem(ParseItem(cast(Symbol, matched), value))

    def shift(self, state:State, action:Shift) -> None:
        state.pushState(action.to)
        self.readToken(state)

    def reduce(self, state:State, action:Reduce) -> None:
        argCount = len(action.production.symbols)
        argItems = state.popItems(argCount)
        state.popState(argCount)

        for idx in range(argCount):
            symbol = action.production.symbols[idx]
            arg = argItems[idx]

            if symbol != arg.symbol:
                raise CompilationError(f'Expected {action.production.nonterminal}')

        result = action.production.produce([item.value for item in argItems])
        state.pushItem(ParseItem(action.production.nonterminal, result))

        gotos = self.parseTable.gotoTable[state.state]
        if state.symbol not in gotos:
            raise CompilationError(f'Unexpected {state.symbol}')

        state.pushState(gotos[state.symbol])

    def parseString(self, source:str) -> object:
        """ Parse a source string """
        state = State(self.whitespace, source)
        parsing = True

        self.readToken(state)

        while parsing:
            parseItem = state.stack[-1]
            print(f'\nCurrent State: {state.state}')
            print(f'Symbol: {parseItem}')

            actions = self.parseTable.actionTable[state.state]
            #gotos = self.parseTable.gotoTable[state.state]
            #print(f'Gotos: {gotos}')

            if parseItem.symbol in actions:
                action = actions[parseItem.symbol]
                print(f'Action: {action}')

                if isinstance(action, Accept):
                    parsing = False
                elif isinstance(action, Shift):
                    self.shift(state, action)
                elif isinstance(action, Reduce):
                    self.reduce(state, action)
            else:
                raise CompilationError(f'Unexpected {parseItem.symbol}: {parseItem.value}')

        return state.stack[-1].value


    def parseFile(self, file:str|IOBase) -> object:
        """ Parse a source file """
        if isinstance(file, IOBase):
            stream = file
        else:
            stream = open(file, 'r', encoding='utf-8')

        with stream:
            source = stream.read()
            return self.parseString(source)


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

