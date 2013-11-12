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
class SymbolTable(object):
    def __init__(self):
        self.__table = dict()
        self.__nested_scopes = list()
        self.__parent = None

    def add_nested_scope(self, scope):
        scope.__parent = self
        return self.__nested_scopes.append(scope)

    def get_parent(self):
        return self.__parent

    def in_current_scope(self, key):
        return key in self.__table

    def __getitem__(self, key):
        return self.__table[key]

    def __setitem__(self, key, value):
        self.__table[key] = value

    def __delitem__(self, key):
        del self.__table[key]

    def __contains__(self, item):
        scope = self
        while scope is not None:
            if item in scope.__table:
                return True
            scope = scope.__parent

        return False

    def __iteritems__(self):
        return self.__table.__iteritems__()

    def iterkeys(self):
        return self.__table.iterkeys()

    def keys(self):
        return self.__table.keys()

    def has_key(self, key):
        return self.__table.has_key(key)

    def __str__(self):
        disp = lambda s, d: ("  " * d) + ("%d : " % d) + ", ".join([str(sym) for sym in s.keys()]) + "\n"

        def trav(st):
            if st is None:
                return (0, "")

            depth, result = trav(st.__parent)
            return (depth + 1, result + disp(st, depth))

        return trav(self)[1]
