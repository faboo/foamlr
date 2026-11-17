from lrparser import generate, NoMatchException, T, R, Nonterminal

integer = R('integer', '[+-]?[0-9]+')
real = R('float', r'[+-]?[0-9]+\.[0-9]+')
string = R('string', r'"(\\"|[^"])*"')
operator = R('operator', '[-+*/|&^$@?~=<>]+')
identifier = R('identifier', '[_a-zA-Z][_a-zA-Z0-9]*')

expr = Nonterminal('expression')

constant = Nonterminal('constant',
    string,
    integer,
    real,
    )

boolean = Nonterminal('boolean',
    T('!') * expr,
    )

objectRef = Nonterminal('object-ref')
objectRef.fill(
    identifier,
    objectRef * '.' * identifier,
    )

elementList = Nonterminal('element list')
elementList.fill(
    elementList * ',' * expr,
    expr
    )
array = Nonterminal('array',
    (T('[') * elementList * ']'),
    (T('[') * ']'),
    )

expr.fill(
    identifier,
    constant,
    array,
    boolean,
    objectRef,
    )

describe = Nonterminal('help',
    T('help') * expr,
    T('help'),
    )

statement = Nonterminal('statement',
    T('exit'),
    T('import') * identifier,
    describe,
    T('let') * identifier * '=' * expr,
    expr
    )


def test_generate():
    parser = generate(statement)

def test_exit():
    parser = generate(statement)
    result = parser.parseString('exit')
    assert 'exit' == result

def test_define():
    parser = generate(statement)
    result = parser.parseString('let foo = 12')
    assert result == ['let', 'foo', '=', '12']

    result = parser.parseString('let foo = bar')
    assert result == ['let', 'foo', '=', 'bar']

def test_import():
    parser = generate(statement)
    result = parser.parseString('import array')
    assert result == ['import', 'array']

def test_boolean():
    parser = generate(statement)
    result = parser.parseString('!value')
    assert result == ['!', 'value']

def test_object_ref():
    parser = generate(statement)
    result = parser.parseString('object.value')
    assert result == ['object', '.', 'value']
