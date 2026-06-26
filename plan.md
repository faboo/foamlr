# LRParser Implementation Plan

## Overview

Implement an LR(1) parser generator that builds parse tables from grammar rules and produces a runtime Parser class. The library follows the interface specified in Readme.md, supporting token rules, production rules with `+` (sequences) and `|` (alternatives), recursion via DelayedRule, and custom producers via `[ ]`.

---

## Phase 1: Project Setup

### Tasks
- Initialize pyproject.toml-based project structure
- Configure pytest for testing
- Set up basic package layout under `/lrparser/`

### Files to Create
```
pyproject.toml       - Package metadata, dependencies (pytest only)
src/lrparser/__init__.py  - Public API exports
tests/test_*.py      - Test suite
```

---

## Phase 2: Core Data Structures

### Task A: Rule Hierarchy Design

Create the rule class hierarchy that mirrors the grammar definition interface:

1. **Rule** (base/abstract)
   - Interface: combine with `+`, `|`, apply producer `[ ]`

2. **TokenRule** (extends Rule)
   - Base for lexer-level rules that read from input text
   
3. **ConstToken** (extends TokenRule)
   - Matches exact literal strings
   - Stores the string to match and return value

4. **ReToken** (extends TokenRule)  
   - Uses compiled regex pattern
   - Needs efficient matching at parse boundary position

5. **DelayedRule** (extends Rule)
   - Forward-reference placeholder for recursive grammars
   - `fill(production)` injects the resolved rule
   - Internally tracks whether filled/ready to use

6. **Sequence** (extends ProductionRule)
   - Represents: rule1 + rule2 + ...
   - Stores ordered list of child rules
   
7. **Alternative** (extends ProductionRule)  
   - Represents: rule1 | rule2 | ...
   - Stores choices; tries first match at parse time

### Key Decisions
- Rules are immutable once constructed, except DelayedRule before fill()
- Each Rule has a unique ID for table generation bookkeeping
- Optional producer function transforms children's results into custom object

---

## Phase 3: Grammar Normalization (Internal Representation)

LR tables require grammar in canonical form. Need to convert user-facing rules to LR notation:

### Task A: Flatten Rules

Transform arbitrary nested productions into basic production items:

```
User writes:   expr = num + '*' + expr | num
Becomes:       E' → expr (start symbol)
               expr → num '*' expr
               expr → num
               num  → RE[0-9]+
```

### Task B: Handle DelayedRule

1. Collect all DelayedRules during rule construction
2. Build topological dependency order  
3. Resolve each by substituting its filled production into reference sites
4. Detect infinite recursion or unfilled delayed rules (error)

---

## Phase 4: LR(1) Table Construction

This is the core of parser generation using standard algorithms from "Dragon Book".

### Task A: Symbol Management

- **Terminal symbols**: token rule types + special whitespace marker if needed
- **Non-terminal symbols**: production rule left-hand sides, plus start symbol E'
- **Lookahead tokens**: for LR(1) items (need first-follow sets or canonical construction)

### Task B: Compute FIRST Sets

For each non-terminal X:
```python
FIRST:: 
  - If α = T... where T is terminal: return {T}
  - If α = ε: add ε to result  
  - Otherwise compute recursively through nullable symbols
```

Needed for FOLLOW and item set computation. (LR(1) uses first/follow propagation.)

### Task C: Compute Canonical LR(1) Items

Item form: `[A → α·β, a]` where `a ∈ TERM ∪ {$}` is lookahead symbol

Use **closure** function to expand items transitively for each rule referenced after the dot.

### Task D: Build Item Sets DFA

