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
from executor_visitor import ExecutorVisitor
from parser.import_spec import Import
from parser.module import Module
from parser.component import Component
from parser.command import Function, Command, Return, IfCommand, LetCommand
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


class IntermediateRepresentation(object):
    class IRNode(object):
        def __init__(self, pt_object, parent = None):
            self.object = pt_object
            self.parent = parent

        def add_child(self, node):
            raise NotImplementedError

    class IRFunctionNode(IRNode):
        def __init__(self, pt_object, parent):
            IntermediateRepresentation.IRNode.__init__(self, pt_object, parent)

        def add_child(self, node):
            pass

    class IRCommandNode(IRNode):
        def __init__(self, pt_object, parent):
            IntermediateRepresentation.IRNode.__init__(self, pt_object, parent)
            self.children = list()

        def add_child(self, node):
            self.children.append(node)

    class IRIfNode(IRNode):
        def __init__(self, pt_object, parent):
            IntermediateRepresentation.IRNode.__init__(self, pt_object, parent)
            self.then_block = list()
            self.else_block = list()
            self.is_then_block = True

        def add_child(self, node):
            if self.is_then_block is True:
                self.then_block.append(node)
            elif self.is_then_block is False:
                self.else_block.append(node)

        def switch_to_else_block(self):
            self.is_then_block = False

    class IRReturnNode(IRNode):
        def __init__(self, pt_object, parent):
            IntermediateRepresentation.IRNode.__init__(self, pt_object, parent)

        def add_child(self, node):
            pass

    class IRLetNode(IRNode):
        def __init__(self, pt_object, parent):
            IntermediateRepresentation.IRNode.__init__(self, pt_object, parent)
            self.bindings = list()

        def add_child(self, node):
            if isinstance(node.object, Command):
                self.bindings.append(node)


    def __init__(self, variable_name_generator, function_name_generator):
        self.__root = list()
        self.__current_node = None
        self.__current_if = None
        self.__current_let = None
        self.__var_name_generator = variable_name_generator
        self.__func_name_generator = function_name_generator

    def __add_node(self, node, update_current_node = True):
        if node.parent is None:
            self.__root.append(node)
        else:
            self.__current_node.add_child(node)

        if update_current_node:
            self.__current_node = node

    def push_command_action(self, command):
        node = IntermediateRepresentation.IRCommandNode(command, self.__current_node)
        self.__add_node(node)

    def push_if_action(self, if_command):
        node = IntermediateRepresentation.IRIfNode(if_command, self.__current_node)
        self.__add_node(node)
        self.__current_if = node

    def mark_else_block(self):
        self.__current_if.switch_to_else_block()
        self.__current_node = self.__current_if

    def mark_endif(self):
        self.__current_node = self.__current_if.parent
        self.__current_if = None

    def push_return_action(self, return_command):
        node = IntermediateRepresentation.IRReturnNode(return_command, self.__current_node)
        self.__add_node(node, False)

    def push_let_action(self, let_command):
        node = IntermediateRepresentation.IRLetNode(let_command, self.__current_node)
        self.__add_node(node)
        self.__current_let = node

    def mark_let_end(self, let_expression_function):
        node = IntermediateRepresentation.IRFunctionNode(let_expression_function, self.__current_node)
        self.__current_node.add_child(node)
        self.__current_node = self.__current_let.parent
        self.__current_let = None

    def generate_code(self, executor_visitor, is_instrumented):
        # Generate function call lambdas
        generate_func_args = lambda args, scope: ", ".join([executor_visitor._generate_terminal(a, scope) for a in args])
        generate_func_call = lambda f, scope: "____%s(%s)" % (f.name, generate_func_args(f.arguments, scope))

        top_function_name = self.__func_name_generator.get_name(executor_visitor._module.definition.identifier)
        code = [("def %s(a, s):" % top_function_name, "+")]
        for node in self.__root:
            code.extend(self.__generate_code(node,
                                             generate_func_call,
                                             executor_visitor,
                                             is_instrumented))
        code.extend([(None, "-"),
                     ("return %s" % top_function_name, "")])

        return code

    def __generate_code(self, node, generate_function_call, executor_visitor, is_instrumented):
        code = list()

        if isinstance(node, IntermediateRepresentation.IRFunctionNode):
            # Currently, this is *only* used for let expressions
            function = node.object
            scope = function['scope']

            if is_instrumented:
                code.append(("____instr_command_begin('%s', %d, '%s', a, s)" % (function.filename, function.lineno, function),
                             ""))

            tmp_var = self.__var_name_generator.get_name(function, scope)
            code.append(("%s = %s" % (tmp_var, generate_function_call(function, scope)),
                         ""))
            code.append(("return %s" % tmp_var,
                         ""))
        elif isinstance(node, IntermediateRepresentation.IRCommandNode):
            # Command action code generation
            command = node.object
            scope = command['scope']

            code.append(("def %s(a, s):" % self.__func_name_generator.get_name(command),
                         "+"))
            if command.identifier:
                code.append(("%s = %s" % (self.__var_name_generator.get_name(command.identifier, scope), \
                                          generate_function_call(command.function, scope)),
                             ""))
            else:
                code.append((generate_function_call(command.function, scope),
                             ""))

            for child in node.children:
                more_code = self.__generate_code(child,
                                                 generate_function_call,
                                                 executor_visitor,
                                                 is_instrumented)
                code.extend(more_code)

            code.append((None, "-"))
            if is_instrumented:
                value_var = self.__var_name_generator.get_name(command, scope)
                code.append(("____instr_command_begin('%s', %d, '%s', a, s)" % (command.filename, command.lineno, command),
                             ""))
                code.append(("%s = %s(a, s)" % (value_var, self.__func_name_generator.lookup_name(command)),
                             ""))
                code.append(("return %s" % value_var,
                             ""))
            else:
                code.append(("return %s(a, s)" % self.__func_name_generator.lookup_name(command),
                             ""))
        elif isinstance(node, IntermediateRepresentation.IRIfNode):
            # If command action code generation
            if_command = node.object
            scope = if_command['scope']

            code.append(("def %s(a, s):" % self.__func_name_generator.get_name(if_command),
                         "+"))
            code.append(("if %s:" % executor_visitor._generate_condition(if_command.condition, scope),
                         "+"))

            for then_node in node.then_block:
                more_code = self.__generate_code(then_node,
                                                 generate_function_call,
                                                 executor_visitor,
                                                 is_instrumented)
                code.extend(more_code)
            code.append((None, "-"))
            
            code.append(("else:", "+"))
            for else_node in node.else_block:
                more_code = self.__generate_code(else_node,
                                                 generate_function_call,
                                                 executor_visitor,
                                                 is_instrumented)
                code.extend(more_code)

            code.extend([(None, "-"), (None, "-")])
            if if_command.identifier:
                code.append(("%s = %s(a, s)" % (self.__var_name_generator.get_name(if_command.identifier, scope), \
                                                self.__func_name_generator.lookup_name(if_command)),
                             ""))
            else:
                code.append(("%s(a, s)" % self.__func_name_generator.lookup_name(if_command),
                             ""))
        elif isinstance(node, IntermediateRepresentation.IRReturnNode):
            return_command = node.object
            scope = return_command['scope']

            if return_command.value:
                code.append(("return %s" % executor_visitor._generate_terminal(return_command.value, scope),
                             ""))
            elif len(return_command.mappings) == 0:
                code.append(("return None",
                             ""))
            else:
                code.append(("return {%s}" % ", ".join(["'%s' : %s" % \
                                                        (m.to, executor_visitor._generate_terminal(m.from_, scope)) \
                                                        for m in return_command.mappings]),
                             ""))
        elif isinstance(node, IntermediateRepresentation.IRLetNode):
            # Let command
            let_command = node.object
            scope = let_command['scope']

            code.append(("def %s(a, s):" % self.__func_name_generator.get_name(let_command),
                         "+"))

            for binding in node.bindings:
                more_code = self.__generate_code(binding,
                                                 generate_function_call,
                                                 executor_visitor,
                                                 is_instrumented)
                code.extend(more_code)

            code.append((None, "-"))
            if let_command.identifier:
                code.append(("%s = %s(a, s)" % (self.__var_name_generator.get_name(let_command.identifier, scope), \
                                                self.__func_name_generator.lookup_name(let_command)),
                             ""))
            else:
                code.append(("%s(a, s)" % self.__func_name_generator.lookup_name(let_command),
                             ""))

        return code


