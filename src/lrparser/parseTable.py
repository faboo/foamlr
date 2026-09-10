""" Parse table row data """

from typing import cast, Callable
from .rule import Rule, Terminal, Nonterminal, Symbol, Production

class DFAState:
    """ A state in the parsing automata """
    def __init__(self, stateId:int) -> None:
        self.stateId = stateId
        # token ruleId -> next stateId
        self.shift:dict[Terminal,int] = { }
        # token ruleId -> next stateId (don't consume)
        self.follow:dict[Terminal,int] = { }
        # token ruleId -> reduce Rule
        self.reduce:dict[Terminal,Production] = { }
        # token ruleId -> next stateId
        self.goto:dict[Nonterminal,int] = { }
        # token ruleId
        self.accept:set[int] = set()

class Action:
    pass

class Shift(Action):
    def __init__(self, stateId:int) -> None:
        self.to = stateId

    def __str__(self) -> str:
        return f'Shift({self.to})'

class Reduce(Action):
    def __init__(self, production:Production) -> None:
        self.production = production

    def __str__(self) -> str:
        return f'Reduce({len(self.production.symbols)})'

class Accept(Action):
    def __str__(self) -> str:
        return 'Accept'

class ParseTable:
    """ A state table """
    def __init__(self, grammar:Rule) -> None:
        self.tokens:list[Terminal] = []
        self.rules:list[Nonterminal] = []
        self.actionTable:list[dict[Terminal, Action]] = []
        self.gotoTable:list[dict[Nonterminal, int]] = []

        self.extractTokens(grammar)


    def extractTokens(self, grammar:Rule) -> None:
        """ Extract all the tokens from the grammar """
        def extract(symbol):
            if isinstance(symbol, Terminal):
                self.tokens.append(symbol)
            elif isinstance(symbol, Nonterminal):
                self.rules.append(symbol)
        grammar.visit(extract)


    def print(self) -> None:
        def pf(value):
            print(f'{str(value):10} | ', end='')

        pf('State')
        for token in self.tokens:
            pf(token.name)
        for rule in self.rules:
            pf(rule.name)
        print('')

        for stateId in range(len(self.actionTable)):
            pf(stateId)

            for token in self.tokens:
                if token not in self.actionTable[stateId]:
                    pf('Error')
                else:
                    action = self.actionTable[stateId][token]
                    pf(action)
            for rule in self.rules:
                if rule not in self.gotoTable[stateId]:
                    pf(' ')
                else:
                    gotoId = self.gotoTable[stateId][rule]
                    pf(f'Goto({gotoId})')

            print('')



