#!/usr/bin/env python
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
import os
import sys
import traceback

from optparse import OptionParser
from parser.helpers import parse_component
from parser.resolver import Resolver
from parser.executor import Executor


__VERSION = "1.2.0"


if __name__ == '__main__':
    # The option parser
    parser = OptionParser("Usage: %prog [options] [PCL file]")
    parser.add_option("-l",
                      "--loglevel",
                      default = "WARN",
                      dest = "loglevel",
                      help = "parser log file reporting level [default: %default]")
    parser.add_option("-i",
                      "--instrument",
                      action = "store_true",
                      default = False,
                      dest = "is_instrumented",
                      help = "Generated code shall instrument components")
    parser.add_option("-v",
                      "--version",
                      action = "store_true",
                      default = False,
                      dest = "version",
                      help = "show version and exit")
    (options, args) = parser.parse_args()

    # Show version?
    if options.version is True:
        print __VERSION
        sys.exit(0)

    # Check we've got at least one command line argument
    if len(args) < 1:
        print >> sys.stderr, "ERROR: no input file"
        sys.exit(2)

    # Add the PCL extension is one is missing
    basename = os.path.basename(args[0])
    basename_bits = basename.split(".")
    if len(basename_bits) == 1:
        # Add the PCL extension on
        basename_bits.append("pcl")

    # PCL file name
    pcl_filename = os.path.join(os.path.dirname(args[0]), ".".join(basename_bits))
    if os.path.isfile(pcl_filename) is False:
        print >> sys.stderr, "ERROR: Cannot find file %s" % pcl_filename
        sys.exit(1)

    # Parse...
    ast = parse_component(pcl_filename, options.loglevel)
    if not ast:
        sys.exit(1)

    # Resolve...
    resolver = Resolver(os.getenv("PCL_IMPORT_PATH", "."))
    resolver.resolve(ast)
    for warning in resolver.get_warnings():
        print >> sys.stderr, warning
    if resolver.has_errors():
        for error in resolver.get_errors():
            print >> sys.stderr, error
        sys.exit(1)

    # Execute.
    executor = Executor(basename_bits[0], options.is_instrumented)
    try:
        executor.execute(ast)
    except Exception as ex:
        print >> sys.stderr, traceback.format_exc()
        print >> sys.stderr, "ERROR: Code generation failed: %s" % ex
        sys.exit(1)

    sys.exit(0)
