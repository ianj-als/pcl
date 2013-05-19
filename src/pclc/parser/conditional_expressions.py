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
from entity import Entity


AND = "and"
OR = "or"
XOR = "xor"
EQUALS = "=="
NOT_EQUALS = "!="
GREATER_THAN = ">"
LESS_THAN = "<"
GREATER_THAN_EQUAL_TO = ">="
LESS_THAN_EQUAL_TO = "<="


class ConditionalExpression(Entity):
    def __init__(self, filename, lineno, left_expr, right_expr, operator):
        Entity.__init__(self, filename, lineno)
        self.left = left_expr
        self.right = right_expr
        self.operator = operator

    def accept(self, visitor):
        self.left.accept(visitor)
        self.right.accept(visitor)
        visitor.visit(self)

    def __str__(self):
        return "(%s %s %s)" % (self.left, self.operator, self.right)

    def __repr__(self):
        return "<ConditionalExpression: op = %s, left = %s, right = %s, entity = %s>" % \
               (self.operator,
                self.left.__repr__(),
                self.right.__repr__(),
                super(ConditionalExpression, self).__repr__())

class AndConditionalExpression(ConditionalExpression):
    def __init__(self, filename, lineno, left_expr, right_expr):
        ConditionalExpression.__init__(self, filename, lineno, left_expr, right_expr, AND)

class OrConditionalExpression(ConditionalExpression):
    def __init__(self, filename, lineno, left_expr, right_expr):
        ConditionalExpression.__init__(self, filename, lineno, left_expr, right_expr, OR)

class XorConditionalExpression(ConditionalExpression):
    def __init__(self, filename, lineno, left_expr, right_expr):
        ConditionalExpression.__init__(self, filename, lineno, left_expr, right_expr, XOR)

class EqualsConditionalExpression(ConditionalExpression):
    def __init__(self, filename, lineno, left_expr, right_expr):
        ConditionalExpression.__init__(self, filename, lineno, left_expr, right_expr, EQUALS)

class NotEqualsConditionalExpression(ConditionalExpression):
    def __init__(self, filename, lineno, left_expr, right_expr):
        ConditionalExpression.__init__(self, filename, lineno, left_expr, right_expr, NOT_EQUALS)

class GreaterThanConditionalExpression(ConditionalExpression):
    def __init__(self, filename, lineno, left_expr, right_expr):
        ConditionalExpression.__init__(self, filename, lineno, left_expr, right_expr, GREATER_THAN)

class LessThanConditionalExpression(ConditionalExpression):
    def __init__(self, filename, lineno, left_expr, right_expr):
        ConditionalExpression.__init__(self, filename, lineno, left_expr, right_expr, LESS_THAN)

class GreaterThanEqualToConditionalExpression(ConditionalExpression):
    def __init__(self, filename, lineno, left_expr, right_expr):
        ConditionalExpression.__init__(self, filename, lineno, left_expr, right_expr, GREATER_THAN_EQUAL_TO)

class LessThanEqualToConditionalExpression(ConditionalExpression):
    def __init__(self, filename, lineno, left_expr, right_expr):
        ConditionalExpression.__init__(self, filename, lineno, left_expr, right_expr, LESS_THAN_EQUAL_TO)

class UnaryConditionalExpression(Entity):
    def __init__(self, filename, lineno, expression):
        Entity.__init__(self, filename, lineno)
        self.expression = expression

    def accept(self, visitor):
        self.expression.accept(visitor)
        visitor.visit(self)

    def __str__(self):
        return "(%s)" % self.expression

    def __repr__(self):
        return "<UnaryConditionalExpression: expr = %s, entity = %s>" % \
               (self.expression.__repr__(),
                super(UnaryConditionalExpression, self).__repr__())

class TerminalConditionalExpression(Entity):
    def __init__(self, terminal):
        Entity.__init__(self, terminal.filename, terminal.lineno)
        self.terminal = terminal

    def accept(self, visitor):
        visitor.visit(self)

    def __str__(self):
        return str(self.terminal)

    def __repr__(self):
        return "<TerminalConditionalExpression: terminal = %s, entity = %s>" % \
               (self.terminal.__repr__(),
                super(TerminalConditionalExpression, self).__repr__())
