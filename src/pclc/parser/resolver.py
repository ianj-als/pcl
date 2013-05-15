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
from visitors.first_pass_resolver_visitor import FirstPassResolverVisitor
from visitors.second_pass_resolver_visitor import SecondPassResolverVisitor
from visitors.third_pass_resolver_visitor import ThirdPassResolverVisitor


class Resolver(object):
    def __init__(self, pcl_import_path):
        self.__visitors = (FirstPassResolverVisitor(pcl_import_path),
                           SecondPassResolverVisitor(),
                           ThirdPassResolverVisitor())

    def resolve(self, ast):
        for visitor in self.__visitors:
            ast.accept(visitor)

    def has_warnings(self):
        return reduce(lambda acc, r: acc + int(r.has_warnings()),
                      self.__visitors,
                      0) > 0

    def get_warnings(self):
        return reduce(lambda acc, r: acc.extend(r.get_warnings()) or acc,
                      self.__visitors,
                      list())

    def has_errors(self):
        return reduce(lambda acc, r: acc + int(r.has_errors()),
                      self.__visitors,
                      0) > 0

    def get_errors(self):
        return reduce(lambda acc, r: acc.extend(r.get_errors()) or acc,
                      self.__visitors,
                      list())