@multimethodclass
class DoExecutorVisitor(ExecutorVisitor):
    __INSTRUMENTATION_FUNCTION = "import sys, threading, datetime\n" \
                                 "def ____instr_command_begin(filename, lineno, cmd_type, a, s):\n" \
                                 "  print >> sys.stderr, '%s: %s: Component %s begining %s, at line %d (%s), with input %s and state %s' % (datetime.datetime.now().strftime('%x %X.%f'), threading.current_thread().name, get_name(), cmd_type, lineno, filename, a, {skey : s[skey] for skey in filter(lambda k: k != '____prev_', s.keys())})\n"

    __VAR_NAME_PREFIX = "____tmp"
    __FUNC_NAME_PREFIX = "____func"

    def __init__(self, filename_root, is_instrumented):
        var_name_generator = ScopedNameGenerator(DoExecutorVisitor.__VAR_NAME_PREFIX)
        ExecutorVisitor.__init__(self,
                                 filename_root,
                                 var_name_generator,
                                 "",
                                 is_instrumented)
        self.__func_name_generator = ScopedNameGenerator(DoExecutorVisitor.__FUNC_NAME_PREFIX)
        self.__ir = IntermediateRepresentation(var_name_generator, self.__func_name_generator)
        if self._is_instrumented:
            self._write_line(DoExecutorVisitor.__INSTRUMENTATION_FUNCTION)
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

    @multimethod(Module)
    def visit(self, module):
        self._module = module

    @multimethod(Import)
    def visit(self, an_import):
        self._write_line("import %s as ____%s" % (an_import.module_name, an_import.alias))

    @multimethod(Component)
    def visit(self, component):
        type_formatting_fn = lambda c: str([str(i) for i in c])

        # The get name function. This is not strictly needed but is included for completeness
        self._write_line()
        self._write_line()
        self._write_function("get_name",
                             [("return '%s'" % component.identifier,
                               "")])

        # The get inputs function
        self._write_function("get_inputs",
                             "return %s" %  type_formatting_fn(component.inputs))

        # The get outputs function
        self._write_function("get_outputs",
                             "return %s" % type_formatting_fn(component.outputs))

        # The get configuration function
        self._write_function("get_configuration",
                             "return %s" % \
                             [str(i) for i in self._module.resolution_symbols['configuration'].keys()])

        # The configure function
        self._write_function("configure",
                             "return {%s}" % ", ".join(["'%s' : args['%s']" % (i, i) \
                                                        for i in self._module.resolution_symbols['configuration']]),
                             ["args"])

    @multimethod(object)
    def visit(self, nowt):
        func_defs = self.__ir.generate_code(self, self._is_instrumented)

        # Write initialise function
        self._write_function("initialise", func_defs, ["config"])
        self._object_file.close()

    @multimethod(Function)
    def visit(self, function):
        pass

    @multimethod(Command)
    def visit(self, command):
        self.__ir.push_command_action(command)

    @multimethod(Return)
    def visit(self, ret):
        self.__ir.push_return_action(ret)

    @multimethod(IfCommand)
    def visit(self, if_command):
        self.__ir.push_if_action(if_command)

    @multimethod(IfCommand.ThenBlock)
    def visit(self, then_block):
        pass

    @multimethod(IfCommand.ElseBlock)
    def visit(self, else_block):
        self.__ir.mark_else_block()

    @multimethod(IfCommand.EndIf)
    def visit(self, end_if):
        self.__ir.mark_endif()

    @multimethod(LetCommand)
    def visit(self, let_command):
        self.__ir.push_let_action(let_command)

    @multimethod(LetCommand.LetBindings)
    def visit(self, let_bindings):
        pass

    @multimethod(LetCommand.LetEnd)
    def visit(self, let_end):
        self.__ir.mark_let_end(let_end.let_command.expression)

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
