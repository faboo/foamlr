from lrparser import generate, NoMatchException, P, T, R, RECURSE, Nonterminal

integer = R('integer', '[+-]?[0-9]+')
real = R('float', r'[+-]?[0-9]+\.[0-9]+')
string = R('string', r'"(\\"|[^"])*"')
operator = R('operator', '[-+*/|&^$@?~=<>]+', '=|!')
identifier = R(
    'identifier',
    '[_a-zA-Z][_a-zA-Z0-9]*',
    'exit|help|import|let|if|then|else|try')

expr = Nonterminal('expression')

constant = Nonterminal('constant',
    string,
    integer,
    real,
    )

boolean = Nonterminal('boolean',
    T('!') * expr,
    )

objectRef = Nonterminal('object-ref',
    identifier,
    RECURSE * '.' * identifier, # TODO: lvalue . identifier
    )

elementList = Nonterminal('element list',
    RECURSE * ',' * expr,
    expr
    )
array = Nonterminal('array',
    (T('[') * elementList * ']'),
    (T('[') * ']'),
    )

tryex = Nonterminal('try',
    T('try') * expr,
    )

ifthen = Nonterminal('if statement',
    T('if') * expr * 'then' * expr * 'else' * expr,
    )

subscript = Nonterminal('subscript',
    expr * '[' * expr * ']',
    )

paramList = Nonterminal('parameter list',
    identifier,
    RECURSE * ',' * identifier,
    )
closurePreamble = Nonterminal('closure preamble',
    T('\\') * paramList * '.',
    T('\\') * '.',
    )
closure = Nonterminal('closure',
    closurePreamble * expr,
    )

arg = Nonterminal('key arg',
    identifier * ':' * expr,
    )
argList = Nonterminal('key args',
    arg,
    RECURSE * ',' * arg,
    )
args = Nonterminal('args',
    T('(') * elementList * ',' * argList * ')',
    T('(') * elementList * ')',
    T('(') * argList * ')',
    T('(') * ')',
    )
funcall = Nonterminal('call',
    expr * args,
    )

opcall = Nonterminal('operation',
    expr * operator * expr,
    )

dictObject = Nonterminal('object',
    P* '{' * argList * '}',
    T('{') * '}',
    )

lvalue = Nonterminal('lvalue',
    objectRef,
    funcall,
    #exr, ?
    )

group = Nonterminal('group',
    T('(') * expr * ')',
    )

assign = Nonterminal('assignment',
    lvalue * '=' * expr,
    )

expr.fill(
    array,
    dictObject,
    constant,
    closure,
    boolean,
    tryex,
    ifthen,
    subscript,
    funcall,
    opcall,
    group,
    objectRef,
    )

block = Nonterminal('block')
block.fill(
    expr,
    block * ';' * expr,
    )

describe = Nonterminal('help',
    T('help') * expr,
    T('help'),
    )

statement = Nonterminal('statement',
    describe,
    T('exit'),
    T('import') * identifier,
    T('let') * identifier,
    T('let') * identifier * '=' * expr,
    block
    )


def test_generate():
    parser = generate(statement)

def test_exit():
    parser = generate(statement)
    result = parser.parseString('exit')
    assert 'exit' == result

def test_define():
    parser = generate(statement)
    result = parser.parseString('let qux')
    assert result == ['let', 'qux']

def test_define_and_assign():
    parser = generate(statement)
    result = parser.parseString('let foo = 12')
    assert result == ['let', 'foo', '=', '12']

    result = parser.parseString('let baz= bar')
    assert result == ['let', 'baz', '=', 'bar']

def test_import():
    parser = generate(statement)
    result = parser.parseString('import package')
    assert result == ['import', 'package']

def test_boolean():
    parser = generate(statement)
    result = parser.parseString('!value')
    assert result == ['!', 'value']

def test_object_ref():
    parser = generate(statement)
    result = parser.parseString('object.value')
    assert result == ['object', '.', 'value']

def test_array():
    parser = generate(statement)

    result = parser.parseString('[]')
    assert result == ['[', ']']

    result = parser.parseString('[1]')
    assert result == ['[', '1', ']']

    result = parser.parseString('[1, 2, 3]')
    assert result == ['[', [['1', ',', '2'], ',', '3'], ']']

def test_dictObject():
    parser = generate(statement)

    result = parser.parseString('{}')
    assert result == ['{', '}']

    result = parser.parseString('{a: 1}')
    assert result == ['{', ['a', ':', '1'], '}']

def test_closure():
    parser = generate(statement)
    
    result = parser.parseString(r'\x. x')
    assert result == [['\\', 'x', '.'], 'x']

    result = parser.parseString(r'\. x')
    assert result == [['\\', '.'], 'x']

def test_group():
    parser = generate(statement)
    
    result = parser.parseString('(1)')
    assert result == ['(', '1', ')']
    
def test_block():
    parser = generate(statement)
    
    result = parser.parseString('1; 2')
    assert result == ['1', ';', '2']
    
def test_opcall():
    parser = generate(statement)
    
    result = parser.parseString('1 + 2')
    assert result == ['1', '+', '2']
    
def test_funcall():
    parser = generate(statement)
    
    result = parser.parseString('foo()')
    assert result == ['foo', ['(', ')']]
    
    result = parser.parseString('foo(1)')
    assert result == ['foo', ['(', '1', ')']]
    
    result = parser.parseString('foo(1, 2)')
    assert result == ['foo', ['(', ['1', ',', '2'], ')']]
    
    result = parser.parseString('foo(a: 1)')
    assert result == ['foo', ['(', ['a', ':', '1'], ')']]
    
    result = parser.parseString('foo(1, a: 2)')
    assert result == ['foo', ['(', '1', ',', ['a', ':', '2'], ')']]
    
def test_opcall():
    parser = generate(statement)
    
    result = parser.parseString('1 + 2')
    assert result == ['1', '+', '2']
    
def test_subscript():
    parser = generate(statement)
    
    result = parser.parseString('foo[1]')
    assert result == ['foo', '[', '1', ']']
    
def test_ifthen():
    parser = generate(statement)
    
    result = parser.parseString('if foo then 1 else 2')
    assert result == ['if', 'foo', 'then', '1', 'else', '2']
    
def test_tryex():
    parser = generate(statement)
    
    result = parser.parseString('try foo()')
    assert result == ['try', ['foo', ['(', ')']]]

