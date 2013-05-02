from entity import Entity

class Component(Entity):
    def __init__(self,
                 filename,
                 lineno,
                 identifier,
                 inputs,
                 outputs,
                 configuration,
                 declarations,
                 definition):
        Entity.__init__(self, filename, lineno)
        self.identifier = identifier
        self.inputs = inputs
        self.outputs = outputs
        self.configuration = configuration
        self.declarations = declarations
        self.definition = definition

    def accept(self, visitor):
        visitor.visit(self)
        for decl in self.declarations:
            decl.accept(visitor)
        self.definition.accept(visitor)

    def __str__(self):
        return str(self.identifier)

    def __repr__(self):
        return "<Component:\n\tname = %s,\n\tinputs = %s,\n\toutputs = %s," \
               "\n\tconfiguration = %s,\n\tdeclarations = %s\n\tdefinition = %s" \
               "\n\tentity = %s>" % \
               (self.identifier.__repr__(), self.inputs.__repr__(),
                self.outputs.__repr__(), self.configuration.__repr__(),
                self.declarations.__repr__(), self.definition.__repr__(),
                super(Component, self).__repr__())
