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
class ScopedNameGenerator(object):
    def __init__(self, name_prefix):
        self.__prefix = name_prefix
        self.__table = dict()
        self.__number = 0
        # A default scope
        self.__table[None] = dict()

    def get_name(self, thing, scope = None):
        name = "%s_%d" % (self.__prefix, self.__number)
        if scope in self.__table:
            scoped_table = self.__table[scope]
        else:
            scoped_table = dict()
            self.__table[scope] = scoped_table

        scoped_table[thing] = name
        self.__number += 1
        return name

    def register_name(self, thing, name, scope = None):
        if scope in self.__table:
            scoped_table = self.__table[scope]
        else:
            scoped_table = dict()
            self.__table[scope] = scoped_table

        scoped_table[thing] = name

    def lookup_name(self, thing, scope = None):
        scoped_table = self.__table[scope]
        return scoped_table[thing]

    def iter_names(self, scope = None):
        return self.__table[scope].iterkeys()

    def remove_name(self, thing, scope = None):
        scoped_table = self.__table[scope]
        return scoped_table.pop(thing)
