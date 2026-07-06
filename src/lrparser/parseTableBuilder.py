""" A parse table builder class to convert a grammar to a parse table """

from .rule import Nonterminal, Production, Terminal, Symbol, Token
from .parseTable import DFAState

class GenerationError(Exception):
    """ A compilation error """


class ParseTableBuilder:
    """ Build a parse table """
    def __init__(self, grammar:Nonterminal) -> None:
        self.grammar = grammar
        self._nextStateId = 0
        # nonterminal Id -> [token Id]
        self.startSymbols:dict[int,list[int]] = {}
        # ruleId -> stateId
        self.nonterminalStates:dict[int,int] = {}
        self.stateStack:list[DFAState] = []
        # stateId -> state
        self.states:list[DFAState] = []
        # 
        self.symbols:dict[int, NonTerminal|Terminal] = { }

        self.stateStack.append(self.newState())


    def newState(self) -> DFAState:
        """ Create (and track) a new parse state """
        state = DFAState(self._nextStateId)
        self.states.append(state)
        self._nextStateId += 1
        return state


    def popStateStack(self, production:Production) -> None:
        """ Pop the state stack by the size of the production """
        length = len(production.symbols)
        self.stateStack = self.stateStack[:-length]


    def flattenRules(nonterminal:Nonterminal, processed:set[Nonterminal]|None=None) -> list[Nonterminal]:
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


    def collectStartSymbols(nonterminals:list[Nonterminal]) -> dict[int,list[int]]:
        """ Collect start terminals for each nonterminal """
        startSymbols:dict[int,list[Symbol]] = { }
        finished = True
        
        for nt in nonterminal:
            startSymbols[nt.ruleId] = []
            for production in nt.productions:
                startSymbols[nt.ruleId].append(production.symbols[0])

        while True:
            for nt in nonterminals:
                newSymbols = startSymbols[nt.ruleId]

                for symbol in startSymbols[nt.ruleId]:
                    elif isinstance(symbol, Nonterminal):
                        newSymbols += list(filter(lambda s: s != nt, startSymbols[symbol.ruleId]))
                        finished = False

                if not finished:
                    startSymbols[nt.ruleId] = list(set(newSymbols))

            if finished:
                break

        return {ntId: [tk.ruleId for tk in tks] for ntId, tks in enumerate(startSymbols)}


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

    def build(self) -> None:
        """ Build (and return) the entire parse table """
        nonterminals = self.flattenRules(self.grammar)

        self.startSymbols = self.collectStartSymbols(nonterminals)
        self.processNonterminal(self.grammar)

