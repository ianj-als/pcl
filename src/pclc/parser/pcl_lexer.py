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
    'and' : 'AND',
    'as' : 'AS',
    'bottom' : 'BOTTOM',
    'component' : 'COMPONENT',
    'configuration' : 'CONFIGURATION',
    'declare' : 'DECLARE',
    'do' : 'DO',
    'endif' : 'ENDIF',
    'else' : 'ELSE',
    'first' : 'FIRST',
    'import' : 'IMPORT',
    'if' : 'IF',
    'in' : 'IN',
    'input' : 'INPUTS',
    'inputs' : 'INPUTS',
    'let' : 'LET',
    'merge' : 'MERGE',
    'new' : 'NEW',
    'or' : 'OR',
    'output' : 'OUTPUTS',
    'outputs' : 'OUTPUTS',
    'return' : 'RETURN',
    'second' : 'SECOND',
    'split' : 'SPLIT',
    'then' : 'THEN',
    'top' : 'TOP',
    'wire' : 'WIRE',
    'with' : 'WITH',
    'xor' : 'XOR'}

#
# Tokens
#
tokens = [
    'ASSIGN',
    'EQUALS',
    'NOT_EQUALS',
    'GT', 'LT', 'G_EQUAL', 'L_EQUAL',
    'LEFT_ARROW',
    'QUALIFIED_IDENTIFIER', 'IDENTIFIER',
    'COMPOSITION',
    'FLOAT',
    'INTEGER',
    'BOOLEAN',
    'MAPS_TO',
    'PARALLEL_WITH_TUPLE',
    'PARALLEL_WITH_SCALAR',
    'STRING'] + list(reserved.values())


class PCLLexer(object):
    tokens = tokens

    literals = ",()[]@"

    t_ASSIGN = r':='
    t_EQUALS = r'=='
    t_NOT_EQUALS = r'!='
    t_GT = r'>'
    t_LT = r'<'
    t_G_EQUAL = r'>='
    t_L_EQUAL = r'<='
    t_LEFT_ARROW = r'<-'
    t_COMPOSITION = r'>>>'
    t_MAPS_TO = r'->'
    t_PARALLEL_WITH_TUPLE = r'\*\*\*'
    t_PARALLEL_WITH_SCALAR = r'&&&'

    t_ignore_COMMENT = r'\#.*'
    t_ignore  = ' \t\r'

    def t_BOOLEAN(self, t):
        r'([Tt][Rr][Uu][Ee]|[Ff][Aa][Ll][Ss][Ee])'
        t.value = True if t.value.upper() == "TRUE" else False
        return t

    def t_QUALIFIED_IDENTIFIER(self, t):
        r'([a-zA-Z_][a-zA-Z0-9_]*(\.[a-zA-Z_][a-zA-Z0-9_]*)+)'
        return t

    def t_IDENTIFIER(self, t):
        r'[a-zA-Z_][a-zA-Z0-9_]*'
        t.type = reserved.get(t.value, 'IDENTIFIER')
        return t

    def t_FLOAT(self, t):
        r'[-]?\d+\.\d+([eE][-+]?\d+)?'
        t.value = float(t.value)
        return t

    def t_INTEGER(self, t):
        r'[-]?\d+'
        t.value = int(t.value)
        return t

    def t_STRING(self, t):
        r'"(\\.|[^"])*"'
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
