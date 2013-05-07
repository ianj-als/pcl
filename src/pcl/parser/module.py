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

class Module(Entity):
    def __init__(self, filename, lineno, imports, component_definition):
        Entity.__init__(self, filename, lineno)
        self.imports = imports
        self.definition = component_definition

    def accept(self, visitor):
        visitor.visit(self)
        for an_import in self.imports:
            an_import.accept(visitor)
        self.definition.accept(visitor)
        visitor.visit(object())

    def __str__(self):
        return self.filename

    def __repr__(self):
        return "<Module:\n\timports = %s,\n\tdefinition = %s,\n\tentity = %s>" % \
               (self.imports.__repr__(),
                self.definition.__repr__(),
                super(Module, self).__repr__())
