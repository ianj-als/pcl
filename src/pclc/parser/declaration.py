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

class Declaration(Entity):
    def __init__(self, filename, lineno, identifier, component_alias, configuration_mappings):
        Entity.__init__(self, filename, lineno)
        self.identifier = identifier
        self.component_alias = component_alias
        self.configuration_mappings = configuration_mappings

    def accept(self, visitor):
        visitor.visit(self)

    def __str__(self):
        return str(self.identifier)

    def __repr__(self):
        return "<Declaration: identifier = %s\n\tcomponent_alias = %s\n\t" \
               "config_mappings %s\n\tentity = %s>" % \
               (self.identifier.__repr__(), self.component_alias.__repr__(),
                self.configuration_mappings.__repr__(),
                super(Declaration, self).__repr__())

    def __hash__(self):
        return self.identifier.__hash__()

    def __eq__(self, other):
        if not isinstance(other, Declaration):
            return False
        return self.identifier == other.identifier
