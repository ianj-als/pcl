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


@multimethodclass
class DoExecutorVisitor(ExecutorVisitor):
    def __init__(self, filename_root, is_instrumented):
        ExecutorVisitor.__init__(self, filename_root, "", is_instrumented)

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
