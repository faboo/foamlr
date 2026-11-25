# Foamlr

Foamlr is a python LR-1, reduce-shift parser generator. The generated parser reads text streams or raw strings and
outputs either a list-based parse tree or a custom object if producers are provided to the grammar rules.


# Basic Example

A simple arithmatic parser:

```
from foamlr import ReToken, Nonterminal, RECURSE, P

# First, we define the grammar

integer = ReToken('integer', '[0-9]+')

arithmetic = Nonterminal('arithemtic')

value = Nonterminal('value',
    integer,
    P* '-' * RECURSE,
    P* '(' * arithemtic * ')',
    )

multiplication = Nonterminal('multiplication',
    value * '*' * value,
    value * '/' * value,
    )

arithmetic.fill(
    multiplication * '+' * multiplication,
    multiplication * '-' * multiplication,
    )

# Then, we can generate a parser from the grammar
parser:Parser = generate(arithmetic)

# With the parser, we can parse a string into parse tree
tree:list = parser.parseString("2 * (7 - 4)")
```

In this example we didn't provide constuctors to the grammar rules, so the final value of `tree` is a parse tree:

     ['2' '*' ['(' ['7' '-' '4'] ')']]


# API

## Parser creation
```
# Create a Parser object from a grammar.
def generate(grammar:Nonterminal) -> Parser

class Parser:
    # Parse directly from a string
    def parseString(input:str) -> object

    # Parse text from a file, given a filename or stream object
    def parseFile(file:str|Stream) -> object

    # Set whitespace characters (default: ' \t\n') that are automatically skipped between rules.
    # Set to None to 
    def setWhite(whitespace:str|None) -> None
```

### Tokens (Terminals)

Foamlr handles tokenization directly. Defined tokens can be used directly as symbols in a grammar.

```
# Match an exact string in the input. The result of these tokens is always the provided string.
class Token(TokenRule):
    def __init__(self, string:str)
```

```
# Match a regular expression in the input. 
class ReToken(TokenRule):
    def __init__(self, name:str, regex:str)
```

Plain tokens don't usually need to be defined explicitly - plain strings will be converted internally to `Token` objects.

For convenience, `Token` and `ReToken` can be imported as `T` and `R` respectively.

### Nonterminals (Grammars) and Productions

Grammars are built from "non-terminal" symbols and productions. Non-terminals start with a name (for logging):

```
grammar = Nonterminal('grammar',
    ...
    )
```

The remaining arguments are the various productions that define the non-terminal. Productions are a series of symbols (Tokens/ReTokens and Nonterminals) combined with '*'. From our arithmetic example:

```
multiplication * '+' * multiplication
```

Here, the production matches a "multiplication" non-terminal (defined previously), followed by a '+' character and another "multiplication" non-terminal. Any whitespace between symbols is skipped automatically. (Use `setWhite()` on the generated parser to change what is considered whitespace.)

Bare strings are converted to Tokens internally, but productions that begin with a token either  need to start with an explicit Token, or the production must begin with the production leader `P`. For example:

```
numeral = R('numeral', '[1-9][0-9]*')
integers = Nonterminal('integers',
    Token('+') * numeral,
    T('-') * numeral,
    P* '~' * numeral,
    )
```

### Recursion

You can define a Nonterminal seperately from filling in its productions, letting using it recursively, including in other Nonterminal's productions. From the arithmetic example:

```
arithmetic = Nonterminal('arithemtic')

...

arithmetic.fill(
    multiplication * '+' * multiplication,
    multiplication * '-' * multiplication,
    )
```

As a shortcut, if a Nonterminal is only directly recursive the RECURSE constant can be used as a stand-in for current Nonterminal. For example:

```
numeral = R('numeral', '[1-9][0-9]*')
integers = Nonterminal('integers',
    numeral,
    P* '-' * RECURSE,
    )
```

## Custom parse trees

By default, a production produces a list containing each parsed symbol in order. A custom producer set for a production with the `@` operator:

```
class AddExp:
    def __init__(self, left:int, op:str, right:int) -> None:
        self.left = left
        self.right = right

class SubExp:
    def __init__(self, left:int, op:str, right:int) -> None:
        self.left = left
        self.right = right

integerT = ReToken('integer', '[0-9]+')
integer = Nonterminal('integer',
    integerT @ int,
    )

arithmetic = Nonterminal('arithemtic')
    integer * '+' * integer @ AddExp,
    integer * '-' * integer @ SubExp,
    )
```

## Anonymous Non-terminals

If what you need is a quick and dirty recognizer or very simple parser, you can simplify grammar definitions by embedding anonymous non-terminals within productions with the `|` (choice) operator. With `|` you can embed alternative productions. Consider this very simple grammar:

```
a = T('a')
b = T('b')
S = Nonterminal('S',
    a,
    b,
    )
X = Nonterminal('X',
    P* '[' * S * ']',
    )
```

This can be rewritten as:

```
a = T('a')
b = T('b')
X = Nonterminal('X',
    P* '[' * (a | b) * ']',
    )
```

The construction `a | b` is an anonymous Nonterminal equivalent to `S` above. We can even embed custom producers within the anonymous Nonterminal, or use `RECURSE` within one if we're feeling brave.

```
def string(raw):
    return raw[1:-1]

assign = Nonterminal('assign',
    R('[a-z]+') * '=' * 
        ( R('[0-9]+') @ int 
        | R('"[^"]"') @ string
        ) * ';'
    )
```

Note that using `RECURSE` within an anonymous Nonterminal recurses within the anonymous Nonterminal, *not* the outer, named Nonterminal.

```
ident = R('[a-z]+')
list = Nonterminal('list',
    P* '[' * (ident | RECURSE * ',' * ident) * ']',
    )
```



# Copyright

Comber copyright 2025 Ray Wallace III

This library is free software; you can redistribute it and/or modify it under the terms of the GNU Lesser General Public License as published by the Free Software Foundation, **version 2.1**.
                                                                          
This library is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more details.
                                                                          
You should have received a copy of the GNU Lesser General Public License along with this library; if not, write to the Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301 USA
