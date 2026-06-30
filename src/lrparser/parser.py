""" Genearte a new parser """

from io import IOBase
from .rule import Rule, Nonterminal, Production
from .state import State

class GenerationError(Exception):
    """ A compilation error """

class CompilationError(Exception):
    """ A compilation error """


class Parser:
    """ The reusable parser """
    def __init__(self, whitespace:str|None=' \t\n') -> None:
        self.whitespace = whitespace

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


class DFAState:
    """ A state in the parsing automata """
    def __init__(self, stateId:int) -> None:
        self.stateId = stateId
        # token ruleId -> next stateId
        self.shift:dict[int,int] = { }
        # token ruleId -> reduce Rule
        self.reduce:dict[int,Rule] = { }
        # token ruleId -> next stateId
        self.goto:dict[int,int] = { }
        # token ruleId
        self.accept:set[int] = set()

def _buildStates(grammar:Nonterminal) -> list[DFAState]:
    nextStateId = 0
    # ruleId -> IX[ruleId, stateId]
    nonterminalStates:dict[int,list[tuple[int, int]]] = {}
    # stateId -> state
    states:list[DFAState] = []
    stateStack:list[DFAState] = [newState()]

    def newState() -> DFAState:
        nonlocal nextStateId
        state = DFAState(nextStateId)
        states.append(state)
        nextStateId += 1
        return state

    def popStateStack(production:Production) -> None:
        nonlocal stateStack
        length = len(production.symbols)
        stateStack = stateStack[:-length]

    def processNonterminal(nonterminal:Nonterminal) -> list[tuple[int,int]]:
        # IX[ruleId, stateId]
        startStates:list[tuple[int,int]] = [ ]
        state = stateStack[-1]

        # If we've processed this non-terminal before, we can reuse it
        if nonterminal.ruleId in nonterminalStates:
            startStates = nonterminalStates[nonterminal.ruleId]

            for ruleId, stateId in startStates:
                if ruleId in state.shift:
                    raise GenerationError('Shift/shift error')
                elif ruleId in state.reduce:
                    print('Shift/reduce warning')
                else:
                    state.shift[ruleId] = stateId

            return startStates

        # Process this non-terminal for the first time
        for production in nonterminal.productions:

            for idx, sym in enumerate(production.symbols):
                last = idx == len(production.symbols)+1

                if last:
                    if sym.ruleId in state.shift:
                        print('Shift/reduce warning')
                    elif sym in state.reduce:
                        raise GenerationError('Reduce/reduce error')
                else:
                    if sym.ruleId in state.shift:
                        raise GenerationError('Shift/shift error')
                    elif sym.ruleId in state.reduce:
                        print('Shift/reduce warning')
                        break

                if isinstance(sym, Nonterminal):
                    ntStartStates = processNonterminal(sym)

                    if idx == 0:
                        startStates += ntStartStates

                    gotoState = newState()
                    state.goto[sym.ruleId] = gotoState.stateId
                    stateStack.append(gotoState)

                else:
                    # Last symbol, let's reduce
                    if last:
                        state.reduce[sym.ruleId] = production
                        popStateStack(production)
                    # Otherwise, shift
                    else:
                        nextState = newState()
                        if idx == 0:
                            startStates.append((sym.ruleId, nextState.stateId))
                        state.shift[sym.ruleId] = nextState.stateId
                        stateStack.append(nextState)

        nonterminalStates[nonterminal.ruleId] = startStates
        return startStates


    processNonterminal(grammar)
    return states



def generate(grammar:Nonterminal, whitespace=' \t\n') -> Parser:
    """ Create a new parser from a grammar """
    #productions:dict[int,list[Nonterminal]]  = \
    #    { 0: [grammar]
    #    }

    #_flattenRules(productions, grammar)
    states = _buildStates(grammar)

    parser = Parser(whitespace)

    return parser

