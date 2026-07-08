""" A parse table builder class to convert a grammar to a parse table """

from .rule import Nonterminal, Production, Terminal, Symbol, Token
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

    def __eq__(self, right:'Item') -> bool:
        return self.prod == right.prod and self.pos == right.prod

    def __hash__(self) -> int:
        return hash(hash(self.prod) + hash(self.pos))

class State:
    def __init__(self, stateId) -> None:
        self.stateId = stateId
        self.closure:list[Item] = []
        self.goto:dict[Symbol, State] = { }


    def addItem(self, item:Item|list[Item]) -> None:
        if isinstance(item, list):
            self.closure = self.closure + item
        else:
            self.closure.append(item)


    def addGoto(self, nextState:'State') -> None:
        for item in state.closure:
            self.goto[item.symbol] = state


class ParseTableBuilder:
    """ Build a parse table """
    def __init__(self, grammar:Nonterminal) -> None:
        self._nextStateId = 0
        self.grammar = self.startSymbol(grammar)
        self.items:set[Item] = set()
        self.startItems:dict[Nonterminal, list[Item]]
        self.nonterminals:list[Nonterminal] = []
        # stateId -> state
        self.states:list[State] = []
    

    def startSymbol(self, grammar:Nonterminal) -> Nonterminal:
        start = Nonterminal()
        start.extend(Production(grammar))
        return start


    def nextStateId(self) -> int:
        stateId = self._nextStateId
        self._nextStateId += 1
        return stateId

    def newState(self) -> DFAState:
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
                    nonterminal += self.flattenRules(symbol, processed)

        return nonterminals


    def processNonterminal(self, nonterminal:Nonterminal) -> None:
        """ Build states from a nonterminal """
        # IX[ruleId, stateId]
        startStates:list[tuple[int,int]] = [ ]

        # TODO: Create a state for the nonterminal that captures the production transitions
        self.newState()
        self.stateStack.append(gotoState)

        # If we've processed this non-terminal before, we can reuse it
        if nonterminal.ruleId in self.nonterminalStates:
            startStates = self.nonterminalStates[nonterminal.ruleId]

            for ruleId, stateId in startStates:
                if ruleId in state.shift:
                    raise GenerationError('Shift/shift error')
                elif ruleId in state.reduce:
                    print('Shift/reduce warning')
                else:
                    state.shift[ruleId] = stateId

            return startStates

        self.symbols[nonterminal.ruleId] = nonterminal

        # Process this non-terminal for the first time
        for production in nonterminal.productions:

            for idx, sym in enumerate(production.symbols):
                state = self.stateStack[-1]
                last = idx == len(production.symbols)+1

                if last:
                    if sym.ruleId in state.shift:
                        print('Shift/reduce warning')
                    elif sym in state.reduce:
                        raise GenerationError('Reduce/reduce error')
                else:
                    if sym.ruleId in state.shift:
                        raise GenerationError('Shift/shift error: %s -> %s' % (state.stateId, sym.name or sym.ruleId))
                    elif sym.ruleId in state.reduce:
                        print('Shift/reduce warning')
                        break

                if isinstance(sym, Nonterminal):
                    ntStartStates = self.processNonterminal(sym)

                    if idx == 0:
                        startStates += ntStartStates

                    gotoState = self.newState()
                    state.goto[sym.ruleId] = gotoState.stateId
                    self.stateStack.append(gotoState)

                else:
                    self.symbols[sym.ruleId] = sym
                    # Last symbol, let's reduce
                    if last:
                        state.reduce[sym.ruleId] = production
                        self.popStateStack(production)
                    # Otherwise, shift
                    else:
                        nextState = self.newState()
                        if idx == 0:
                            startStates.append((sym.ruleId, nextState.stateId))
                        state.shift[sym.ruleId] = nextState.stateId
                        self.stateStack.append(nextState)

        self.nonterminalStates[nonterminal.ruleId] = startStates
        return startStates

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
        def expand(nt:Nonterminal) -> list[Item]:
            print('Start item for: %s' % (symbol))
            for nt, items in self.startItems.items():
                print('%s: %s' % (nt, items))
            items = self.startItems[symbol]

            for item in items:
                if isinstance(item.symbol, Nonterminal):
                    items += expand(item.symbol)

            return items

        state = self.newState()
        symbol = production.symbols[position]

        if isinstance(symbol, Terminal):
            state.addItem(Item(production, position))
        else:
            state.addItem(expand(symbol))

        return state


    def buildProductionStates(self, production:Production) -> list[State]:
        states:list[State] = []
        priorState:State|None = None
        pos = 0

        while pos <= len(production.symbols):
            state = self.buildState(production, pos)
            if priorState:
                priorState.addGoto(state)
            states.append(state)
            pos += 1



    def buildDFAState(self, state:State) -> DFAState:
        dfaState = DFAState(state.stateId)

        for symbol, nextState in state.goto:
            #TODO: manage conflicts
            if isinstance(symbol, Terminal):
                dfaState.shift[symbol] = nextState.stateId
            else:
                dfaState.goto[symbol] = nextState.stateId



    def build(self) -> list[DFAState]:
        """ Build (and return) the entire parse table """
        self.nonterminals = self.flattenRules(self.grammar)
        self.startItems = { nt: [] for nt in self.nonterminals }

        self.buildItems()

        for nt, items in self.startItems.items():
            print('%s: %s' % (nt.ruleId, items))

        for nt in self.nonterminals:
            for prod in nt.productions:
                self.buildProductionStates(prod)

        return [self.buildDFAState(state) for state in self.states]

        

