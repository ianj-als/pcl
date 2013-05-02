#
# Pipeline Creation Language Lexical Analysis
#
import sys
import ply.lex as lex


#
# Reserved words
#
reserved = {
    'as' : 'AS',
    'bottom' : 'BOTTOM',
    'component' : 'COMPONENT',
    'configuration' : 'CONFIGURATION',
    'declare' : 'DECLARE',
    'first' : 'FIRST',
    'import' : 'IMPORT',
    'input' : 'INPUTS',
    'inputs' : 'INPUTS',
    'merge' : 'MERGE',
    'new' : 'NEW',
    'output' : 'OUTPUTS',
    'outputs' : 'OUTPUTS',
    'second' : 'SECOND',
    'split' : 'SPLIT',
    'top' : 'TOP',
    'wire' : 'WIRE',
    'with' : 'WITH'}

#
# Tokens
#
tokens = [
    'ASSIGN',
    'QUALIFIED_IDENTIFIER', 'IDENTIFIER',
    'COMPOSITION',
    'FLOAT',
    'INTEGER',
    'MAPS_TO',
    'PARALLEL_WITH_TUPLE',
    'PARALLEL_WITH_SCALAR',
    'STRING'] + list(reserved.values())


class PCLLexer(object):
    tokens = tokens

    literals = ",()[]"

    t_ASSIGN = r':='
    t_COMPOSITION = r'>>>'
    t_MAPS_TO = r'->'
    t_PARALLEL_WITH_TUPLE = r'\*\*\*'
    t_PARALLEL_WITH_SCALAR = r'&&&'

    t_ignore_COMMENT = r'\#.*'
    t_ignore  = ' \t\r'

    def t_QUALIFIED_IDENTIFIER(self, t):
        r'([a-zA-Z_][a-zA-Z0-9_]*(\.[a-zA-Z_][a-zA-Z0-9_]*)+)'
        return t

    def t_IDENTIFIER(self, t):
        r'[a-zA-Z_][a-zA-Z0-9_]*'
        t.type = reserved.get(t.value, 'IDENTIFIER')
        return t

    def t_FLOAT(self, t):
        r'[-]?\d+\.\d+?([eE][-+]\d+)?'
        t.value = float(t.value)
        return t

    def t_INTEGER(self, t):
        r'[-]?\d+'
        t.value = int(t.value)
        return t

    def t_STRING(self, t):
        r'"(\\.|[^"])*"'
        t.value = t.value[1:-1].replace("\\", "")
        return t

    def t_newline(self, t):
        r'\n+'
        t.lexer.lineno += len(t.value)

    def t_error(self, t):
        print >> sys.stderr, "Illegal character [%s] at line [%d]" % \
              (t.value[0], self.__lexer.lineno)
        t.lexer.skip(1)

    def __init__(self, **kwargs):
        self.__lexer = lex.lex(module = self, **kwargs)

    def input(self, input):
        self.__lexer.input(input)

    def token(self):
        return self.__lexer.token()

    def getLexer(self):
        return self.__lexer


if __name__ == "__main__":
    lexer = PCLLexer(debug = 1)
    lexer.input(r'''
    import twat.arse.feck as bum
    component arse
    inputs a, b
    output c
    configuration a,b,c,d
    declare
      a := new arse with a -> b.d.c c -> d
      b := new bum
    as
      (wire a -> b, c -> d &&& wire a -> b) >>>
      merge top[a] -> bollox, -7 -> v, -7.9e-9 -> arse, "b'o'\"l\"lox" -> bum, "" -> feck >>> arse''')
    while True:
        token = lexer.token()
        if not token:
            break
        print token
