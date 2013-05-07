#!/usr/bin/env python
import os
import sys

from parser.helpers import parse_component
from parser.resolver import Resolver
from visitors.executor_visitor import ExecutorVisitor


if __name__ == '__main__':
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
    ast = parse_component(pcl_filename)
    if not ast:
        sys.exit(1)

    resolver = Resolver(os.getenv("PCL_IMPORT_PATH", "."))
    resolver.resolve(ast)
    for warning in resolver.get_warnings():
        print warning
    if resolver.has_errors():
        for error in resolver.get_errors():
            print error
        sys.exit(1)
    else:
        executor = ExecutorVisitor(basename_bits[0])
        ast.accept(executor)

    sys.exit(0)
