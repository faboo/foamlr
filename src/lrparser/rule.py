"""Parser rules - productions and tokens."""

from typing import cast, Generator, Callable, Union
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

    @property
    def ruleId(self) -> int:
        """The unique ID of the rule"""
        return self._ruleId

    def __mul__(self, nextSymbol:Union['Symbol', str]) -> 'Production':
        rule:Production

        if isinstance(self, Symbol):
            rule = Production(self)
        else:
            rule = cast(Production, self)

        rule.extend(nextSymbol)
        return rule


class Symbol(Rule):
    """ Parser symbol - either a terminal or nonterminal. """
    def __init__(self) -> None:
        super().__init__()
        self._name:str|None = None

    @property
    def name(self) -> str|None:
        """The name of the part of grammar this rule represents (or None)
        """
        return self._name


class Production(Rule):
    """Production rule representing a sequence of rules, e.g. rule1 + rule2 + rule3"""
    def __init__(self, rule:Symbol|str) -> None:
        super().__init__()
        self._symbols:list[Symbol] = []

        self.extend(rule)

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
        rule:Symbol

        if isinstance(newRule, str):
            rule = Token(newRule)
        else:
            rule = newRule
        self._symbols.append(rule)

    def __matmul__(self, producer:Callable) -> 'Production':
        self._producer = producer
        return self


class Nonterminal(Symbol):
    """Production rule representing several possible productions for a single nonterminal symbol, e.g. rule1 | rule2 |
    rule3"""
    def __init__(self, name:str, *productions:Production|Symbol|str) -> None:
        super().__init__()

        self._productions:list[Production] = []
        self._name = name
        self.fill(*productions)

    @property
    def productions(self) -> list[Production]:
        """Get the alternatives
        """
        return self._productions 

    def extend(self, newRule:Production|Symbol|str) -> None:
        """Add a rule to the end of the list of alternatives
        """
        prod:Production

        if isinstance(newRule, str):
            newRule = Token(newRule)

        if isinstance(newRule, Production):
            prod = newRule
        else:
            prod = Production(newRule)

        self._productions.append(prod)

    def fill(self, *productions:Production|Symbol|str) -> None:
        """Complete the delayed rule with an actual rule.
        """
        for prod in productions:
            self.extend(prod)


# Tokens
# =============================================================================

class Terminal(Symbol):  
    """Abstract base class for token-level rules that read directly from input text (leaf nodes). 

    Concrete subclasses must implement the match(input_string: str, position:int) method returning matched value and new
    cursor position or raise ParsingError if failure.
    """
    def __init__(self) -> None:
        super().__init__()
        self._producer = str

    def produce(self, string:str) -> object:
        """Return the matched token.
        """
        return self._producer(string)

    @abstractmethod
    def match(self, state:State) -> str:
        """Match the token against the source stream (or raise)
        """

class EOI(Terminal):
    """ The end of input """
    _singleton:'EOI'|None = None

    def __new__(cls) -> 'EOI':
        if cls._singleton is None:
            cls._singleton = super(EOI, cls).__new__(cls)
        return cls._singleton

    @property
    def name(self) -> str|None:
        return '<<EOF>>'

    def match(self, state:State) -> str:
        raise NoMatchException()

class Token(Terminal):  
    """Matches an exact literal string in input. Result is always the provided constant string per Readme.md spec
    section on Tokens subsection under API documentation.
    """

    _tokens:dict[str,'Token'] = {}

    def __new__(cls, string:str) -> 'Token':
        if string not in Token._tokens:
            Token._tokens[string] = super(Token, cls).__new__(cls)

        return Token._tokens[string]
    
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

    _tokens:dict[str,'ReToken'] = {}

    def __new__(cls, string:str) -> 'ReToken':
        if string not in ReToken._tokens:
            ReToken._tokens[string] = super(ReToken, cls).__new__(cls)

        return ReToken._tokens[string]

    def __init__(self, regex:str, producer:Callable[[str], object]|None = None) -> None:
        super().__init__()
        self._regex = re.compile(regex)
        self._producer = cast(Callable, producer)

    def match(self, state:State) -> str:
        match = self._regex.match(state.fullSource, state.pos)
        if not match:
            raise NoMatchException()

        state.consume(len(match[0]))
        return match[0]

