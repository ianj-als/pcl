from entity import Entity

class Declaration(Entity):
    def __init__(self, filename, lineno, identifier, component_alias, configuration_mappings):
        Entity.__init__(self, filename, lineno)
        self.identifier = identifier
        self.component_alias = component_alias
        self.configuration_mappings = configuration_mappings

    def accept(self, visitor):
        visitor.visit(self)

    def __str__(self):
        return str(self.identifier)

    def __repr__(self):
        return "<Declaration: identifier = %s\n\tcomponent_alias = %s\n\t" \
               "config_mappings %s\n\tentity = %s>" % \
               (self.identifier.__repr__(), self.component_alias.__repr__(),
                self.configuration_mappings.__repr__(),
                super(Declaration, self).__repr__())

    def __hash__(self):
        return self.identifier.__hash__()

    def __eq__(self, other):
        if not isinstance(other, Declaration):
            return False
        return self.identifier == other.identifier
