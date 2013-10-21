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
from visitors.pcl_executor_visitor import PCLExecutorVisitor
from visitors.do_executor_visitor import DoExecutorVisitor

class Executor(object):
    def __init__(self, filename_root, is_instrumented = False):
        self.__filename_root = filename_root
        self.__is_instrumented = is_instrumented

    def execute(self, component):
        executor = DoExecutorVisitor(self.__filename_root, self.__is_instrumented) if component.definition.is_leaf \
                   else PCLExecutorVisitor(self.__filename_root, self.__is_instrumented)
        component.accept(executor)
