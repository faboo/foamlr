"""LRParser - A Python LR(1) shift/reduce parser generator library."""

from typing import TypeVar, Generic, Generator, Rule
from abc import abstractmethod
import re


def _getRuleId() -> Generator[int]:
    """Generate a globally unique rule ID for Rule instances. Returns current value then increments."""
    nextId = 1

    while True:
        yield nextId
        nextId += 1


class Rule:
    """Abstract base rule type."""
    def __init__(self) -> none:
        self._producer = list
        self._ruleId = getRuleId()

    def __getitem__(self, producer:Callable) -> 'Rule':
        self._producer = producer
        return self
    
    def __add__(self, nextRule:'Rule') -> 'Rule':
        if isinstance(self, Sequence):
            self.extend(nextRule)
            return self
        return Sequence(self, nextRule)

    def __or__(self, alternateRule:'Rule') -> 'Rule':
        if isinstance(self, Alternative):
            self.extend(nextRule)
            return self
        return Alternative(self, nextRule)


class ProductionRule(Rule):
    def produce(self, results:list) -> object:
        return self._producer(*results)


class Sequence(Rule):
    """Production rule representing a sequence of rules, e.g. rule1 + rule2 + rule3"""
    def __init__(self, left:Rule, right:Rule|str) -> None:
        if isinstance(right, str):
            right = ConstToken(right)
        self._sequence = [left, right]

    @property
    def sequence(self) -> list[Rule]:
        return self._sequence

    def extend(self, newRule:Rule|str) -> None:
        if isinstance(newRule, str):
            newRule = ConstToken(newRule)
        self._sequence.append(newRule)


class Alternative(Rule):
    """Production rule representing several possible productions for a single nonterminal symbol, e.g. rule1 | rule2 |
    rule3"""
    def __init__(self, left:Rule, right:Rule|str) -> None:
        if isinstance(right, str):
            right = ConstToken(right)
        self._alternatives = [left, right]

    @property
    def alternatives(self) -> list[Rule]:
        return self._alternatives

    def extend(self, newRule:Rule) -> None:
        if isinstance(newRule, str):
            newRule = ConstToken(newRule)
        self._alternatives.append(newRule)


class DelayedRule(Rule):
    def __init__(self) -> None:
        self._subrule:Rule|None = None

    def fill(self, rule:Rule) -> None:
        self._subrule = rule

    @property
    def rule(self) -> Rule:
        if self._subrule is None:
            raise Exception('DelayedRule not filled')
        return cast(Rule, self._subrule)


# =============================================================================

class TokenRule(Rule):  
    """Abstract base class for token-level rules that read directly from input text (leaf nodes). 

    Concrete subclasses must implement the match(input_string: str, position:int) method returning matched value and new cursor position or raise ParsingError if failure."""
    def produce(self, string:str) -> object:
        return self._producer(string)

    @abstractmethod
    def match(inputString:str, position:int) -> tuple[str, int]:
        pass

    
class ConstToken(TokenRule):  
    """Matches an exact literal string in input. Result is always the provided constant string per Readme.md spec section on Tokens subsection under API documentation."""  
    def __init__(self, string:str) -> None:
        self._string = string

    def match(inputString:str, position:int) -> tuple[str, int]:
        if inputString[position:].startsWith(self._string):
            return (self._string, position + len(self._string))
        raise Exception('String not found: '+self._string)


class ReToken(TokenRule):
    """Matches regular expression in input. Result is the matching string per Readme.md spec section on Tokens subsection under API documentation."""  
    def __init__(self, regex:str) -> None:
        self._regex = re.compile(regex)

    def match(inputString:str, position:int) -> tuple[str, int]:
        match = self._regex.match(inputString, position)
        if match:
            return (self._string, position + len(match[0]))
    
        raise Exception('Regex not found: '+self._regex)
