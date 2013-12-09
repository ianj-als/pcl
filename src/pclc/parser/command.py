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


class ResolutionSymbols(object):
    def __init__(self):
        self.symbols = dict()

    def __setitem__(self, symbol, value):
        self.symbols[symbol] = value

    def __getitem__(self, symbol):
        return self.symbols[symbol]

class Assignment(Entity, ResolutionSymbols):
    def __init__(self,
                 filename,
                 lineno,
                 identifier):
        Entity.__init__(self, filename, lineno)
        ResolutionSymbols.__init__(self)
        self.identifier = identifier

    def accept(self, visitor):
        visitor.visit(self)

    def __str__(self):
        return "%s <-" % str(self.identifier)

    def __repr__(self):
        return "<Assignment: identifier %s\n\tentity = %s>" % \
               (repr(self.identifier),
                super(Assignment, self).__repr__())

class Function(Entity, ResolutionSymbols):
    def __init__(self,
                 filename,
                 lineno,
                 identifier,
                 arguments):
        Entity.__init__(self, filename, lineno)
        ResolutionSymbols.__init__(self)
        self.package_alias, self.name = str(identifier).split(".")
        self.arguments = arguments

    def get_qualified_name(self):
        return ".".join([self.package_alias, self.name])

    def accept(self, visitor):
        visitor.visit(self)

    def __str__(self):
        return "%s(%s)" % \
               (self.get_qualified_name(),
                ", ".join(map(lambda arg: str(arg), self.arguments)))

    def __repr__(self):
        return "<Function:\n\tname = %s\n\tpackage alias = %s\n\t" \
               "arguments = %s\n\tentity = %s>" % \
               (repr(self.name),
                repr(self.package_alias),
                ", ".join(map(lambda arg: arg.__repr__(), self.arguments)),
                super(Function, self).__repr__())

class Command(Entity, ResolutionSymbols):
    def __init__(self,
                 filename,
                 lineno,
                 assignment,
                 function):
        Entity.__init__(self, filename, lineno)
        ResolutionSymbols.__init__(self)
        self.assignment = assignment
        self.function = function

    def accept(self, visitor):
        visitor.visit(self)
        if self.assignment:
            self.assignment.accept(visitor)

    def __str__(self):
        l = [str(self.function)]
        if self.assignment:
            l.insert(0, str(self.assignment))
        return " ".join(l)
                    
    def __repr__(self):
        return "<Command:\n\tassignment = %s\n\tfunction = %s\n\t" \
               "entity = %s>" % \
               (repr(self.assignment),
                repr(self.function),
                super(Command, self).__repr__())

class Return(Entity, ResolutionSymbols):
    def __init__(self,
                 filename,
                 lineno,
                 value = None,
                 mappings = list()):
        Entity.__init__(self, filename, lineno)
        ResolutionSymbols.__init__(self)
        self.value = value
        self.mappings = mappings

    def accept(self, visitor):
        visitor.visit(self)

    def __str__(self):
        def value_str():
            if self.value is not None:
                return str(self.value)
            elif not self.mappings:
                return "()"
            else:
                return ", ".join(map(lambda m: str(m), self.mappings))
        return "return %s" % value_str()

    def __repr__(self):
        return "<Return:\n\tvalue = %s\n\tmappings = %s\n\tentity = %s>" % \
               (repr(self.value),
                "()" if not self.mappings \
                     else ", ".join(map(lambda m: repr(m), self.mappings)), \
                super(Return, self).__repr__())

class Block(Entity):
    def __init__(self, filename, lineno, commands, parent_command):
        Entity.__init__(self, filename, lineno)
        self.commands = commands
        self.parent_command = parent_command

    def __getitem__(self, idx):
        return self.commands[idx]

    def __iter__(self):
        return self.commands.__iter__()

    def append(self, cmd):
        self.commands.append(cmd)

    def accept(self, visitor):
        visitor.visit(self)
        for cmd in self.commands:
            cmd.accept(visitor)

