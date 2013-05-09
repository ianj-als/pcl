#
# Copyright Capita Translation and Interpreting 2013
#!/usr/bin/env python
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
import os
import sys

from parser.helpers import parse_component
from parser.resolver import Resolver
from visitors.executor_visitor import ExecutorVisitor


if __name__ == '__main__':
    # Check we've got at least one command line argument
    if len(sys.argv) < 2:
        print "Usage:"
        print "\t%s [PCL filename]" % os.path.basename(sys.argv[0])
        print
        sys.exit(2)

    # Add the PCL extension is one is missing
    basename = os.path.basename(sys.argv[1])
    basename_bits = basename.split(".")
    if len(basename_bits) == 1:
        # Add the PCL extension on
        basename_bits.append("pcl")

    # PCL file name
    pcl_filename = os.path.join(os.path.dirname(sys.argv[1]), ".".join(basename_bits))
    if os.path.isfile(pcl_filename) is False:
        print "ERROR: Cannot find file %s" % pcl_filename
        sys.exit(1)

    # Parse...
    ast = parse_component(pcl_filename)
    if not ast:
        sys.exit(1)

    # Resolve...
    resolver = Resolver(os.getenv("PCL_IMPORT_PATH", "."))
    resolver.resolve(ast)
    for warning in resolver.get_warnings():
        print warning
    if resolver.has_errors():
        for error in resolver.get_errors():
            print error
        sys.exit(1)

    # Execute.
    executor = ExecutorVisitor(basename_bits[0])
    try:
        ast.accept(executor)
    except Exception as ex:
        print "ERROR: Code generation failed: %s" % ex
        sys.exit(1)

    sys.exit(0)
