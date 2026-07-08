"""Parser rules - productions and tokens."""

from typing import Generator, Callable, Union
from abc import abstractmethod
import re
from .state import State


def _generateRuleId() -> Generator[int]:
    """Generate a globally unique rule ID for Rule instances. Returns current value then increments.
    """
    nextId = 1

    while True:
        yield nextId
        nextId += 1

_nextRuleId = _generateRuleId()


class NoMatchException(Exception):
    """Raised when a rule does not match the code at the current position
    """


class Rule:
    """Abstract base rule type.
    """
    def __init__(self) -> None:
        super().__init__()
        self._producer:Callable = list
        self._ruleId = next(_nextRuleId)
        self._name:str|None = None

    @property
    def ruleId(self) -> int:
        """The unique ID of the rule"""
        return self._ruleId

    @property
    def name(self) -> str|None:
        """The name of the part of grammar this rule represents (or None)
        """
        return self._name

    def __getitem__(self, producer:Callable) -> 'Rule':
        self._producer = producer
        return self

    def __matmul__(self, name:str) -> 'Rule':
        self._name = name
        return self
    
    def __add__(self, nextRule:Union['Rule', str]) -> 'Rule':
        rule = self

        if not isinstance(rule, Production):
            rule = Production(rule)

        rule.extend(nextRule)
        return rule

    def __or__(self, alternateRule:Union['Rule', str]) -> 'Rule':
        rule = self

        if not isinstance(rule, Nonterminal):
            rule = Nonterminal()
            rule.extend(self)

        rule.extend(alternateRule)
        return rule


class Symbol(Rule):
    """ Parser symbol - either a terminal or nonterminal. """

class Production(Rule):
    """Production rule representing a sequence of rules, e.g. rule1 + rule2 + rule3"""
    def __init__(self, rule:Symbol) -> None:
        super().__init__()
        self._symbols = [rule]

    @property
    def symbols(self) -> list[Symbol]:
        """Get the rules in the sequence.
        """
        return self._symbols

    def produce(self, results:list) -> object:
        """Create an object from stack items that the production matched.
        """
        return self._producer(*results)

    def extend(self, newRule:Symbol|str) -> None:
        """Add a rule to the sequence.
        """
        if isinstance(newRule, str):
            newRule = Token(newRule)
        self._symbols.append(newRule)


class Nonterminal(Symbol):
    """Production rule representing several possible productions for a single nonterminal symbol, e.g. rule1 | rule2 |
    rule3"""
    def __init__(self) -> None:
        super().__init__()

        self._productions:list[Production] = []

    @property
    def productions(self) -> list[Production]:
        """Get the alternatives
        """
        return self._productions 

    def extend(self, newRule:Rule|str) -> None:
        """Add a rule to the end of the list of alternatives
        """
        if isinstance(newRule, str):
            newRule = Token(newRule)
        if not isinstance(newRule, Production):
            newRule = Production(newRule)
        self._productions.append(newRule)

    def fill(self, rule:'Nonterminal') -> None:
        """Complete the delayed rule with an actual rule.
        """
        self._productions = rule.productions
        if self.name is None:
            self._name = rule.name


# Tokens
# =============================================================================

class Terminal(Symbol):  
    """Abstract base class for token-level rules that read directly from input text (leaf nodes). 

    Concrete subclasses must implement the match(input_string: str, position:int) method returning matched value and new
    cursor position or raise ParsingError if failure.
    """
    def produce(self, string:str) -> object:
        """Return the matched token.
        """
        return self._producer(string)

    @abstractmethod
    def match(self, state:State) -> str:
        """Match the token against the source stream (or raise)
        """

    
class Token(Terminal):  
    """Matches an exact literal string in input. Result is always the provided constant string per Readme.md spec
    section on Tokens subsection under API documentation.
    """
    def __init__(self, string:str) -> None:
        super().__init__()
        self._string = string

    @property
    def name(self) -> str|None:
        return self._string

    def match(self, state:State) -> str:
        if not state.source.startswith(self._string):
            raise NoMatchException()

        state.consume(len(self._string))
        return self._string


class ReToken(Terminal):
    """Matches regular expression in input. Result is the matching string per Readme.md spec section on Tokens
    subsection under API documentation.
    """
    def __init__(self, regex:str) -> None:
        super().__init__()
        self._regex = re.compile(regex)

    def match(self, state:State) -> str:
        match = self._regex.match(state.fullSource, state.pos)
        if not match:
            raise NoMatchException()

        state.consume(len(match[0]))
        return match[0]