- Start state S0 = closure( { [E' → ·expr, $] } )
- Compute GOTO(qi, X) transitions between item sets
- Each reachable set becomes a parser table row

Algorithm:
```python
I0 := CLOSURE({[S' -> .S, $]})   # S is start symbol  
J  := [I0]; i := 1
while J has unmarked subset I do:
    mark I as marked
    for each lookahead a in terminals ∪ {ε}: 
        GOTO(I, X) = K (where X any grammar symbol):    
            if len(K)>0 and K not already defined then  
                i := new state number; assign Ji := CLOSURE(GOTO(I,X)); add to J

    fill action/goto table entries from computed sets
```

### Task E: Populate Parse Tables

Build two tables: **ACTION** (terminals) × states, **GOTO** (non-terminals) × states

- ACTION[state][token] = shift/join/reduce/error entries  
  - Shift S j → goto state when token consumed and push to stack
  - Reduce A→α R k → pop |A→α| items from stack, apply production
  
- GOTO[state][nonterminal[j]] defines next states  

Detect conflicts:

1. **Shift/Reduce**: multiple table actions valid for same cell  
2. **Reduce/Reduce**: two reduction rules applicable simultaneously

Report errors with helpful context if conflicts arise (this is user grammar error)


---
## Phase 5: Runtime Parser Implementation 

After generating tables, implement the shift/reduce parser engine that drives the parse state machine using those tables.

### Task A: Lexer Integration  

Implement scanning pass over input text to yield token objects for terminals. For each position in string: consume optional whitespace chars if enabled by setWhite setting; attempt matching ConstToken (exact strings) or ReToken regex patterns, yielding matched values with their rule type IDs back into parse engine loop.

### Task B: Stack-Based Parser Loop  

Implement standard LR parser algorithm as state machine simulation using ACTION/GOTO tables on runtime stack of "state/rule pairs". On each iteration peek next token/lookahead symbol and consult action table entry to determine shift or reduce operation; repeat until accept, reject parse failure, or error condition detected.

### Task C: Parser State Tracking  

Maintain two stacks during parsing: state stack tracks parser DFA states as we navigate item sets, value accumulator stack holds semantic values being constructed (either list trees for default behavior or custom typed objects when producers are defined in grammar rules).


---
## Phase 6: Public API Implementation

### Task A: Parser Class  
Implement the generated runtime class with methods matching Readme.md interface — parseString() takes raw input text returning parsed result, parseFile() reads from filename or stream object then delegates to string parsing path, setWhite() configuration method controls whitespace skipping (default allows space/tab/newline chars), plus internal tokenizer and driver components.

### Task B: generate() Function  

Grammar compilation entry point that takes a root Rule tree through full pipeline of normalization → table generation errors check for conflicts → instantiates Parser subclass with embedded tables ready to parse input on demand.


---
## Phase 7: Error Handling & Feedback Looping 

Need good error messages when user supplies invalid grammar or bad inputs.

### Task A: Grammar Construction Errors  

Catch and raise descriptive exceptions for unfilled DelayedRules used in final parse table generation, recursive definitions that are truly circular with no base case to terminate expansion attempts, conflicts discovered during table build phase (shift-reduce/reduce-reduce situations indicating ambiguous user grammar).


### Task B: Parsing Runtime Errors

During lexing or shifting detect mismatch between provided input and expected token sequences; construct error message including current position index in text being analyzed plus what rule/token was anticipated when parse algorithm reached dead end.


---
## Phase 8: Testing Strategy  

Write comprehensive pytest coverage across all implementation layers before moving on to optional performance optimizations.

### Task A: Unit Tests for Rule Classes  
Verify DelayedRule fill mechanism resolves forward references properly, operator overloading + and | constructs correct sequence/alternative trees, bracket syntax [ ] applies producer transformers correctly when invoked at parse time construction step.


### Task B: Table Generation Correctness 

Validate generated ACTION/GOTO tables against known grammars (arithmetic expressions with standard precedence rules from Readme example), confirm error reporting surfaces shift-reduce and reduce-reduce conflicts appropriately rather than silently choosing arbitrary resolution option during ambiguous case handling.

  
### Task C: Parsing Output Validation  

Check that parser results match documented examples exactly for simple cases, verify default list tree construction builds nested arrays matching user grammar structure correctly when no custom producers provided to rules in specification phase.  


---
## Phase 9: Performance Notes (Future Work) 


If performance becomes critical later can add caching layers or compiled table variants but prioritize correctness first with this implementation approach.


Key optimization opportunities once baseline works: memoization of closure computations during repeated parses, precompiled regex engine for ReToken patterns to avoid runtime compilation overhead per match, vectorized table lookup instead of dictionary-based dispatch mechanisms in hot code path through parsing loop iterations on large inputs requiring substantial work throughput analysis before investing here though premature.


---
## File Organization Summary  


Final target structure after completing all phases:
```

/Users/raymondwallace/asrc/lrparser/  
├── pyproject.toml        # Package configuration, pytest dependency only  
├── plan.md              # This document outlining implementation approach  
└── README.md             # User-facing documentation from initial requirement specification  

src/ 
  └── lrparser/__init__.py   # Main package - exports Parser, generate(), all Rule classes to public API  


tests/                 
  ├── test_rule_construction.py     # Testing grammar building operations: sequences, alternatives, delayed rules  
  ├── test_parser_generation.py      # Validate LR table construction correctness and conflict detection mechanisms
```

This architecture separates the rule definition DSL from internal compiler stages (normalization then canonical item set computation), keeps generated parse tables encapsulated within instantiated Parser objects for each compiled grammar variant being tested or deployed in production code scenarios requiring robust error diagnostics during development cycles when building new language parsers with this framework infrastructure.


---
## Implementation Notes  

- DelayedRule can be filled only once before parser table generation begins - document and enforce single assignment constraint in code with clear error messaging if attempted twice during grammar specification phase
```
