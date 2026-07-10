""" A parse table builder class to convert a grammar to a parse table """

from typing import cast
from .rule import Nonterminal, Production, Terminal, Symbol
from .parseTable import DFAState

class GenerationError(Exception):
    """ A compilation error """


class Item:
    def __init__(self, prod:Production, position:int) -> None:
        self.prod = prod
        self.pos = position

    @property
    def end(self) -> bool:
        return len(self.prod.symbols) == self.pos

    @property
    def symbol(self) -> Symbol:
        return self.prod.symbols[self.pos]

    def __eq__(self, right:object) -> bool:
        if not isinstance(right, Item):
            return False
        return self.prod == right.prod and self.pos == right.prod

    def __hash__(self) -> int:
        return hash(hash(self.prod) + hash(self.pos))

class State:
    def __init__(self, stateId) -> None:
        self.stateId = stateId
        self.closure:list[Item] = []
        self.goto:dict[Symbol, State] = { }
        self.reduce:Production|None = None


    def addItem(self, item:Item|list[Item]) -> None:
        if isinstance(item, list):
            self.closure = self.closure + item
        else:
            self.closure.append(item)


    def addGoto(self, nextState:'State') -> None:
        for item in nextState.closure:
            self.goto[item.symbol] = nextState


class ParseTableBuilder:
    """ Build a parse table """
    def __init__(self, grammar:Nonterminal) -> None:
        self._nextStateId = 0
        self.grammar = self.startSymbol(grammar)
        self.items:set[Item] = set()
        self.startItems:dict[Nonterminal, list[Item]]
        self.nonterminals:list[Nonterminal] = []
        self.terminals:set[Terminal] = set()
        self.states:list[State] = []
 

    def startSymbol(self, grammar:Nonterminal) -> Nonterminal:
        start = Nonterminal('S')
        start.extend(Production(grammar))
        return start


    def nextStateId(self) -> int:
        stateId = self._nextStateId
        self._nextStateId += 1
        return stateId

    def newState(self) -> State:
        """ Create (and track) a new parse state """
        state = State(self.nextStateId())
        self.states.append(state)
        return state


    def flattenRules(self, nonterminal:Nonterminal, processed:set[Nonterminal]|None=None) -> list[Nonterminal]:
        """ Transform arbitrary nested productions into basic production items:

        User writes:   expr = num + '*' + expr | num
        Becomes:       E' → expr (start symbol)
                       expr → num '*' expr
                       expr → num
                       num  → RE[0-9]+

        Incidentally resolve Delayeds
        """
        if processed is None:
            processed = set()

        nonterminals = [nonterminal]
        processed.add(nonterminal)

        for production in nonterminal.productions:
            for symbol in production.symbols:
                if isinstance(symbol, Nonterminal) and symbol not in processed:
                    nonterminals += self.flattenRules(symbol, processed)
                else:
                    self.terminals.add(cast(Terminal, symbol))

        return nonterminals


    def buildItems(self) -> None:
        for nt in self.nonterminals:
            for prod in nt.productions:
                for pos, _ in enumerate(prod.symbols):
                    item = Item(prod, pos)
                    self.items.add(item)
                    if pos == 0:
                        self.startItems[nt].append(item)
                self.items.add(Item(prod, len(prod.symbols)))


    def buildState(self, production:Production, position:int) -> State:
        def expand(symbol:Nonterminal) -> list[Item]:
            items = self.startItems[symbol]

            for item in items:
                if isinstance(item.symbol, Nonterminal):
                    items += expand(item.symbol)

            return items

        state = self.newState()

        if position < len(production.symbols):
            symbol = production.symbols[position]

            if isinstance(symbol, Terminal):
                state.addItem(Item(production, position))
            else:
                state.addItem(expand(cast(Nonterminal, symbol)))
        else:
            state.reduce = production

        return state


    def buildProductionStates(self, production:Production) -> None:
        states:list[State] = []
        priorState:State|None = None
        pos = 0

        while pos <= len(production.symbols):
            state = self.buildState(production, pos)
            if priorState:
                priorState.addGoto(state)
            states.append(state)
            pos += 1
            priorState = state



    def buildDFAState(self, state:State) -> DFAState:
        dfaState = DFAState(state.stateId)
        print('Converting %s (%s) C(%s) G(%s) R(%s)' %
            (state, state.stateId, len(state.closure), len(state.goto), state.reduce))

        for symbol, nextState in state.goto.items():
            #TODO: manage conflicts
            if isinstance(symbol, Terminal):
                dfaState.shift[symbol] = nextState.stateId
            else:
                dfaState.goto[cast(Nonterminal, symbol)] = nextState.stateId
        #if self.reduce:
        #    dfaState.

        return dfaState



    def build(self) -> list[DFAState]:
        """ Build (and return) the entire parse table """
        self.nonterminals = self.flattenRules(self.grammar)
        self.startItems = { nt: [] for nt in self.nonterminals }

        self.buildItems()

        for nt in self.nonterminals:
            for prod in nt.productions:
                self.buildProductionStates(prod)

        return [self.buildDFAState(state) for state in self.states]

        

