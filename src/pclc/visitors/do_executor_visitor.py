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
from parser.command import Function, Command, Return, IfCommand
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


class IntermediateRepresentation(object):
    class IRNode(object):
        def __init__(self, pt_object, parent = None):
            self.object = pt_object
            self.parent = parent

        def add_child(self, node):
            raise NotImplementedError

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

    __TEMP_FUNC_FMT = "____func_%d"

    def __init__(self):
        self.__root = list()
        self.__current_node = None
        self.__current_if = None
        self.__func_table = dict()
        self.__func_no = 0

    def push_command_action(self, command):
        node = IntermediateRepresentation.IRCommandNode(command, self.__current_node)
        if node.parent is None:
            self.__root.append(node)
        else:
            self.__current_node.add_child(node)
        self.__current_node = node

    def push_then_block(self, then_block):
        node = IntermediateRepresentation.IRIfNode(then_block.if_command, self.__current_node)
        if node.parent is None:
            self.__root.append(node)
        else:
            self.__current_node.add_child(node)
        self.__current_node = node
        self.__current_if = node

    def mark_else_block(self):
        self.__current_if.switch_to_else_block()
        self.__current_node = self.__current_if

    def mark_endif(self):
        self.__current_node = self.__current_if.parent
        self.__current_if = None

    def push_return_action(self, return_command):
        node = IntermediateRepresentation.IRReturnNode(return_command, self.__current_node)
        if node.parent is None:
            self.__root.append(node)
        else:
            self.__current_node.add_child(node)

    def generate_code(self, executor_visitor, assignment_symbol_table):
        # Generate function call lambdas
        generate_func_args = lambda args: ", ".join(["s['%s']" % a.identifier if isinstance(a, StateIdentifier) \
                                                     else executor_visitor._lookup_var(a) if isinstance(a, Identifier) and \
                                                                                             a in assignment_symbol_table \
                                                     else "a['%s']" % a if isinstance(a, Identifier) \
                                                     else str(a) for a in args])
        generate_func_call = lambda f: "____%s(%s)" % (f.name, generate_func_args(f.arguments))

        code = list()
        for node in self.__root:
            code.extend(self.__generate_code(node, generate_func_call, executor_visitor))

        top_function_name = self.__lookup_function_name(self.__root[0].object)

        return (code, top_function_name)

    def __generate_code(self, node, generate_function_call, executor_visitor):
        code = list()

        if isinstance(node, IntermediateRepresentation.IRCommandNode):
            # Command action code generation
            command = node.object
            code.append(("def %s(a, s):" % self.__get_function_name(command), "+"))
            if command.identifier:
                code.append(("%s = %s" % (executor_visitor._get_temp_var(command.identifier), \
                                          generate_function_call(command.function)), ""))
            else:
                code.append((generate_function_call(command.function), ""))

            for child in node.children:
                more_code = self.__generate_code(child, generate_function_call, executor_visitor)
                code.extend(more_code)

            code.append((None, "-"))
            code.append(("%s(a, s)" % self.__lookup_function_name(command), ""))
        elif isinstance(node, IntermediateRepresentation.IRIfNode):
            # If command action code generation
            if_command = node.object
            code.append(("def %s(a, s):" % self.__get_function_name(if_command), "+"))
            code.append(("if %s:" % executor_visitor._generate_condition(if_command.condition), "+"))

            for then_node in node.then_block:
                more_code = self.__generate_code(then_node, generate_function_call, executor_visitor)
                code.extend(more_code)
            code.append((None, "-"))
            
            code.append(("else:", "+"))
            for else_node in node.else_block:
                more_code = self.__generate_code(else_node, generate_function_call, executor_visitor)
                code.extend(more_code)
            

            code.append((None, "-"))
            code.append(("%s(a, s)" % self.__lookup_function_name(if_command), ""))
        elif isinstance(node, IntermediateRepresentation.IRReturnNode):
            return_command = node.object
            if len(return_command.mappings) == 0:
                code.append(("return None", ""))
                            
        return code

    def __get_function_name(self, function):
        func_name = IntermediateRepresentation.__TEMP_FUNC_FMT % self.__func_no
        self.__func_table[function] = func_name
        self.__func_no += 1
        return func_name

    def __lookup_function_name(self, function):
        return self.__func_table[function]



##            # Generate the whole code
##            def generate_code(cmd_iterator, accum):
##                cmd = None
##                try:
##                    cmd = cmd_iterator.next()
##                except StopIteration:
##                    return None

##                print cmd, type(cmd)

##                if isinstance(cmd, Command):
##                    accum.append()
##                    accum.append()
##                elif isinstance(cmd, IfCommand):
##                    accum.append(())
##                    accum.append((None, "+"))
##                    #accum.extend(generate_code(cmd.then_commands.__iter__(), accum))
##                    accum.append((None, "-"))
##                    accum.append(("else:", "+"))
##                    #accum.extend(generate_code(cmd.else_commands.__iter__(), accum))

##                more_code = generate_code(cmd_iterator, accum)
##                if more_code:
##                    accum.extend(more_code)

##                if isinstance(cmd, Command):
##                    accum.append()
##                accum.append()

##                # Generate some code
##                iterator = self.__commands.__iter__()
##                func_defs = list()
##                generate_code(iterator, func_defs)


@multimethodclass
class DoExecutorVisitor(ExecutorVisitor):
    def __init__(self, filename_root, is_instrumented):
        ExecutorVisitor.__init__(self, filename_root, "", is_instrumented)
        self.__ir = IntermediateRepresentation()
        self.__func_no = 0
        self.__func_table = dict()

    @multimethod(Module)
    def visit(self, module):
        self._module = module

    @multimethod(Import)
    def visit(self, an_import):
        self._write_line("import %s as ____%s" % \
                         (an_import.module_name, \
                          an_import.alias))

    @multimethod(Component)
    def visit(self, component):
        type_formatting_fn = lambda c: str([str(i) for i in c])

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
                             type_formatting_fn(component.inputs))

        # The get outputs function
        self._write_function("get_outputs",
                             "return %s" % \
                             type_formatting_fn(component.outputs))

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
        func_defs, top_function_name = self.__ir.generate_code(self, self._module.resolution_symbols['assignment_table'])

        # Write initialise function
        self._write_function("initialise", func_defs, ["config"])
        self._reset_indent_level()
        self._write_lines([("", "+")])
        self._write_line("return %s" % top_function_name)
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
        self.__ir.mark_endif()

    @multimethod(IfCommand.ThenBlock)
    def visit(self, then_block):
        self.__ir.push_then_block(then_block)

    @multimethod(IfCommand.ElseBlock)
    def visit(self, else_block):
        self.__ir.mark_else_block()

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