class IfCommand(Entity, ResolutionSymbols):
    class ThenBlock(Block):
        def __init__(self, filename, lineno, commands, if_command):
            Block.__init__(self, filename, lineno, commands, if_command)

    class ElseBlock(Block):
        def __init__(self, filename, lineno, commands, if_command):
            Block.__init__(self, filename, lineno, commands, if_command)

    class EndIf(Entity):
         def __init__(self, filename, lineno, if_command):
            Entity.__init__(self, filename, lineno)
            self.if_command = if_command

         def accept(self, visitor):
             visitor.visit(self)

    def __init__(self,
                 filename,
                 lineno,
                 assignment,
                 condition,
                 then_commands,
                 else_commands,
                 endif_lineno):
        Entity.__init__(self, filename, lineno)
        ResolutionSymbols.__init__(self)
        self.assignment = assignment
        self.condition = condition
        self.then_commands = IfCommand.ThenBlock(filename, then_commands[0].lineno, then_commands, self)
        self.else_commands = IfCommand.ElseBlock(filename, else_commands[0].lineno, else_commands, self)
        self.endif = IfCommand.EndIf(filename, endif_lineno, self)

    def accept(self, visitor):
        visitor.visit(self)
        self.condition.accept(visitor)
        self.then_commands.accept(visitor)
        self.else_commands.accept(visitor)
        self.endif.accept(visitor)
        if self.assignment:
            self.assignment.accept(visitor)

    def __str__(self):
        f = lambda cmd: str(cmd)
        l = list()
        if self.assignment:
            l.append(str(self.assignment))
        l.extend(['if',
                  str(self.condition),
                  'then',
                  " ".join(map(f, self.then_commands)),
                  'else',
                  " ".join(map(f, self.else_commands)),
                  'endif'])
        return " ".join(l)

    def __repr__(self):
        f = lambda cmd: repr(cmd)
        return "<IfCommand:\n\tassignment = %s\n\tcondition = %s\n\tthen_commands = %s\n\t" \
               "else_commands = %s\n\tentity = %s>" % \
               (repr(self.assignment),
                repr(self.condition),
                " ".join(map(f, self.then_commands)),
                " ".join(map(f, self.else_commands)),
                super(IfCommand, self).__repr__())

class LetCommand(Entity, ResolutionSymbols):
    class LetBindings(Entity):
        def __init__(self,
                     filename,
                     lineno,
                     bindings):
            Entity.__init__(self, filename, lineno)
            self.bindings = bindings

        def __getitem__(self, idx):
            return self.bindings[idx]

        def __iter__(self):
            return self.bindings.__iter__()

        def accept(self, visitor):
            visitor.visit(self)
            for binding in self.bindings:
                binding.accept(visitor)

    class LetExpression(Entity):
        def __init__(self, filename, lineno, expression):
            Entity.__init__(self, filename, lineno)
            self.expression = expression

        def accept(self, visitor):
            visitor.visit(self)
            self.expression.accept(visitor)

    class LetEnd(Entity):
        def __init__(self, filename, lineno, let_command):
            Entity.__init__(self, filename, lineno)
            self.let_command = let_command

        def accept(self, visitor):
            visitor.visit(self)

    def __init__(self,
                 filename,
                 lineno,
                 assignment,
                 bindings,
                 expression):
        Entity.__init__(self, filename, lineno)
        ResolutionSymbols.__init__(self)
        self.assignment = assignment
        self.bindings = LetCommand.LetBindings(filename, bindings[0].lineno, bindings)
        self.expression = LetCommand.LetExpression(filename, expression.lineno, expression)
        self.let_end = LetCommand.LetEnd(filename, expression.lineno, self)

    def accept(self, visitor):
        visitor.visit(self)
        self.bindings.accept(visitor)
        self.expression.accept(visitor)
        self.let_end.accept(visitor)
        if self.assignment:
            self.assignment.accept(visitor)

    def __str__(self):
        l = list()
        if self.assignment:
            l.append(str(self.assignment))
        l.append('let')
        l.extend([str(b) for b in self.bindings])
        l.append('in')
        l.append(str(self.expression))
        return ' '.join(l)

    def __repr__(self):
        f = lambda t: repr(t)
        return "<LetCommand:\n\tassignment = %s\n\tbindings = %s\n\t" \
               "expression = %s\n\tentity = %s>" % \
               (repr(self.assignment),
                " ".join(map(f, self.bindings)),
                repr(self.expression),
                super(LetCommand, self).__repr__())

class MapCommand(Entity, ResolutionSymbols):
    class EndMap(Entity):
        def __init__(self, filename, lineno, map_command):
            Entity.__init__(self, filename, lineno)
            self.map_command = map_command

        def accept(self, visitor):
            visitor.visit(self)

    def __init__(self,
                 filename,
                 lineno,
                 assignment,
                 mapped_identifier,
                 iterable_identifier,
                 commands,
                 endmap_lineno):
        Entity.__init__(self, filename, lineno)
        ResolutionSymbols.__init__(self)
        self.assignment = assignment
        self.mapped_identifier = mapped_identifier
        self.iterable_identifier = iterable_identifier
        self.commands = commands
        self.endmap = MapCommand.EndMap(filename, endmap_lineno, self)

    def accept(self, visitor):
        visitor.visit(self)
        for cmd in self.commands:
            cmd.accept(visitor)
        self.endmap.accept(visitor)
        if self.assignment:
            self.assignment.accept(visitor)

    def __str__(self):
        l = list()
        if self.assignment:
            l.append(str(self.assignment))
        l.extend(['map',
                  str(self.mapped_identifier),
                  'from',
                  str(self.iterable_identifier),
                  " ".join(map(lambda c: str(c), self.commands)),
                  'endmap'])
        return " ".join(l)

    def __repr__(self):
        return "<MapCommand:\n\tassignment = %s\n\tmapped = %s\n\t" \
               "iterable = %s\n\tcommands = %s\n\tentity = %s>" % \
               (repr(self.assignment),
                repr(self.mapped_identifier),
                repr(self.iterable_identifier),
                " ".join(map(lambda c: str(c), self.commands)),
                super(MapCommand, self).__repr__())
