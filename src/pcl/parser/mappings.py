from entity import Entity

class Mapping(Entity):
    def __init__(self, filename, lineno, from_identifier, to_identifier):
        Entity.__init__(self, filename, lineno)
        self.from_ = from_identifier
        self.to = to_identifier

    def accept(self, visitor):
        visitor.visit(self)

    def __str__(self):
        return "%s -> %s" % (self.from_, self.to)

    def __repr__(self):
        return "<Mapping: from = %s,\n\tto = %s\n\tentity = %s>" % \
               (self.from_.__repr__(),
                self.to.__repr__(),
                super(Mapping, self).__repr__())

class TopMapping(Mapping):
    def __init__(self, filename, lineno, from_identifier, to_identifier):
        Mapping.__init__(self, filename, lineno, from_identifier, to_identifier)

    def __repr__(self):
        return "<TopMapping: from = %s,\n\tto = %s\n\tentity = %s>" % \
               (self.from_.__repr__(),
                self.to.__repr__(),
                super(TopMapping, self).__repr__())

class BottomMapping(Mapping):
    def __init__(self, filename, lineno, from_identifier, to_identifier):
        Mapping.__init__(self, filename, lineno, from_identifier, to_identifier)

    def __repr__(self):
        return "<BottomMapping: from = %s,\n\tto = %s\n\tentity = %s>" % \
               (self.from_.__repr__(),
                self.to.__repr__(),
                super(BottomMapping, self).__repr__())

class LiteralMapping(Entity):
    def __init__(self, filename, lineno, literal, to_identifier):
        Entity.__init__(self, filename, lineno)
        self.literal = literal
        self.to = to_identifier

    def accept(self, visitor):
        visitor.visit(self)

    def __str__(self):
        return "%s -> %s" % (self.literal, self.to)

    def __repr__(self):
        return "<LiteralMapping: literal = %s,\n\tto = %s\n\tentity = %s>" % \
               (self.literal.__repr__(),
                self.to.__repr__(),
                super(LiteralMapping, self).__repr__())
