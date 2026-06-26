# LRParser

LRParser is a python LR-1, reduce-shift parser generator. The generated parser reads text streams or raw strings and
outputs either a list-based parse tree or a custom object if producers are provided to the grammar rules.


# Basic Example

A simple arithmatic parser:

``
# First, we define the grammar
arithmatic:Rule = DelayedRule()
integer = ReToken('[0-9]+')
addition = ( integer + '+' + arithmatic ) | ( integer + '-' + arithmatic )
multiplication = ( integer + '*' + arithmatic ) | ( integer + '/' + arithmatic )
grouping = ConstToken('(') + arithmatic + ')'
arithmatic.fill(integer | addition | multiplication | grouping)

# Then, we can generate a parser from the grammar
parser:Parser = generate(arithmatic)

# With the parser, we can parse a string into parse tree
tree:list = parser.parseString("2 * (7 - 4)")
``

In this example we didn't provide constuctors to the grammar rules, so the final value of `tree` is a parse tree:

     ['2' '*' ['(' ['7' '-' ['4']] ')']]


# API

## Parser creation
``
# Create a Parser object from a grammar.
def generate(grammar:Rule) -> Parser

class Parser:
    # Parse directly from a string
    def parseString(input:str) -> object

    # Parse text from a file, given a filename or stream object
    def parseFile(file:str|Stream) -> object

    # Set whitespace characters (default: ' \t\n') that are automatically skipped between rules.
    # Set to None to 
    def setWhite(whitespace:str|None) -> None
``

## Rules

There are effectively two kinds of rules: "token" rules, and "production" rules.

Token rules serve as tokenizers, reading directly from the input to extract a string. Token rules also consume white
space before and after the extracted token.

Production rules the "productions" of the grammar, combining other rules to build the parse tree. If a bare string is
passed to any production producing function or operator, it is interpreted as a ConstToken.


### Tokens

``
# Match an exact string in the input. The result of this rule is always the provided string.
class ConstToken(TokenRule):
    def __init__(self, string:str)
``

``
# Match a regular expression in the input. 
class ReToken(TokenRule):
    def __init__(self, regex:str)
``


### Productions

Rules are combined into productions with two basic operations: sequences and alternatives.

Sequences are built with the `+` operator:

``
nonterminal = rule1 + rule2 + rule3
``

A sequence of rules is parsed from left to right. Every rule in the sequence must match for the sequence to match.

Alternatives are specified with the `|` operator:

``
nonterminal = rule1 | rule2 | rule3
``

The first matching rule in a set of alternatives is used as the matching rule.


### Recursion

Recursive rules can be defined using the DelayedRule class. A delayed rule can be used throughout the definition of the
grammar as soon as it's defined, but only needs to be "filled in" once all its prerequisites are defined.

``
class DelayedRule(Rule):
    def fill(self, production:Rule) -> None
``


## Custom parse trees

By default, rules produce either a string (for token rules) or a list (for production rules). You can override the
producer of any rule using the `[ ]` operator:

``
class Exp:
    pass

class AddExp(Exp):
    def __init__(self, left:int, op:str, right:int) -> None:
        self.left = left
        self.right = right

class MultExp:
    def __init__(self, left:int, op:str, right:int) -> None:
        self.left = left
        self.right = right

integer = ReToken('[0-9]+')[int]
addition = (integer + '+' + integer)[AddExp]
multiplication = (integer + '*' + integer)[MultExp]
expression = multiplication | addition

parser = generate[Exp](expression)
``

