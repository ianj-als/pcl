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
from multimethod import multimethod, multimethodclass
from parser.import_spec import Import
from parser.command import Function, Command, Return, IfCommand, LetCommand
from parser.component import Component
from parser.conditional_expressions import ConditionalExpression, \
     UnaryConditionalExpression, \
     TerminalConditionalExpression
from parser.declaration import Declaration
from parser.expressions import UnaryExpression, \
     BinaryExpression, \
     CompositionExpression, \
     ParallelWithScalarExpression, \
     FirstExpression, \
     SecondExpression, \
     SplitExpression
from pypeline.core.types.just import Just
from pypeline.core.types.nothing import Nothing
from first_pass_resolver_visitor import FirstPassResolverVisitor


@multimethodclass
class SecondPassResolverVisitor(FirstPassResolverVisitor):
    def __init__(self):
        FirstPassResolverVisitor.__init__(self, None)

    @multimethod(Import)
    def visit(self, an_import):
        pass

    @multimethod(Component)
    def visit(self, component):
        pass

    @multimethod(Declaration)
    def visit(self, decl):
        pass

    @multimethod(object)
    def visit(self, nowt):
        pass

    def __derive_inputs(self, expr):
        return self.__walk_expression(expr.parent, expr)

    def __walk_expression(self, node, child):
        if node is None:
            return Just(frozenset(self._module.definition.inputs))

        if isinstance(node, ParallelWithScalarExpression):
            if node.resolution_symbols.has_key('inputs') and \
               not isinstance(node.resolution_symbols['inputs'], Nothing):
                return node.resolution_symbols['inputs']
        elif isinstance(node, BinaryExpression):
            if node.left is child:
                if node.resolution_symbols.has_key('inputs') and \
                   not isinstance(node.resolution_symbols['inputs'], Nothing):
                    return node.resolution_symbols['inputs']
            elif node.right is child:
                if node.left.resolution_symbols.has_key('outputs') and \
                   not isinstance(node.left.resolution_symbols['outputs'], Nothing):
                    return node.left.resolution_symbols['outputs']
            else:
                raise Exception("Child is neither left or right: %s" % child.__repr__())
        elif isinstance(node, UnaryExpression):
            pass
        else:
            raise Exception("Unexpected expression type: %s" % type(node))

        return self.__walk_expression(node.parent, node)

    @multimethod(FirstExpression)
    def visit(self, first_expr):
        top_inputs = first_expr.expression.resolution_symbols['inputs']
        top_outputs = first_expr.expression.resolution_symbols['outputs']

        # Derive the bottom inputs
        inputs = self.__derive_inputs(first_expr)
        bottom_inputs = inputs >= (lambda ins: Just(frozenset(ins[1])) if isinstance(ins, tuple) \
                                   else Just(frozenset(ins)))

        first_expr.resolution_symbols['inputs'] = top_inputs >= (lambda tins: bottom_inputs >= \
                                                                 (lambda bins: Just((tins, bins))))
        first_expr.resolution_symbols['outputs'] = top_outputs >= (lambda touts: bottom_inputs >= \
                                                                   (lambda bouts: Just((touts, bouts))))

    @multimethod(SecondExpression)
    def visit(self, second_expr):
        # Derive the top inputs
        inputs = self.__derive_inputs(second_expr)
        top_inputs = inputs >= (lambda ins: Just(frozenset(ins[0])) if isinstance(ins, tuple) \
                                else Just(frozenset(ins)))

        bottom_inputs = second_expr.expression.resolution_symbols['inputs']
        bottom_outputs = second_expr.expression.resolution_symbols['outputs']

        second_expr.resolution_symbols['inputs'] = top_inputs >= (lambda tins: bottom_inputs >= \
                                                                  (lambda bins: Just((tins, bins))))
        second_expr.resolution_symbols['outputs'] = top_inputs >= (lambda touts: bottom_outputs >= \
                                                                   (lambda bouts: Just((touts, bouts))))

    @multimethod(SplitExpression)
    def visit(self, split_expr):
        # Derive the inputs
        inputs = self.__derive_inputs(split_expr)
        split_expr.resolution_symbols['inputs'] = inputs
        split_expr.resolution_symbols['outputs'] = inputs >= (lambda ins: Just((ins, ins)))

    @multimethod(TerminalConditionalExpression)
    def visit(self, term_cond_expr):
        pass

    @multimethod(Function)
    def visit(self, function):
        pass

    @multimethod(Command)
    def visit(self, command):
        pass

    @multimethod(Return)
    def visit(self, ret):
        pass

    @multimethod(IfCommand)
    def visit(self, if_command):
        pass

    @multimethod(IfCommand.ThenBlock)
    def visit(self, then_block):
        pass

    @multimethod(IfCommand.ElseBlock)
    def visit(self, else_block):
        pass

    @multimethod(IfCommand.EndIf)
    def visit(self, end_if):
        pass

    @multimethod(LetCommand)
    def visit(self, let_command):
        pass

    @multimethod(LetCommand.LetBindings)
    def visit(self, let_bindings):
        pass

    @multimethod(LetCommand.LetEnd)
    def visit(self, let_end):
        pass
