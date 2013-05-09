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
class ResolverVisitor(object):
    def __init__(self):
        self._errors = list()
        self._warnings = list()

    @staticmethod
    def __add_messages(msg_fmt, collection, unpack_fn, msg_collection):
        for entity in collection:
            info = unpack_fn(entity)
            msg_collection.append(msg_fmt % info)

    def _add_errors(self, msg_fmt, collection, unpack_fn):
        ResolverVisitor.__add_messages(msg_fmt,
                                       collection,
                                       unpack_fn,
                                       self._errors)

    def _add_warnings(self, msg_fmt, collection, unpack_fn):
        ResolverVisitor.__add_messages(msg_fmt,
                                       collection,
                                       unpack_fn,
                                       self._warnings)

    def has_errors(self):
        return len(self._errors) > 0

    def get_errors(self):
        return tuple(self._errors)

    def has_warnings(self):
        return len(self._warnings) > 0

    def get_warnings(self):
        return tuple(self._warnings)
