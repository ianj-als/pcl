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

class Component(Entity):
    def __init__(self,
                 filename,
                 lineno,
                 identifier,
                 inputs,
                 outputs,
                 configuration,
                 declarations,
                 definition,
                 is_leaf):
        Entity.__init__(self, filename, lineno)
        self.identifier = identifier
        self.inputs = inputs
        self.outputs = outputs
        self.configuration = configuration
        self.declarations = declarations
        self.definition = definition
        self.is_leaf = is_leaf

    @staticmethod
    def getLeafComponent(filename,
                         lineno,
                         identifier,
                         inputs,
                         outputs,
                         configuration,
                         do_commands):
        class LeafDefinition(Entity):
            def __init__(self):
                self.filename = filename
                self.lineno = do_commands[0].lineno
                self.do_commands = do_commands

            def accept(self, visitor):
                for cmd in self.do_commands:
                    cmd.accept(visitor)
                         
        return Component(filename,
                         lineno,
                         identifier,
                         inputs,
                         outputs,
                         configuration,
                         list(),
                         LeafDefinition(),
                         True)

    @staticmethod
    def getNodeComponent(filename,
                         lineno,
                         identifier,
                         inputs,
                         outputs,
                         configuration,
                         declarations,
                         definition):
        return Component(filename,
                         lineno,
                         identifier,
                         inputs,
                         outputs,
                         configuration,
                         declarations,
                         definition,
                         False)

    def accept(self, visitor):
        visitor.visit(self)
        for decl in self.declarations:
            decl.accept(visitor)
        self.definition.accept(visitor)

    def __str__(self):
        return str(self.identifier)

    def __repr__(self):
        return "<Component:\n\tname = %s,\n\tinputs = %s,\n\toutputs = %s," \
               "\n\tconfiguration = %s,\n\tdeclarations = %s,\n\tdefinition = %s," \
               "\n\tentity = %s>" % \
               (self.identifier.__repr__(), self.inputs.__repr__(),
                self.outputs.__repr__(), self.configuration.__repr__(),
                self.declarations.__repr__(), self.definition.__repr__(),
                super(Component, self).__repr__())
