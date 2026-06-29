""" Genearte a new parser """

from io import IOBase
from .rule import Rule, DelayedRule, Production, Alternative, Sequence
from .state import State

class GenerationError(Exception):
    """ A compilation error """

class CompilationError(Exception):
    """ A compilation error """


class Parser:
    """ The reusable parser """
    def __init__(self, whitespace:str=' \t\n') -> None:
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


def _resolveRule(rule:Rule) -> Rule:
    """ Resolve DelayedRules (or fail) """
    if isinstance(rule, DelayedRule):
        if rule.rule is None:
            raise GenerationError('Unfilled DelayedRule'+(' '+rule.name if rule.name else ''))
        else:
            rule= rule.rule
    return rule


def _flattenRules(productions:dict[int,list[Production]], grammar:Rule) -> None:
    """ Transform arbitrary nested productions into basic production items:

    User writes:   expr = num + '*' + expr | num
    Becomes:       E' → expr (start symbol)
                   expr → num '*' expr
                   expr → num
                   num  → RE[0-9]+

    Incidentally resolve DelayedRules
    """
    grammar = _resolveRule(grammar)

    # Add every top-level production and recurse into each one
    if isinstance(grammar, Alternative):
        productions[grammar.ruleId] = grammar.alternatives

        for idx, production in list(enumerate(grammar.alternatives)):
            expanded = _resolveRule(production)

            _flattenRules(productions, expanded)

            if isinstance(production, DelayedRule):
                grammar.sequence[idx] = expanded

    # Check each symbol for nonterminals (Alternative) and recurse if we haven't added it already (avoiding cycles)
    elif isinstance(grammar, Sequence):
        for idx, symbol in list(enumerate(grammar.sequence)):
            expanded = _resolveRule(symbol)
            if isinstance(expanded, Alternative) and expanded.ruleId not in productions:
                _flattenRules(productions, expanded)

            if isinstance(production, DelayedRule):
                grammar.sequence[idx] = expanded

    # Tokens go right on the table
    else:
        productions[grammar.ruleId] = [grammar]


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

def _buildStates(grammar:dict[int,list[Production]]) -> None:
    def newState() -> None:
        nonlocal nextStateId
        state = DFAState(nextStateId)
        states[nextStateId] = state
        nextStateId += 1
        return state

    def popStateStack(production:Sequence) -> None:
        nonlocal stateStack
        length = len(production.sequence)
        stateStack = stateStack[:-length]

    def processNonterminal(nonterminal:Alternative) -> list[tuple[int,int]]:
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
        for production in nonterminal:

            for idx, sym in enumerate(production.sequence):
                last = idx == len(production)+1

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

                if isinstance(sym, Alternative):
                    ntStartStates = processNonterminal(sym)

                    if idx == 0:
                        startStates += ntStartStates

                    gotoState = newState()
                    state.goto[sym] = gotoState
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
                        state.shift[sym.ruleId] = nextState
                        stateStack.append(nextState)

        nonterminalStates[nonterminal.ruleId] = startStates
        return startStates

    nextStateId = 0
    prods = list(grammar[0])
    # ruleId -> IX[ruleId, stateId]
    nonterminalStates:dict[int,list[tuple[int, int]]] = {}
    # stateId -> state
    states:dict[int,DFAState] = {}
    stateStack:list[DFAState] = [newState()]

    processNonterminal(grammar)

        


def generate(grammar:Rule, whitespace=' \t\n') -> Parser:
    """ Create a new parser from a grammar """
    productions:dict[int,list[Alternative]]  = \
        { 0: [grammar]
        }

    _flattenRules(productions, _resolveRule(grammar))
    _buildStates(productions)

    parser = Parser(whitespace)



