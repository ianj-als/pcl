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

class Import(Entity):
    def __init__(self, filename, lineno, module_name, alias):
        Entity.__init__(self, filename, lineno)
        self.module_name = module_name
        self.alias = alias

    def __str__(self):
        return str(self.module_name)

    def __repr__(self):
        return "<ImportSpec: module = [%s], alias = [%s], entity = %s>" % \
               (self.module_name.__repr__(),
                self.alias.__repr__(),
                super(Import, self).__repr__())
