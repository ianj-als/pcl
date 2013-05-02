from visitors.first_pass_resolver_visitor import FirstPassResolverVisitor
from visitors.second_pass_resolver_visitor import SecondPassResolverVisitor


class Resolver(object):
    def __init__(self, pcl_import_path):
        self.__visitors = (FirstPassResolverVisitor(lambda pclip, pyip: Resolver(pclip, pyip),
                                                    pcl_import_path),
                           SecondPassResolverVisitor(lambda pclip, pyip: Resolver(pclip, pyip),
                                                    pcl_import_path))

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
