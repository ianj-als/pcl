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
from parser.declaration import Declaration
from parser.expressions import Literal, \
     Identifier, \
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
     IdentifierExpression, \
     LiteralExpression
from parser.mappings import Mapping, \
     TopMapping, \
     BottomMapping, \
     LiteralMapping
from parser.module import Module


@multimethodclass
class ExecutorVisitor(object):
    __INDENTATION = "  "
    __HEADER = "#\n" \
               "# DO NOT EDIT THIS FILE!\n" \
               "#\n" \
               "# This file was automatically generated by PCLc on\n" \
               "# %(datetime)s.\n" \
               "#\n" \
               "from pypeline.helpers.parallel_helpers import cons_function_component, cons_wire, cons_dictionary_wire, cons_split_wire, cons_unsplit_wire\n" \
               "from pypeline.core.arrows.kleisli_arrow import KleisliArrow\n"
    __TEMP_VAR = "____tmp_%d"

    def __init__(self, filename_root):
        # Check that the __init__.py file exists in the
        # working directory
        if os.path.isfile('__init__.py') is False:
            open('__init__.py', 'w').close()
        self._object_file = open('%s.py' % filename_root, 'w')
        self._indent_level = 0
        self._tmp_var_no = 0
        self._var_table = dict()
        header_args = {'datetime' : \
                       datetime.datetime.now().strftime("%A %d %B %Y at %H:%M:%S")}
        self.__write_line(ExecutorVisitor.__HEADER % header_args)

    @multimethod(Module)
    def visit(self, module):
        self._module = module

    def __write_line(self, stuff = ""):
        with_indents = "%s%s\n" % (ExecutorVisitor.__INDENTATION * self._indent_level, \
                                   stuff)
        self._object_file.write(with_indents)

    def __write_lines(self, lines):
        if isinstance(lines, list) or \
           isinstance(lines, tuple):
            for line, indent_step in lines:
                self.__write_line(line)
                if indent_step == "+":
                    self.__incr_indent_level()
                elif indent_step == "-":
                    self.__decr_indent_level()
        else:
            self.__write_line(lines)

    def __incr_indent_level(self):
        self._indent_level += 1

    def __decr_indent_level(self):
        self._indent_level -= 1
        if self._indent_level < 1:
            self.__reset_indent_level(self)

    def __reset_indent_level(self):
        self._indent_level = 0

    def __write_function(self, fn_name, body_lines, arguments = []):
        self.__reset_indent_level()
        self.__write_line("def %s(%s):" % (fn_name, ", ".join(arguments)))
        self.__incr_indent_level()
        self.__write_lines(body_lines)
        self.__write_line()

    def __get_temp_var(self, expr):
        temp_var = ExecutorVisitor.__TEMP_VAR % self._tmp_var_no
        self._var_table[expr] = temp_var
        self._tmp_var_no += 1
        return temp_var

    def __lookup_var(self, expr):
        return self._var_table[expr]

    @multimethod(Import)
    def visit(self, an_import):
        self.__write_line("import %s as ____%s" % \
                          (an_import.module_name, \
                           an_import.alias))

    @multimethod(Component)
    def visit(self, component):
        type_formatting_fn = lambda m: m >= (lambda c: str(([str(i) for i in c[0]], \
                                                            [str(i) for i in c[1]])) \
                                             if isinstance(c, tuple) else str([str(i) for i in c]))

        # The get name function. This is not strictly needed but is included for completeness
        self.__write_line()
        self.__write_line()
        self.__write_function("get_name",
                              [("return '%s'" % \
                                component.identifier,
                                "")])

        # The get inputs function
        self.__write_function("get_inputs",
                              "return %s" % \
                              type_formatting_fn(self._module.resolution_symbols['inputs']))

        # The get outputs function
        self.__write_function("get_outputs",
                              "return %s" % \
                              type_formatting_fn(self._module.resolution_symbols['outputs']))

        # The get configuration function
        self.__write_function("get_configuration",
                              "return %s" % \
                              [str(i) for i in self._module.resolution_symbols['configuration'].keys()])

        # The configure function
        self.__write_function("configure",
                              "return {%s}" % ", ".join(["'%s' : args['%s']" % (i, i) \
                                                         for i in self._module.resolution_symbols['configuration']]),
                              ["args"])

        # The initialise function
        component_initialisations = ["%s = ____%s.initialise(____%s.configure(%s))" % \
                                     (decl.identifier,
                                      decl.component_alias,
                                      decl.component_alias,
                                      "{%s}" % (", ".join(["'%s' : %s" % \
                                                           (cm.to, \
                                                            "config['%s']" % cm.from_ \
                                                            if isinstance(cm.from_, Identifier) \
                                                            else cm.from_.value.__repr__() \
                                                            if isinstance(cm.from_.value, str) \
                                                            else m.literal) \
                                                           for cm in decl.configuration_mappings]))) \
                                     for decl in self._module.resolution_symbols['components']]
        component_decl_guards = ["%(id)s = %(id)s " \
                                 "if isinstance(%(id)s, KleisliArrow) " \
                                 "else cons_function_component(%(id)s)" % \
                                 {'id' : decl.identifier} \
                                 for decl in self._module.resolution_symbols['components']]
        initialise_fn = [t for pair in zip(component_initialisations, component_decl_guards) for t in pair]
        # Store variables in variable table
        for decl in self._module.resolution_symbols['components']:
            self._var_table[IdentifierExpression(None,
                                                 0,
                                                 decl.identifier,
                                                 Expression(None, 0))] = str(decl.identifier)
        self.__write_function("initialise",
                              [(smt, "") for smt in initialise_fn],
                              ["config"])

    @multimethod(Declaration)
    def visit(self, decl):
        pass

    @multimethod(object)
    def visit(self, nowt):
        for expr in self._var_table.keys():
            if expr.parent == None:
                self.__write_line()
                self.__write_line("return %s" % self.__lookup_var(expr))
                break        
        self._object_file.close()

    @multimethod(UnaryExpression)
    def visit(self, unary_expr):
        var_name = self._var_table.pop(unary_expr.expression)
        self._var_table[unary_expr] = var_name

    @multimethod(CompositionExpression)
    def visit(self, comp_expr):
        self.__write_line("%s = %s >> %s" % \
                          (self.__get_temp_var(comp_expr),
                           self.__lookup_var(comp_expr.left),
                           self.__lookup_var(comp_expr.right)))

    @multimethod(ParallelWithTupleExpression)
    def visit(self, para_tuple_expr):
        self.__write_line("%s = %s.first() >> %s.second()" % \
                          (self.__get_temp_var(para_tuple_expr),
                           self.__lookup_var(para_tuple_expr.left),
                           self.__lookup_var(para_tuple_expr.right)))

    @multimethod(ParallelWithScalarExpression)
    def visit(self, para_scalar_expr):
        self.__write_line("%s = cons_split_wire() >> (%s.first() >> %s.second())" % \
                          (self.__get_temp_var(para_scalar_expr),
                           self.__lookup_var(para_scalar_expr.left),
                           self.__lookup_var(para_scalar_expr.right)))

    @multimethod(FirstExpression)
    def visit(self, first_expr):
        self.__write_line("%s = %s.first()" % \
                          (self.__get_temp_var(first_expr),
                           self.__lookup_var(first_expr.expression)))

    @multimethod(SecondExpression)
    def visit(self, second_expr):
        self.__write_line("%s = %s.second()" % \
                          (self.__get_temp_var(second_expr),
                           self.__lookup_var(second_expr.expression)))

    @multimethod(SplitExpression)
    def visit(self, split_expr):
        self.__write_line("%s = cons_split_wire()" % \
                          self.__get_temp_var(split_expr))

    @multimethod(MergeExpression)
    def visit(self, merge_expr):
        top_mappings = ["'%s' : t['%s']" % (m.to, m.from_) \
                        for m in merge_expr.top_mapping \
                        if str(m.to) != '_']
        bottom_mappings = ["'%s' : b['%s']" % (m.to, m.from_) \
                           for m in merge_expr.bottom_mapping \
                           if str(m.to) != '_']
        literal_mappings = ["'%s' : %s" % \
                            (m.to, \
                             m.literal.value.__repr__() if isinstance(m.literal.value, str) else m.literal) \
                            for m in merge_expr.literal_mapping]
        mapping = ", ".join(top_mappings + bottom_mappings + literal_mappings)
        self.__write_line("%s = cons_unsplit_wire(lambda t, b: {%s})" % \
                          (self.__get_temp_var(merge_expr),
                           mapping))

    @multimethod(WireExpression)
    def visit(self, wire_expr):
        self.__write_line("%s = cons_dictionary_wire({%s})" % \
                          (self.__get_temp_var(wire_expr),
                           ", ".join(["'%s' : '%s'" % \
                                      (m.from_, m.to) \
                                      for m in wire_expr.mapping \
                                      if str(m.to) != '_'])))

    @multimethod(WireTupleExpression)
    def visit(self, wire_tuple_expr):
        wire_fn = "lambda t, s: ({%s}, {%s})" % \
                  (", ".join(["'%s' : t[0]['%s']" % \
                              (m.to, m.from_) \
                              for m in wire_tuple_expr.top_mapping \
                              if str(m.to) != '_']), \
                   ", ".join(["'%s' : t[1]['%s']" % \
                              (m.to, m.from_) \
                              for m in wire_tuple_expr.bottom_mapping \
                              if str(m.to) != '_']))
        self.__write_line("%s = cons_wire(%s)" % \
                          (self.__get_temp_var(wire_tuple_expr),
                           wire_fn))

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

    @multimethod(LiteralExpression)
    def visit(self, literal_expr):
        pass
