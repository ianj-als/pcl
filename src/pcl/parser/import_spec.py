from entity import Entity

class Import(Entity):
    def __init__(self, filename, lineno, module_name, alias):
        Entity.__init__(self, filename, lineno)
        self.module_name = module_name
        self.alias = alias

    def __str__(self):
        return self.module_name

    def __repr__(self):
        return "<ImportSpec: module = [%s], alias = [%s], entity = %s>" % \
               (self.module_name.__repr__(),
                self.alias.__repr__(),
                super(Import, self).__repr__())
