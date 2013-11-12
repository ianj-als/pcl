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
from parser.component import Component
from parser.conditional_expressions import AndConditionalExpression, \
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
from parser.declaration import Declaration
from parser.expressions import CompositionExpression, \
     ParallelWithScalarExpression, \
     IfExpression, \
     Identifier, \
     StateIdentifier
from pypeline.core.types.just import Just
from pypeline.core.types.nothing import Nothing
from first_pass_resolver_visitor import type_formatting_fn
from second_pass_resolver_visitor import SecondPassResolverVisitor


@multimethodclass
class ThirdPassResolverVisitor(SecondPassResolverVisitor):
    def __init__(self):
        SecondPassResolverVisitor.__init__(self)

    @multimethod(object)
    def visit(self, nowt):
        if self._module.definition.is_leaf:
            return

        # Root expression, so get inputs and outpus
        # from module defined inputs and outputs clauses
        expr = self._module.definition.definition
        # Place the input/output specifications in a Maybe monad
        expected_fn = lambda e: Just((frozenset(e[0]), frozenset(e[1]))) \
                      if isinstance(e, tuple) else Just(frozenset(e))
        self._module.resolution_symbols['inputs'] = expected_fn(self._module.definition.inputs) >= \
                                                    (lambda expected_inputs: expr.resolution_symbols['inputs'] >= \
                                                     (lambda actual_inputs: self._add_errors("ERROR: %(filename)s at line %(lineno)d, component " \
                                                                                             "defines mismatched inputs:" \
                                                                                             "\n\texpected %(expected)s\n\tgot %(got)s", \
                                                                                             [expr],
                                                                                             lambda e: {'filename' : e.filename, \
                                                                                                        'lineno' : e.lineno, \
                                                                                                        'expected' : type_formatting_fn(expected_inputs), \
                                                                                                        'got' : type_formatting_fn(actual_inputs)}) or Nothing() \
                                                      if expected_inputs != actual_inputs else Just(actual_inputs)))
        self._module.resolution_symbols['outputs'] = expected_fn(self._module.definition.outputs) >= \
                                                     (lambda expected_outputs: expr.resolution_symbols['outputs'] >= \
                                                      (lambda actual_outputs: self._add_errors("ERROR: %(filename)s at line %(lineno)d, component " \
                                                                                               "defines mismatched outputs:" \
                                                                                               "\n\texpected %(expected)s\n\tgot %(got)s", \
                                                                                               [expr],
                                                                                               lambda e: {'filename' : e.filename, \
                                                                                                          'lineno' : e.lineno, \
                                                                                                          'expected' : type_formatting_fn(expected_outputs), \
                                                                                                          'got' : type_formatting_fn(actual_outputs)}) or Nothing() \
                                                       if expected_outputs != actual_outputs else Just(actual_outputs)))

    # (>>>) :: Arrow c => a b c -> a c d -> a b d
    @multimethod(CompositionExpression)
    def visit(self, comp_expr):
        # Check that the composing components are output/input
        # compatible
        left_outputs = comp_expr.left.resolution_symbols['outputs']
        right_inputs = comp_expr.right.resolution_symbols['inputs']
        if left_outputs != right_inputs or left_outputs is Nothing() or right_inputs is Nothing():
            self._add_errors("ERROR: %(filename)s at line %(lineno)d, attempted composition " \
                             "with incompatible components:\n\texpected %(expected)s\n\tgot %(got)s", \
                             [comp_expr],
                             lambda e: {'filename' : e.filename,
                                        'lineno' : e.lineno,
                                        'expected' : left_outputs >= type_formatting_fn,
                                        'got' : right_inputs >= type_formatting_fn})

        # Update the inputs and outputs for this composed component
        comp_expr.resolution_symbols['inputs'] = comp_expr.left.resolution_symbols['inputs']
        comp_expr.resolution_symbols['outputs'] = comp_expr.right.resolution_symbols['outputs']

    # &&& : Arrow a => a b c -> a b c' -> a b (c c')
    @multimethod(ParallelWithScalarExpression)
    def visit(self, para_scalar_expr):
        # Inputs are all the union of the top and bottom component inputs
        top_inputs = para_scalar_expr.left.resolution_symbols['inputs']
        bottom_inputs = para_scalar_expr.right.resolution_symbols['inputs']
        if top_inputs != bottom_inputs or top_inputs is Nothing() or bottom_inputs is Nothing():
            self._add_errors("ERROR: %(filename)s at line %(lineno)d, attempted use of incompatible inputs " \
                             "with components in fanout:\n\ttop %(top_inputs)s\n\tbottom %(bottom_inputs)s", \
                             [para_scalar_expr],
                             lambda e: {'filename' : e.filename,
                                        'lineno' : e.lineno,
                                        'top_inputs' : top_inputs >= type_formatting_fn,
                                        'bottom_inputs' : bottom_inputs >= type_formatting_fn})

    @multimethod(IfExpression)
    def visit(self, if_expr):
        # Store the current if expression for condition expression resolution
        self._current_if_expr = if_expr

        # Check that the then and else components' inputs and output match
        then_inputs = if_expr.then.resolution_symbols['inputs']
        then_outputs = if_expr.then.resolution_symbols['outputs']
        else_inputs = if_expr.else_.resolution_symbols['inputs']
        else_outputs = if_expr.else_.resolution_symbols['outputs']

        if then_inputs != else_inputs or then_inputs is Nothing() or else_inputs is Nothing():
            self._add_errors("ERROR: %(filename)s at line %(lineno)d, if components have mismatched " \
                             "component inputs:\n\tthen = %(then_inputs)s\n\telse = %(else_inputs)s",
                             [if_expr],
                             lambda i: {'filename' : i.filename,
                                        'lineno' : i.lineno,
                                        'then_inputs' : then_inputs >= type_formatting_fn,
                                        'else_inputs' : else_inputs >= type_formatting_fn})

        if then_outputs != else_outputs or then_outputs is Nothing() or else_outputs is Nothing():
            self._add_errors("ERROR: %(filename)s at line %(lineno)d, if components have mismatched " \
                             "component outputs:\n\tthen = %(then_outputs)s\n\telse = %(else_outputs)s",
                             [if_expr],
                             lambda i: {'filename' : i.filename,
                                        'lineno' : i.lineno,
                                        'then_outputs' : then_outputs >= type_formatting_fn,
                                        'else_outputs' : else_outputs >= type_formatting_fn})

        if_expr.resolution_symbols['inputs'] = then_inputs
        if_expr.resolution_symbols['outputs'] = then_outputs

    @multimethod(TerminalConditionalExpression)
    def visit(self, term_cond_expr):
        terminal = term_cond_expr.terminal
        if isinstance(terminal, StateIdentifier):
            if terminal not in self._module.resolution_symbols['configuration']:
                self._add_errors("ERROR: %(filename)s at line %(lineno)d, identifier %(entity)s " \
                                 "not defined in component configuration",
                                 [terminal],
                                 lambda e: {'entity' : e,
                                            'filename' : e.filename,
                                            'lineno' : e.lineno})
        elif isinstance(terminal, Identifier):
            if self._module.definition.is_leaf:
                self._add_errors("ERROR: %(filename)s at line %(lineno)d, unknown identifier %(identifier)s",
                                 [terminal] if terminal not in self._module.definition.inputs and \
                                               terminal not in term_cond_expr.scope \
                                            else [],
                                 lambda t: {'filename' : t.filename,
                                            'lineno' : t.lineno,
                                            'identifier' : t})
            else:
                self._current_if_expr.resolution_symbols['inputs'] >= (lambda s: self._add_errors("ERROR: %(filename)s at line %(lineno)d, " \
                                                                                                  "identifier %(entity)s not defined in " \
                                                                                                  "if inputs",
                                                                                                  [terminal],
                                                                                                  lambda e: {'entity' : e,
                                                                                                             'filename' : e.filename,
                                                                                                             'lineno' : e.lineno}) \
                                                                       if terminal not in s else None)
