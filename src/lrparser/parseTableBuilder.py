""" A parse table builder class to convert a grammar to a parse table """

from typing import cast, override, Optional
from .rule import GenerationError, Nonterminal, Production, Terminal, Symbol, EOI
from .parseTable import ParseTable, Shift, Reduce, Accept


class Item:
    def __init__(self, prod:Production, position:int) -> None:
        self.prod = prod
        self.pos = position

    @property
    def end(self) -> bool:
        return len(self.prod.symbols) == self.pos

    @property
    def eoi(self) -> bool:
        return not self.end and self.symbol == EOI()

    @property
    def symbol(self) -> Symbol:
        return self.prod.symbols[self.pos]

    @property
    def nextItem(self) -> Optional['Item']:
        return Item(self.prod, self.pos+1) if not self.end else None

    def __eq__(self, right:object) -> bool:
        if not isinstance(right, Item):
            return False
        return self.prod == right.prod and self.pos == right.pos

    def __hash__(self) -> int:
        return hash(hash(self.prod) + hash(self.pos))

    def __repr__(self) -> str:
        start = "".join(str(sym) for sym in self.prod.symbols[:self.pos])
        end = "".join(str(sym) for sym in self.prod.symbols[self.pos:])
        name = self.prod.nonterminal.name
        return f'{name} → {start}·{end}'


class Closure(set[Item]):
    @override
    def __hash__(self) -> int:#type: ignore
        return hash(sum(hash(item) for item in self))


class State:
    def __init__(self, stateId) -> None:
        self.stateId = stateId
        self.closure:set[Item] = set()
        self.goto:dict[Symbol,Closure] = { }
        self.edge:dict[Symbol,State] = { }


class ParseTableBuilder:
    """ Build a parse table """
    def __init__(self, grammar:Nonterminal) -> None:
        self._nextStateId = 0
        self.grammar = self.startSymbol(grammar)
        self.parseTable = ParseTable(self.grammar)
        self.states:list[State] = []
        self.stateLookup:dict[Closure, State] = {}


    def startSymbol(self, grammar:Nonterminal) -> Nonterminal:
        start = Nonterminal('S',
            Production(grammar) * EOI())
        return start


    def nextStateId(self) -> int:
        stateId = self._nextStateId
        self._nextStateId += 1
        return stateId

    def newState(self, closure:set[Item]) -> State:
        """ Create (and track) a new parse state """
        state = State(self.nextStateId())
        state.closure = closure
        self.states.append(state)
        self.stateLookup[Closure(closure)] = state
        return state


    def expandClosure(self, closure:set[Item]) -> set[Item]:
        count = 0
        while True:
            added = False
            for item in list(closure):
                if not item.end and isinstance(item.symbol, Nonterminal):
                    for prod in item.symbol.productions:
                        item = Item(prod, 0)
                        if item not in closure:
                            closure.add(item)
                            added = True

            if not added:
                break

        return closure


    def fillGoto(self, state:State) -> None:
        goto:dict[Symbol, Closure] = { }

        for item in self.expandClosure(state.closure):
            nextItem = item.nextItem
            print(f'  {item} -> {nextItem}')
            if nextItem is not None:
                if item.symbol not in goto:
                    goto[item.symbol] = Closure({ })
                goto[item.symbol].add(nextItem)

        state.goto = goto


    def build(self) -> ParseTable:
        """ Build (and return) the entire parse table """
        table = ParseTable(self.grammar)
        # The start state
        self.newState({Item(self.grammar.productions[0], 0)})

        # Build the states
        statePos = 0
        while statePos < len(self.states):
            state = self.states[statePos]
            print(f'State {state.stateId} for {state.closure}')
            self.fillGoto(state)

            for symbol, closure in state.goto.items():
                if symbol == EOI(): continue

                print(f'    GO {symbol} -> {closure}')
                if closure not in self.stateLookup:
                    nextState = self.newState(closure)
                    print(f'    <new state {nextState .stateId}>')
                else:
                    nextState = self.stateLookup[closure]
                    print(f'    <state {nextState .stateId}>')

                state.edge[symbol] = self.stateLookup[closure]
            
            statePos += 1

        # Build the table from the states
        table.actionTable = list({} for _ in range(len(self.states)))
        table.gotoTable = list({} for _ in range(len(self.states)))

        print('TABLE')
        for state in self.states:
            actions = table.actionTable[state.stateId]
            gotos = table.gotoTable[state.stateId]

            print(f'State {state.stateId}')

            for item in state.closure:
                print(f'  {item} ({item.end}) ({item.eoi})')
                if item.end:
                    for terminal in table.tokens:
                        actions[terminal] = Reduce(item.prod)
                elif item.eoi:
                    actions[item.symbol] = Accept()

            for symbol, state in state.edge.items():
                print(f'  SYM: {symbol}')
                if isinstance(symbol, Terminal) and symbol != EOI():
                    if symbol in actions and isinstance(actions[symbol], Shift):
                        # TODO: Need to describe the conflict
                        raise GenerationError('Shift-shift conflict')
                    # TODO: warn about shift/reduce conflict
                    actions[symbol] = Shift(state.stateId)
                else:
                    gotos[cast(Nonterminal, symbol)] = state.stateId

        return table

        

