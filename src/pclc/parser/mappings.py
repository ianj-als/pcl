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

class Mapping(Entity):
    def __init__(self, filename, lineno, from_identifier, to_identifier):
        Entity.__init__(self, filename, lineno)
        self.from_ = from_identifier
        self.to = to_identifier

    def accept(self, visitor):
        visitor.visit(self)

    def __str__(self):
        return "%s -> %s" % (self.from_, self.to)

    def __repr__(self):
        return "<Mapping: from = %s,\n\tto = %s\n\tentity = %s>" % \
               (self.from_.__repr__(),
                self.to.__repr__(),
                super(Mapping, self).__repr__())

class TopMapping(Mapping):
    def __init__(self, filename, lineno, from_identifier, to_identifier):
        Mapping.__init__(self, filename, lineno, from_identifier, to_identifier)

    def __repr__(self):
        return "<TopMapping: from = %s,\n\tto = %s\n\tentity = %s>" % \
               (self.from_.__repr__(),
                self.to.__repr__(),
                super(TopMapping, self).__repr__())

class BottomMapping(Mapping):
    def __init__(self, filename, lineno, from_identifier, to_identifier):
        Mapping.__init__(self, filename, lineno, from_identifier, to_identifier)

    def __repr__(self):
        return "<BottomMapping: from = %s,\n\tto = %s\n\tentity = %s>" % \
               (self.from_.__repr__(),
                self.to.__repr__(),
                super(BottomMapping, self).__repr__())

class LiteralMapping(Entity):
    def __init__(self, filename, lineno, literal, to_identifier):
        Entity.__init__(self, filename, lineno)
        self.literal = literal
        self.to = to_identifier

    def accept(self, visitor):
        visitor.visit(self)

    def __str__(self):
        return "%s -> %s" % (self.literal, self.to)

    def __repr__(self):
        return "<LiteralMapping: literal = %s,\n\tto = %s\n\tentity = %s>" % \
               (self.literal.__repr__(),
                self.to.__repr__(),
                super(LiteralMapping, self).__repr__())

class ReturnMapping(Mapping):
    def __init__(self, filename, lineno, from_, to_identifier):
        Mapping.__init__(self, filename, lineno, from_, to_identifier)

    def __str__(self):
        return "%s <- %s" % (self.to, self.from_)

    def __repr__(self):
        return "<ReturnMapping: from = %s,\n\tto = %s\n\tentity = %s>" % \
               (self.from_.__repr__(),
                self.to.__repr__(),
                super(ReturnMapping, self).__repr__())    
