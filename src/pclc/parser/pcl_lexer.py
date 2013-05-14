#
# Copyright Capita Translation and Interpreting 2013
#
# This file is part of Pipeline Creation Language (PCL).
# 
# Pipeline Creation Language (PCL) is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# Pipeline Creation Language (PCL) is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with Pipeline Creation Language (PCL).  If not, see <http://www.gnu.org/licenses/>.
#
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

    def __init__(self, logger = None, **kwargs):
        if 'debuglog' not in kwargs:
            kwargs['debuglog'] = logger
        if 'errorlog' not in kwargs:
            kwargs['errorlog'] = logger
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
    import a.b.c as d
    component e
    inputs f, g
    output h
    configuration i,j,k,l
    declare
      a := new m with n -> o.p.q, r -> s
      b := new t
    as
      (wire a -> b, c -> d &&& wire a -> b) >>>
      merge top[a] -> b, -7 -> v, -7.9e-9 -> a, "h'e'\"l\"ox" -> b, "" -> u >>> v''')
    while True:
        token = lexer.token()
        if not token:
            break
        print token
