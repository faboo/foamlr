"""Parser rules - productions and tokens."""

from typing import cast, Generator, Callable, Union
from abc import abstractmethod
import re


def _generateRuleId() -> Generator[int]:
    """Generate a globally unique rule ID for Rule instances. Returns current value then increments.
    """
    nextId = 1

    while True:
        yield nextId
        nextId += 1

_nextRuleId = _generateRuleId()


class GenerationError(Exception):
    """ A compilation error """

class NoMatchException(Exception):
    """Raised when a rule does not match the code at the current position
    """


class Rule:
    """Abstract base rule type.
    """
    def __init__(self) -> None:
        def listify(*args):
            if len(args) > 1:
                return list(args)
            else:
                return args[0]
        self._producer:Callable = listify 
        self._ruleId = next(_nextRuleId)

    @property
    def ruleId(self) -> int:
        """The unique ID of the rule"""
        return self._ruleId

    def _visit(self, visitor:Callable[['Rule'], None]) -> None:
        pass

    def __mul__(self, nextSymbol:Union['Symbol', str]) -> 'Production':
        rule:Production

        if isinstance(self, Symbol):
            rule = Production(self)
        else:
            rule = cast(Production, self)

        rule.extend(nextSymbol)
        return rule

    def __hash__(self) -> int:
        return hash(id(self))

    def visit(self,
            callback:Callable[['Rule'], None],
            filt:Callable[['Rule'], bool]|None=None
            ) -> None:
        """ Visit every node in the grammar tree """
        visited:set = set()
        def visit(node:'Rule') -> None:
            # functools.cache was not actually caching, so do it ourself
            if id(node) in visited:
                return
            visited.add(id(node))
            if not filt or filt(node):
                callback(node)

            node._visit(visit)
        visit(self)


class Symbol(Rule):
    """ Parser symbol - either a terminal or nonterminal. """
    def __init__(self) -> None:
        super().__init__()
        self._name:str = 'NONAME'

    @property
    def name(self) -> str:
        """The name of the part of grammar this rule represents (or None)
        """
        return self._name

    def __str__(self) -> str:
        return self.name or 'ERR'


class Production(Rule):
    """Production rule representing a sequence of rules, e.g. rule1 + rule2 + rule3"""
    def __init__(self, rule:Symbol|str) -> None:
        super().__init__()
        self._symbols:list[Symbol] = []
        self._nonterminal:Nonterminal|None = None

        self.extend(rule)

    def setNonterminal(self, nonterminal:'Nonterminal') -> None:
        self._nonterminal = nonterminal

    @property
    def nonterminal(self) -> 'Nonterminal':
        if self._nonterminal is None:
            raise TypeError('Production not initialized (no Nonterminal)')
        return self._nonterminal

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

        if not isinstance(newRule, (Symbol, str)):
            raise GenerationError(f'Production symbols not a str, Token, or ReToken: {newRule}')

        if isinstance(newRule, str):
            rule = Token(newRule)
        else:
            rule = newRule

        self._symbols.append(rule)

    def __matmul__(self, producer:Callable) -> 'Production':
        self._producer = producer
        return self

    def _visit(self, visitor:Callable[['Rule'], None]) -> None:
        for symbol in self._symbols:
            visitor(symbol)


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

        prod.setNonterminal(self)
        self._productions.append(prod)

    def fill(self, *productions:Production|Symbol|str) -> None:
        """Complete the delayed rule with an actual rule.
        """
        for prod in filter(None, productions):
            self.extend(cast(Production|Symbol|str, prod))

    def _visit(self, visitor:Callable[['Rule'], None]) -> None:
        for production in self._productions:
            visitor(production)


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
    def match(self, source:str) -> str:
        """Match the token against the source stream (or raise)
        """

    def __matmul__(self, producer:Callable) -> 'Terminal':
        self._producer = producer
        return self

    def __repr__(self) -> str:
        return f'TOKEN({self.name})'

class EOI(Terminal):
    """ The end of input """
    _singleton:Union['EOI', None] = None

    def __new__(cls) -> 'EOI':
        if cls._singleton is None:
            cls._singleton = super(EOI, cls).__new__(cls)
        return cls._singleton

    @property
    def name(self) -> str:
        return '<<EOF>>'

    def match(self, source:str) -> str:
        if not source:
            return ''
        else:
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
        self._name = string

    def match(self, source:str) -> str:
        if not source.startswith(self._string):
            raise NoMatchException()

        return self._string
T = Token


class ReToken(Terminal):
    """Matches regular expression in input. Result is the matching string per Readme.md spec section on Tokens
    subsection under API documentation.
    """
    def __init__(self, name:str, regex:str, notRegex:str|None=None) -> None:
        super().__init__()
        self._regex = re.compile(regex)
        self._notRegex = re.compile(notRegex) if notRegex else None
        self._name = name

    def match(self, source:str) -> str:
        match = self._regex.match(source)
        if not match:
            raise NoMatchException()
        if self._notRegex and self._notRegex.match(source):
            raise NoMatchException()

        return match[0]
        
R = ReToken
