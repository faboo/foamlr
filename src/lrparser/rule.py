"""Parser rules - productions and tokens."""

from typing import cast, Generator, Callable, Union
from abc import abstractmethod
import re
from .state import State


def _getRuleId() -> Generator[int]:
    """Generate a globally unique rule ID for Rule instances. Returns current value then increments.
    """
    nextId = 1

    while True:
        yield nextId
        nextId += 1


class NoMatchException(Exception):
    """Raised when a rule does not match the code at the current position
    """


class Rule:
    """Abstract base rule type.
    """
    def __init__(self) -> None:
        super().__init__()
        self._producer:Callable = list
        self._ruleId = _getRuleId()
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
        if isinstance(self, Sequence):
            self.extend(nextRule)
            return self
        return Sequence(self, nextRule)

    def __or__(self, alternateRule:Union['Rule', str]) -> 'Rule':
        if isinstance(self, Alternative):
            self.extend(alternateRule)
            return self
        return Alternative(self, alternateRule)


# Productions
# =============================================================================

class Production(Rule):
    """Base production rule.
    """
    def produce(self, results:list) -> object:
        """Create an object from stack items that the production matched.
        """
        return self._producer(*results)


class Sequence(Production):
    """Production rule representing a sequence of rules, e.g. rule1 + rule2 + rule3"""
    def __init__(self, left:Rule, right:Rule|str) -> None:
        super().__init__()
        if isinstance(right, str):
            right = ConstToken(right)
        self._sequence = [left, right]

    @property
    def sequence(self) -> list[Rule]:
        """Get the rules in the sequence.
        """
        return self._sequence

    def extend(self, newRule:Rule|str) -> None:
        """Add a rule to the sequence.
        """
        if isinstance(newRule, str):
            newRule = ConstToken(newRule)
        self._sequence.append(newRule)


class Alternative(Production):
    """Production rule representing several possible productions for a single nonterminal symbol, e.g. rule1 | rule2 |
    rule3"""
    def __init__(self, left:Rule, right:Rule|str) -> None:
        super().__init__()
        if isinstance(right, str):
            right = ConstToken(right)
        self._alternatives = [left, right]

    @property
    def alternatives(self) -> list[Rule]:
        """Get the alternatives
        """
        return self._alternatives

    def extend(self, newRule:Rule) -> None:
        """Add a rule to the end of the list of alternatives
        """
        if isinstance(newRule, str):
            newRule = ConstToken(newRule)
        self._alternatives.append(newRule)


class DelayedRule(Rule):
    """A rule to be defined later, used to facilitate recursive productions.
    """
    def __init__(self) -> None:
        super().__init__()
        self._subrule:Rule|None = None

    def fill(self, rule:Rule) -> None:
        """Complete the delayed rule with an actual rule.
        """
        self._subrule = rule
        if rule.name is None:
            rule.name = self.name

    @property
    def rule(self) -> Rule:
        """Retrieve the wrapped rule
        """
        if self._subrule is None:
            raise TypeError('DelayedRule not filled')
        return cast(Rule, self._subrule)


# Tokens
# =============================================================================

class Token(Rule):  
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

    
class ConstToken(Token):  
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


class ReToken(Token):
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

