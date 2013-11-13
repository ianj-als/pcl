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
import datetime
import os

from parser.conditional_expressions import ConditionalExpression, \
     AndConditionalExpression, \
     OrConditionalExpression, \
     XorConditionalExpression, \
     EqualsConditionalExpression, \
     NotEqualsConditionalExpression, \
     GreaterThanConditionalExpression, \
     LessThanConditionalExpression, \
     GreaterThanEqualToConditionalExpression, \
     LessThanEqualToConditionalExpression, \
     UnaryConditionalExpression, \
     TerminalConditionalExpression
from parser.expressions import StateIdentifier, Identifier, Literal
from scoped_name_generator import ScopedNameGenerator


class ExecutorVisitor(object):
    __INDENTATION = "  "
    __HEADER = "#\n" \
               "# DO NOT EDIT THIS FILE!\n" \
               "#\n" \
               "# This file was automatically generated by PCLc on\n" \
               "# %(datetime)s.\n" \
               "#\n"

    def __init__(self, filename_root, variable_name_generator, imports = "", is_instrumented = False):
         # Check that the __init__.py file exists in the
        # working directory
        if os.path.isfile('__init__.py') is False:
            open('__init__.py', 'w').close()
        self._object_file = open('%s.py' % filename_root, 'w')
        self._indent_level = 0
        
        # Variable generation
        self._variable_generator = variable_name_generator

        # Write header to object file
        header_args = {'datetime' : \
                       datetime.datetime.now().strftime("%A %d %B %Y at %H:%M:%S")}
        self._write_line((ExecutorVisitor.__HEADER + imports) % header_args)

        # Instrumented object code?
        self._is_instrumented = is_instrumented

        # Python conditional operators
        self.__conditional_operators = {AndConditionalExpression : 'and',
                                        OrConditionalExpression : 'or',
                                        XorConditionalExpression : '^',
                                        EqualsConditionalExpression : '==',
                                        NotEqualsConditionalExpression : '!=',
                                        GreaterThanConditionalExpression : '>',
                                        LessThanConditionalExpression : '<',
                                        GreaterThanEqualToConditionalExpression : '>=',
                                        LessThanEqualToConditionalExpression : '<='}

    def _write_line(self, stuff = ""):
        with_indents = "%s%s\n" % (ExecutorVisitor.__INDENTATION * self._indent_level, \
                                   stuff)
        self._object_file.write(with_indents)

    def _write_lines(self, lines):
        if isinstance(lines, list) or \
           isinstance(lines, tuple):
            for line, indent_step in lines:
                if line is not None:
                    self._write_line(line)
                if indent_step == "+":
                    self._incr_indent_level()
                elif indent_step == "-":
                    self._decr_indent_level()
        else:
            self._write_line(lines)

    def _incr_indent_level(self):
        self._indent_level += 1

    def _decr_indent_level(self):
        self._indent_level -= 1
        if self._indent_level < 1:
            self._reset_indent_level()

    def _reset_indent_level(self):
        self._indent_level = 0

    def _write_function(self, fn_name, body_lines, arguments = []):
        self._reset_indent_level()
        self._write_line("def %s(%s):" % (fn_name, ", ".join(arguments)))
        self._incr_indent_level()
        self._write_lines(body_lines)
        self._write_line()

    def _generate_terminal(self, terminal, scope = None):
        if isinstance(terminal, StateIdentifier):
            return "s['%s']" % terminal.identifier
        elif scope is not None and isinstance(terminal, Identifier) and terminal in scope:
            return self._variable_generator.lookup_name(terminal, scope)
        elif isinstance(terminal, Identifier):
            return "a['%s']" % terminal
        elif isinstance(terminal, Literal):
            return str(terminal)
        else:
            raise ValueError("Unexpected terminal in conditional: filename = %s, line no = %d" % \
                             (terminal.filename, terminal.lineno))

    def _generate_condition(self, cond_expr, scope = None):
        # Terminal!
        if isinstance(cond_expr, TerminalConditionalExpression):
            return self._generate_terminal(cond_expr.terminal, scope)
        elif isinstance(cond_expr, ConditionalExpression):
            left_code = self._generate_condition(cond_expr.left, scope)
            right_code = self._generate_condition(cond_expr.right, scope)
            op = self.__conditional_operators[cond_expr.__class__]
            if isinstance(cond_expr, XorConditionalExpression):
                left_code = "bool(%s)" % left_code
                right_code = "bool(%s)" % right_code
            return "(%s %s %s)" % (left_code, op, right_code)
        elif isinstance(cond_expr, UnaryConditionalExpression):
            return "(%s)" % self._generate_condition(cond_expr.expression, scope)
        else:
            raise ValueError("Unexpected expression in conditional: filename = %s, line no = %d" % \
                             (cond_expr.filename, cond_expr.lineno))
