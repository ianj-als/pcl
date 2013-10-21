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


class Function(Entity):
    def __init__(self,
                 filename,
                 lineno,
                 name,
                 arguments):
        Entity.__init__(self, filename, lineno)
        self.name = name
        self.arguments = arguments

    def accept(self, visitor):
        visitor.visit(self)

    def __str__(self):
        return "%s(%s)" % \
               (str(self.name),
                ", ".join(map(lambda arg: str(arg), self.arguments)))

    def __repr__(self):
        return "<Function:\n\tname = %s\n\targuments = %s\n\tentity = %s>" % \
               (self.name.__repr__(),
                ", ".join(map(lambda arg: arg.__repr__(), self.arguments)),
                super(Function, self).__repr__())

class Command(Entity):
    def __init__(self,
                 filename,
                 lineno,
                 identifier,
                 function):
        Entity.__init__(self, filename, lineno)
        self.identifier = identifier
        self.function = function

    def accept(self, visitor):
        self.function.accept(visitor)
        visitor.visit(self)

    def __str__(self):
        l = [str(self.function)]
        if self.identifier:
            l.insert(0, "<-")
            l.insert(0, str(self.identifier))
        return " ".join(l)
                    
    def __repr__(self):
        return "<Command:\n\tidentifier = %s,\n\tfunction = %s,\n\t" \
               "entity = %s>" % \
               (self.identifier.__repr__() if self.identifier else None,
                self.function.__repr__(), super(Command, self).__repr__())

class Return(Entity):
    def __init__(self,
                 filename,
                 lineno,
                 mappings):
        Entity.__init__(self, filename, lineno)
        self.mappings = mappings

    def accept(self, visitor):
        visitor.visit(self)

    def __str__(self):
        return "return %s" % \
               ("()" if not self.mappings \
                     else ", ".join(map(lambda m: str(m), self.mappings)))

    def __repr__(self):
        return "<Return:\n\tmappings = %s\n\tentity = %s>" % \
               ("()" if not self.mappings \
                     else ", ".join(map(lambda m: m.__repr__(), self.mappings)), \
                super(Return, self).__repr__())

class IfCommand(Entity):
    class Block(Entity):
        def __init__(self, filename, lineno, commands):
            Entity.__init__(self, filename, lineno)
            self.commands = commands

        def __iter__(self):
            return self.commands.__iter__()

        def accept(self, visitor):
            visitor.visit(self)
            for cmd in self.commands:
                cmd.accept(visitor)

    class ThenBlock(Block):
        def __init__(self, filename, lineno, commands):
            IfCommand.Block.__init__(self, filename, lineno, commands)

    class ElseBlock(Block):
        def __init__(self, filename, lineno, commands):
            IfCommand.Block.__init__(self, filename, lineno, commands)

    def __init__(self,
                 filename,
                 lineno,
                 condition,
                 then_commands,
                 else_commands):
        Entity.__init__(self, filename, lineno)
        self.condition = condition
        self.then_commands = IfCommand.ThenBlock(filename, then_commands[0].lineno, then_commands)
        self.else_commands = IfCommand.ElseBlock(filename, else_commands[0].lineno, else_commands)

    def accept(self, visitor):
        self.condition.accept(visitor)
        self.then_commands.accept(visitor)
        self.else_commands.accept(visitor)
        visitor.visit(self)

    def __str__(self):
        f = lambda cmd: str(cmd)
        l = ['if',
             str(self.condition),
             'then',
             " ".join(map(f, then_commands)),
             'else',
             " ".join(map(f, else_commands)),
             'endif']
        return " ".join(l)

    def __repr__(self):
        f = lambda cmd: cmd.__repr__()
        return "<IfCommand:\n\tcondition = %s,\n\tthen_commands = %s,\n\t" \
               "else_commands = %s\n\tentity = %s>" % \
               (self.condition.__repr__(), " ".join(map(f, self.then_commands)),
                " ".join(map(f, self.else_commands)), super(IfCommand, self).__repr__())
