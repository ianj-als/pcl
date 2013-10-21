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
    class Scope(object):
        def __init__(self):
            self.__table = dict()
            self.__nested_scopes = list()
            self.__root = None

        def addNestedScope(self, scope):
            scope.__root = self
            return self.__nested_scopes.append(scope)

        def getRoot(self):
            return self.__root

        def __getitem__(self, key):
            return self.__table[key]

        def __setitem__(self, key, value):
            self.__table[key] = value

        def __delitem__(self, key):
            del self.__table[key]

        def __contains__(self, item):
            return item in self.__table

        def __iteritems__(self):
            return self.__table.__iteritems__()

        def iterkeys(self):
            return self.__table.iterkeys()

        def keys(self):
            return self.__table.keys()

        def has_key(self, key):
            return self.__table.has_key(key)

        def _get_nested_scopes_iter(self):
            return self.__nested_scopes.__iter__()

    def __init__(self):
        self.__tree = SymbolTable.Scope()
        self.__current_scope = self.__tree

    def __getitem__(self, key):
        scope = self.__current_scope
        while scope is not None:
            if scope.has_key(key):
                return scope[key]
            scope.getRoot()

        raise KeyError

    def __setitem__(self, key, value):
        self.__current_scope[key] = value

    def __contains__(self, item):
        scope = self.__current_scope
        while scope is not None:
            if item in scope:
                return True
            scope = scope.getRoot()

        return False

    def push_inner_scope(self):
        scope = SymbolTable.Scope()
        self.__current_scope.addNestedScope(scope)
        self.__current_scope = scope

    def pop_inner_scope(self):
        outer_scope = self.__current_scope.getRoot()
        if outer_scope is not None:
            self.__current_scope = outer_scope

    def __str__(self):
        disp = lambda s, d: ("  " * d) + ("%d : " % d) + ", ".join([str(sym) for sym in s.keys()]) + "\n"

        def trav(s, d):
            rep = disp(s, d)
            for ns in s._get_nested_scopes_iter():
                rep += trav(ns, d + 1)
            return rep
        
        return trav(self.__tree, 0)
