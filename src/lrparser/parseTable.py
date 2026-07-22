""" Parse table row data """

from .rule import Terminal, Nonterminal, Symbol, Production

class DFAState:
    """ A state in the parsing automata """
    def __init__(self, stateId:int) -> None:
        self.stateId = stateId
        # token ruleId -> next stateId
        self.shift:dict[Terminal,int] = { }
        # token ruleId -> reduce Rule
        self.reduce:dict[Terminal,Production] = { }
        # token ruleId -> next stateId
        self.goto:dict[Nonterminal,int] = { }
        # token ruleId
        self.accept:set[int] = set()


def printTable(states:list[DFAState], symbols:dict[int, Symbol]) -> None:
    """ Print out a parse table in a nicely formatted table. """
    shifts:list[Symbol] = []
    nonterminals:list[Nonterminal] = []

    print('TABLE (%s)' % len(states))
    for state in states:
        shifts = list(set(shifts).union(set(state.shift.keys())))
        shifts = list(set(shifts).union(set(state.reduce.keys())))
        nonterminals = list(set(nonterminals).union(set(state.goto.keys())))

    headings = map(lambda sym: symbols[sym.ruleId].name, [*shifts, *nonterminals])
    stateHeading = '{0:<8}'.format('State')
    header = ' | '.join(map('{0:<8}'.format, headings))
    sections = f'{{}} | {{:<{len(header)}}} | Goto'.format(' '*8, 'Action')

    print(sections)
    print(stateHeading, '|', header)

    for state in states:
        #pylint: disable=cell-var-from-loop
        actions = map(
            lambda t: f'shift {state.shift[t]}' if t in state.shift
                else 'reduce' if t in state.reduce
                else 'accept' if t in state.accept
                else 'error',
            shifts
            )
        gotos = map(
            lambda t: state.goto[t] if t in state.goto else '',
            nonterminals
            )
        print(' | '.join(map('{0:<8}'.format, [state.stateId, *actions, *gotos])))

