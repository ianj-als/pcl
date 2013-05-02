import os
import sys

from parser.helpers import parse_component
from parser.resolver import Resolver
from visitors.executor_visitor import ExecutorVisitor


if __name__ == '__main__':
    ast = parse_component(sys.argv[1])

    resolver = Resolver(os.getenv("PCL_IMPORT_PATH", "."))
    resolver.resolve(ast)
    for warning in resolver.get_warnings():
        print warning
    if resolver.has_errors():
        for error in resolver.get_errors():
            print error
    else:
        executor = ExecutorVisitor()
        ast.accept(executor)
