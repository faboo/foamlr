""" Parse table row data """

from .rule import Rule, Terminal, Nonterminal

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


def printTable(states:list[DFAState], symbols:dict[int, Terminal|Nonterminal]) -> None:
    """ Print out a parse table in a nicely formatted table. """
    terminals:list[Terminal] = []
    nonterminals:list[Nonterminal] = []

    for state in states:
        terminals = list(set(terminals).union(set(state.shift.keys())))
        terminals = list(set(terminals).union(set(state.reduce.keys())))
        nonterminals = list(set(nonterminals).union(set(state.goto.keys())))

    headings = map(lambda id: symbols[id].name, [*terminals, *nonterminals])
    print(' | '.join(map('{0:<8}'.format, ['State', *headings])))

    for state in states:
        #pylint: disable=cell-var-from-loop
        actions = map(
            lambda t: f'shift {state.shift[t]}' if t in state.shift
                else 'reduce' if t in state.reduce
                else 'accept' if t in state.accept
                else 'error',
            terminals
            )
        gotos = map(
            lambda t: state.goto[t] if t in state.goto else '',
            nonterminals
            )
        print(' | '.join(map('{0:<6}'.format, [state.stateId, *actions, *gotos])))

