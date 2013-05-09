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
class Entity(object):
    def __init__(self, filename, lineno):
        self.filename = filename
        self.lineno = lineno

    def accept(self, visitor):
        visitor.visit(self)

    def __str__(self):
        return "%s at line %d" % (self.filename, self.lineno)

    def __repr__(self):
        return "<Entity: filename = %s, line no = %d>" % \
               (self.filename.__repr__(),
                self.lineno)
