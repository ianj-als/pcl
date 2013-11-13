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

from multimethod import multimethod, multimethodclass
from parser.import_spec import Import
from parser.component import Component
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
from parser.declaration import Declaration
from parser.expressions import Literal, \
     Identifier, \
     StateIdentifier, \
     Expression, \
     UnaryExpression, \
     CompositionExpression, \
     ParallelWithTupleExpression, \
     ParallelWithScalarExpression, \
     FirstExpression, \
     SecondExpression, \
     SplitExpression, \
     MergeExpression, \
     WireExpression, \
     WireTupleExpression, \
     IfExpression, \
     IdentifierExpression
from parser.mappings import Mapping, \
     TopMapping, \
     BottomMapping, \
     LiteralMapping
from parser.module import Module
from executor_visitor import ExecutorVisitor
from scoped_name_generator import ScopedNameGenerator


@multimethodclass
class PCLExecutorVisitor(ExecutorVisitor):
    __IMPORTS = "from pypeline.helpers.parallel_helpers import cons_function_component, cons_wire, cons_split_wire, cons_unsplit_wire, cons_if_component\n" \
                "from pypeline.core.arrows.kleisli_arrow import KleisliArrow\n" \
                "from pypeline.core.arrows.kleisli_arrow_choice import KleisliArrowChoice\n" \
                "from pypeline.core.types.either import Left, Right\n" \
                "from pypeline.core.types.state import return_\n"
    __INSTRUMENTATION_FUNCTIONS = "import sys, threading, datetime\n" \
                                  "def ____instr_component(component_decl_id, component_id, event, a, s):\n" \
                                  "  print >> sys.stderr, '%s: %s: Component %s is %s %s (id = %s) with input %s and state %s' % (datetime.datetime.now().strftime('%x %X.%f'), threading.current_thread().name, get_name(), event, component_decl_id, component_id, a, {skey : s[skey] for skey in filter(lambda k: k != '____prev_', s.keys())})\n" \
                                  "  return a\n"\
                                  "def ____instr_component_construction(component_decl_id, component_id, component_config, invoked_component, decl_line_no):\n" \
                                  "  print >> sys.stderr, '%s: %s: Component %s is constructing %s (id = %s) with configuration %s (%s instance declared at line %d)' % (datetime.datetime.now().strftime('%x %X.%f'), threading.current_thread().name, get_name(), component_decl_id, component_id, component_config, invoked_component, decl_line_no)\n"

    __COMP_NAME_PREFIX = "____comp"

    def __init__(self, filename_root, is_instrumented = False):
        self.__comp_name_generator = ScopedNameGenerator(PCLExecutorVisitor.__COMP_NAME_PREFIX)
        ExecutorVisitor.__init__(self,
                                 filename_root,
                                 self.__comp_name_generator,
                                 PCLExecutorVisitor.__IMPORTS,
                                 is_instrumented)
        if self._is_instrumented:
            self._write_line(PCLExecutorVisitor.__INSTRUMENTATION_FUNCTIONS)
        self._write_line()

    def _generate_terminal(self, terminal, scope = None):
        if isinstance(terminal, StateIdentifier):
            return "s['%s']" % terminal.identifier
        elif isinstance(terminal, Identifier):
            return "a['%s']" % terminal
        elif isinstance(terminal, Literal):
            return str(terminal)
        else:
            raise ValueError("Unexpected terminal in conditional: filename = %s, line no = %d" % \
                             (terminal.filename, terminal.lineno))

    @multimethod(Module)
    def visit(self, module):
        self._module = module

    @multimethod(Import)
    def visit(self, an_import):
        self._write_line("import %s as ____%s" % (an_import.module_name, an_import.alias))

    @multimethod(Component)
    def visit(self, component):
        type_formatting_fn = lambda m: m >= (lambda c: str(([str(i) for i in c[0]], \
                                                            [str(i) for i in c[1]])) \
                                             if isinstance(c, tuple) else str([str(i) for i in c]))

        # The get name function. This is not strictly needed but is included for completeness
        self._write_line()
        self._write_line()
        self._write_function("get_name",
                             [("return '%s'" % \
                               component.identifier,
                               "")])

        # The get inputs function
        self._write_function("get_inputs",
                             "return %s" % \
                             type_formatting_fn(self._module.resolution_symbols['inputs']))

        # The get outputs function
        self._write_function("get_outputs",
                             "return %s" % \
                             type_formatting_fn(self._module.resolution_symbols['outputs']))

        # The get configuration function
        self._write_function("get_configuration",
                             "return %s" % \
                             [str(i) for i in self._module.resolution_symbols['configuration'].keys()])

        # The configure function
        self._write_function("configure",
                             "return {%s}" % ", ".join(["'%s' : args['%s']" % (i, i) \
                                                        for i in self._module.resolution_symbols['configuration']]),
                             ["args"])

        # Component configuration
        component_configuration_exprs = ["%s_configuration = %s" % \
                                         (decl.identifier,
                                          "{%s}" % (", ".join(["'%s' : %s" % \
                                                               (cm.to, \
                                                                "config['%s']" % cm.from_ \
                                                                if isinstance(cm.from_, Identifier) \
                                                                else cm.from_.value.__repr__() \
                                                                if isinstance(cm.from_.value, str) \
                                                                else m.literal) \
                                                                for cm in decl.configuration_mappings]))) \
                                         for decl in self._module.resolution_symbols['components']]
        # The initialise function
        component_initialisations = ["%(id)s = ____%(comp_alias)s.initialise(____%(comp_alias)s.configure(%(id)s_configuration))" % \
                                     {'id' : decl.identifier,
                                      'comp_alias' : decl.component_alias} \
                                     for decl in self._module.resolution_symbols['components']]
        # Guard against a module returning a non-Kleisli arrow type from initialise
        component_decl_guards = ["%(id)s = %(id)s " \
                                 "if isinstance(%(id)s, KleisliArrow) " \
                                 "else cons_function_component(%(id)s)" % \
                                 {'id' : decl.identifier} \
                                 for decl in self._module.resolution_symbols['components']]
        # Wrap this component with any state conversion components
        state_wrappers = ["%(id)s = ((cons_function_component(lambda a, s: a, state_mutator = lambda s: {%(state)s, '____prev_' : s})) >> %(id)s) >> cons_function_component(lambda a, s: a, state_mutator = lambda s: s['____prev_'])" % \
                          {'id' : decl.identifier,
                           'state' : "%s" % (", ".join(["'%s' : %s" % \
                                                        (cm.to, \
                                                        "s['%s']" % cm.from_ \
                                                        if isinstance(cm.from_, Identifier) \
                                                        else cm.from_.value.__repr__() \
                                                        if isinstance(cm.from_.value, str) \
                                                        else m.literal) \
                                                        for cm in decl.configuration_mappings]))} if decl.configuration_mappings else ""
                          for decl in self._module.resolution_symbols['components']]
        # Do we generate instrumented code?
        if self._is_instrumented:
            # Constructed component identifier
            component_id_exprs = ["%(id)s_id = id(%(id)s)" % \
                                  {'id' : decl.identifier} \
                                  for decl in self._module.resolution_symbols['components']]
            # Instrument component construction
            component_init_instrumentation_exprs = ["____instr_component_construction('%(id)s', %(id)s_id, %(id)s_configuration, ____%(comp_alias)s.get_name(), %(decl_line_no)d)" % \
                                                    {'id' : decl.identifier,
                                                     'comp_alias' : decl.component_alias,
                                                     'decl_line_no' : decl.lineno} \
                                                    for decl in self._module.resolution_symbols['components']]
            # Wrap with instrumentation
            component_instrumentation_exprs = ["%(id)s = ((cons_function_component(lambda a, s: ____instr_component('%(id)s', %(id)s_id, 'starting', a, s)) >> " \
                                               "%(id)s) >> " \
                                               "cons_function_component(lambda a, s: ____instr_component('%(id)s', %(id)s_id, 'finishing', a, s)))" % \
                                               {'id' : decl.identifier,
                                                'comp_alias' : decl.component_alias,
                                                'decl_line_no' : decl.lineno} \
                                               for decl in self._module.resolution_symbols['components']]
            # Generated code zipper
            decl_zipper = zip(component_configuration_exprs,
                              component_initialisations,
                              component_decl_guards,
                              component_id_exprs,
                              component_init_instrumentation_exprs,
                              component_instrumentation_exprs,
                              state_wrappers)
        else:
            decl_zipper = zip(component_configuration_exprs,
                              component_initialisations,
                              component_decl_guards,
                              state_wrappers)
        initialise_fn = [t for triple in decl_zipper for t in triple]
        # Store variables in variable table
        for decl in self._module.resolution_symbols['components']:
            self._variable_generator.register_name(IdentifierExpression(None,
                                                                        0,
                                                                        decl.identifier,
                                                                        Expression(None, 0)),
                                                   str(decl.identifier))
        self._write_function("initialise",
                             [(smt, "") for smt in initialise_fn],
                             ["config"])

    @multimethod(Declaration)
    def visit(self, decl):
        pass

    @multimethod(object)
    def visit(self, nowt):
        for expr in self._variable_generator.iter_names():
            if expr.parent == None:
                self._write_line()
                self._write_line("return %s" % self._variable_generator.lookup_name(expr))
                break        
        self._object_file.close()

    @multimethod(UnaryExpression)
    def visit(self, unary_expr):
        var_name = self._variable_generator.remove_name(unary_expr.expression)
        self._variable_generator.register_name(unary_expr, var_name)

    @multimethod(CompositionExpression)
    def visit(self, comp_expr):
        self._write_line("%s = %s >> %s" % \
                         (self._variable_generator.get_name(comp_expr),
                          self._variable_generator.lookup_name(comp_expr.left),
                          self._variable_generator.lookup_name(comp_expr.right)))

    @multimethod(ParallelWithTupleExpression)
    def visit(self, para_tuple_expr):
        self._write_line("%s = %s ** %s" % \
                         (self._variable_generator.get_name(para_tuple_expr),
                          self._variable_generator.lookup_name(para_tuple_expr.left),
                          self._variable_generator.lookup_name(para_tuple_expr.right)))
        
    @multimethod(ParallelWithScalarExpression)
    def visit(self, para_scalar_expr):
        self._write_line("%s = %s & %s" % \
                         (self._variable_generator.get_name(para_scalar_expr),
                          self._variable_generator.lookup_name(para_scalar_expr.left),
                          self._variable_generator.lookup_name(para_scalar_expr.right)))

    @multimethod(FirstExpression)
    def visit(self, first_expr):
        self._write_line("%s = %s.first()" % \
                         (self._variable_generator.get_name(first_expr),
                          self._variable_generator.lookup_name(first_expr.expression)))

    @multimethod(SecondExpression)
    def visit(self, second_expr):
        self._write_line("%s = %s.second()" % \
                         (self._variable_generator.get_name(second_expr),
                          self._variable_generator.lookup_name(second_expr.expression)))

    @multimethod(SplitExpression)
    def visit(self, split_expr):
        self._write_line("%s = cons_split_wire()" % \
                         self._variable_generator.get_name(split_expr))

    @multimethod(MergeExpression)
    def visit(self, merge_expr):
        top_mappings = ["'%s' : t['%s']" % (m.to, m.from_) \
                        for m in merge_expr.top_mapping \
                        if str(m.to) != '_']
        bottom_mappings = ["'%s' : b['%s']" % (m.to, m.from_) \
                           for m in merge_expr.bottom_mapping \
                           if str(m.to) != '_']
        literal_mappings = ["'%s' : %s" % \
                            (m.to, m.literal) \
                            for m in merge_expr.literal_mapping]
        mapping = ", ".join(top_mappings + bottom_mappings + literal_mappings)
        self._write_line("%s = cons_unsplit_wire(lambda t, b: {%s})" % \
                         (self._variable_generator.get_name(merge_expr),
                          mapping))

    @staticmethod
    def __build_wire_expr(mapping):
        dict_repr = ["'%s' : %s" % (m.to,
                                    "a['%s']" % (m.from_) if isinstance(m, Mapping) else m.literal)
                     for m in mapping \
                     if str(m.to) != '_']
        return "cons_wire(lambda a, s: {%s})" % (", ".join(dict_repr))
    
    @multimethod(WireExpression)
    def visit(self, wire_expr):
        self._write_line("%s = %s" % (self._variable_generator.get_name(wire_expr),
                                      PCLExecutorVisitor.__build_wire_expr(wire_expr.mapping)))

    @multimethod(WireTupleExpression)
    def visit(self, wire_tuple_expr):
        self._write_line("%s = %s ** %s" % \
                         (self._variable_generator.get_name(wire_tuple_expr),
                          PCLExecutorVisitor.__build_wire_expr(wire_tuple_expr.top_mapping),
                          PCLExecutorVisitor.__build_wire_expr(wire_tuple_expr.bottom_mapping)))

    @multimethod(IfExpression)
    def visit(self, if_expr):
        self._write_line("%s = cons_if_component(lambda a, s: %s, %s, %s)" % \
                         (self._variable_generator.get_name(if_expr),
                          self._generate_condition(if_expr.condition),
                          self._variable_generator.lookup_name(if_expr.then),
                          self._variable_generator.lookup_name(if_expr.else_)))

    @multimethod(AndConditionalExpression)
    def visit(self, and_cond_expr):
        pass

    @multimethod(OrConditionalExpression)
    def visit(self, or_cond_expr):
        pass

    @multimethod(XorConditionalExpression)
    def visit(self, xor_cond_expr):
        pass

    @multimethod(EqualsConditionalExpression)
    def visit(self, eq_cond_expr):
        pass

    @multimethod(NotEqualsConditionalExpression)
    def visit(self, ne_cond_expr):
        pass

    @multimethod(GreaterThanConditionalExpression)
    def visit(self, gt_cond_expr):
        pass

    @multimethod(LessThanConditionalExpression)
    def visit(self, lt_cond_expr):
        pass

    @multimethod(GreaterThanEqualToConditionalExpression)
    def visit(self, gte_cond_expr):
        pass

    @multimethod(LessThanEqualToConditionalExpression)
    def visit(self, lte_cond_expr):
        pass

    @multimethod(UnaryConditionalExpression)
    def visit(self, unary_cond_expr):
        pass

    @multimethod(TerminalConditionalExpression)
    def visit(self, term_cond_expr):
        pass

    @multimethod(Mapping)
    def visit(self, mapping):
        pass

    @multimethod(TopMapping)
    def visit(self, mapping):
        pass

    @multimethod(BottomMapping)
    def visit(self, mapping):
        pass

    @multimethod(LiteralMapping)
    def visit(self, mapping):
        pass

    @multimethod(IdentifierExpression)
    def visit(self, iden_expr):
        pass
