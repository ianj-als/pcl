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
from parser.declaration import Declaration
from parser.expressions import UnaryExpression, \
     BinaryExpression, \
     CompositionExpression, \
     FirstExpression, \
     SecondExpression, \
     SplitExpression
from pypeline.core.types.just import Just
from pypeline.core.types.nothing import Nothing
from first_pass_resolver_visitor import FirstPassResolverVisitor, resolve_expression_once


type_formatting_fn = lambda c: "(%s), (%s)" % (", ".join([i.identifier for i in c[0]]), \
                                            ", ".join([i.identifier for i in c[1]])) \
                    if isinstance(c, tuple) \
                    else ", ".join([i.identifier for i in c])


@multimethodclass
class SecondPassResolverVisitor(FirstPassResolverVisitor):
    def __init__(self,
                 resolver_factory,
                 pcl_import_path = []):
        FirstPassResolverVisitor.__init__(self,
                                          resolver_factory,
                                          pcl_import_path)

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
        # Root expression, so get inputs and outpus
        # from module defined inputs and outputs clauses
        expr = self._module.definition.definition
        expected_fn = lambda e: Just((frozenset(e[0]), frozenset(e[1]))) \
                      if isinstance(e, tuple) else Just(frozenset(e))

        self._module.resolution_symbols['inputs'] = (Just(self._module.definition.inputs) >= expected_fn) >= \
                                                    (lambda expected_inputs: expr.resolution_symbols['inputs'] >= \
                                                     (lambda actual_inputs: self._errors.append("ERROR: %s at line %d, component " \
                                                                                                "expects inputs %s, but got %s" % \
                                                                                                (expr.filename, \
                                                                                                 expr.lineno, \
                                                                                                 type_formatting_fn(expected_inputs), \
                                                                                                 type_formatting_fn(actual_inputs))) or Nothing() \
                                                      if expected_inputs != actual_inputs else Just(actual_inputs)))
        self._module.resolution_symbols['outputs'] = expected_fn(self._module.definition.outputs) >= \
                                                     (lambda expected_outputs: expr.resolution_symbols['outputs'] >= \
                                                      (lambda actual_outputs: self._errors.append("ERROR: %s at line %d, component " \
                                                                                                  "expects outputs %s, but got %s" % \
                                                                                                  (expr.filename, \
                                                                                                   expr.lineno, \
                                                                                                   type_formatting_fn(expected_outputs), \
                                                                                                   type_formatting_fn(actual_outputs))) or Nothing() \
                                                       if expected_outputs != actual_outputs else Just(actual_outputs)))

    @multimethod(CompositionExpression)
    def visit(self, comp_expr):
        # Check that the composing components are output/input
        # compatible
        left_outputs = comp_expr.left.resolution_symbols['outputs']
        right_inputs = comp_expr.right.resolution_symbols['inputs']
        if left_outputs != right_inputs or left_outputs is Nothing() or right_inputs is Nothing():
            self._errors.append("ERROR: %s at line %d, attempted composition " \
                                "with incompatible components:\n\texpected %s\n\tgot %s" % \
                                (comp_expr.filename,
                                 comp_expr.lineno,
                                 left_outputs >= type_formatting_fn,
                                 right_inputs >= type_formatting_fn))

        # Update the inputs and outputs for this composed component
        comp_expr.resolution_symbols['inputs'] = comp_expr.left.resolution_symbols['inputs']
        comp_expr.resolution_symbols['outputs'] = comp_expr.right.resolution_symbols['outputs']

        if isinstance(comp_expr.left.resolution_symbols['inputs'], frozenset):
            print "Comp Left type: %s" % type(comp_expr.left)
        if isinstance(comp_expr.right.resolution_symbols['outputs'], frozenset):
            print "Comp right type: %s" % type(comp_expr.right)

    def __derive_inputs(self, expr):
        return self.__walk_expression(expr.parent, expr)

    def __walk_expression(self, node, child):
        if node is None:
            return Just(frozenset(self._module.definition.inputs))

        if isinstance(node, BinaryExpression):
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
    @resolve_expression_once
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
    @resolve_expression_once
    def visit(self, second_expr):
        # Derive the top inputs
        inputs = self.__derive_inputs(second_expr)
        top_inputs = inputs >= (lambda ins: Just(set(ins[0])) if isinstance(ins, tuple) else Just(set(ins)))

        bottom_inputs = second_expr.expression.resolution_symbols['inputs']
        bottom_outputs = second_expr.expression.resolution_symbols['outputs']

        second_expr.resolution_symbols['inputs'] = top_inputs >= (lambda tins: bottom_inputs >= \
                                                                  (lambda bins: Just((tins, bins))))
        second_expr.resolution_symbols['outputs'] = top_inputs >= (lambda touts: bottom_outputs >= \
                                                                   (lambda bouts: Just((touts, bouts))))

    @multimethod(SplitExpression)
    @resolve_expression_once
    def visit(self, split_expr):
        # Derive the inputs
        inputs = self.__derive_inputs(split_expr)
        split_expr.resolution_symbols['inputs'] = inputs
        split_expr.resolution_symbols['outputs'] = inputs >= (lambda ins: Just((ins, ins)))
