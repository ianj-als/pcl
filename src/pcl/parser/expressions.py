from entity import Entity

from mappings import TopMapping, BottomMapping, LiteralMapping


class Literal(Entity):
    def __init__(self, filename, lineno, value):
         Entity.__init__(self, filename, lineno)
         self.value = value

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return "<Literal: value = [%s], entity = %s>" % \
               (self.value.__repr__(),
                super(Literal, self).__repr__())

    def __hash__(self):
        return hash(self.value)

    def __eq__(self, other):
        if not isinstance(other, Literal):
            return False
        return self.value == other.value

    def __ne__(self, other):
        return not self.__eq__(other)

class Identifier(Entity):
    def __init__(self, filename, lineno, identifier):
        Entity.__init__(self, filename, lineno)
        self.identifier = identifier

    def __str__(self):
        return str(self.identifier)

    def __repr__(self):
        return "<Identifier: identifier = %s, entity = %s>" % \
               (self.identifier.__repr__(),
                super(Identifier, self).__repr__())

    def __hash__(self):
        return hash(self.identifier)

    def __eq__(self, other):
        if not isinstance(other, Identifier):
            return False
        return self.identifier == other.identifier

    def __ne__(self, other):
        return not self.__eq__(other)

class Expression(Entity):
    def __init__(self, filename, lineno, parent_expr = None):
        Entity.__init__(self, filename, lineno)
        self.parent = parent_expr
        self.resolution_symbols = dict()

    def accept(self, visitor):
        visitor.visit(self)

    def __repr__(self):
        return "<Expression:\n\tresolve syms = %s,\n\tentity = %s>" % \
               (self.resolution_symbols,
                super(Expression, self).__repr__())

class UnaryExpression(Expression):
     def __init__(self, filename, lineno, expression):
        Expression.__init__(self, filename, lineno)
        self.expression = expression
        self.expression.parent = self

     def accept(self, visitor):
         self.expression.accept(visitor)
         visitor.visit(self)

     def __repr__(self):
        return "<UnaryExpression:\n\tunary = %s,\n\texpression = %s>" % \
               (self.expression.__repr__(),
                super(UnaryExpression, self).__repr__())

class BinaryExpression(Expression):
    def __init__(self, filename, lineno, left_expr, right_expr):
        Expression.__init__(self, filename, lineno)
        self.left = left_expr
        self.left.parent = self
        self.right = right_expr
        self.right.parent = self

    def accept(self, visitor):
        self.left.accept(visitor)
        self.right.accept(visitor)
        visitor.visit(self)

    def __repr__(self):
        return "<BinaryExpression:\n\tleft = %s,\n\tright = %s,\n\texpression = %s>" % \
               (self.left.__repr__(),
                self.right.__repr__(),
                super(BinaryExpression, self).__repr__())

class CompositionExpression(BinaryExpression):
    def __init__(self, filename, lineno, left_expr, right_expr):
        BinaryExpression.__init__(self, filename, lineno, left_expr, right_expr)

    def __repr__(self):
        return "<CompositionExpression:\n\tbinary expr = %s>" % \
               (super(CompositionExpression, self).__repr__())

class ParallelWithTupleExpression(BinaryExpression):
     def __init__(self, filename, lineno, left_expr, right_expr):
        BinaryExpression.__init__(self, filename, lineno, left_expr, right_expr)

     def __repr__(self):
        return "<ParallelWithTupleExpression:\n\tbinary expr = %s>" % \
               (super(ParallelWithTupleExpression, self).__repr__())

class ParallelWithScalarExpression(BinaryExpression):
    def __init__(self, filename, lineno, left_expr, right_expr):
        BinaryExpression.__init__(self, filename, lineno, left_expr, right_expr)

    def __repr__(self):
        return "<ParallelWithScalarExpression:\n\tbinary expr = %s>" % \
               (super(ParallelWithTupleExpression, self).__repr__())

class FirstExpression(UnaryExpression):
    def __init__(self, filename, lineno, expr):
        UnaryExpression.__init__(self, filename, lineno, expr)

    def __repr__(self):
        return "<FirstExpression:\n\tunary expr = %s>" % \
               (super(FirstExpression, self).__repr__())

class SecondExpression(UnaryExpression):
    def __init__(self, filename, lineno, expr):
        UnaryExpression.__init__(self, filename, lineno, expr)

    def __repr__(self):
        return "<SecondExpression:\n\tunary expr = %s>" % \
               (super(SecondExpression, self).__repr__())

class SplitExpression(Expression):
    def __init__(self, filename, lineno):
        Expression.__init__(self, filename, lineno)

    def __repr__(self):
        return "<SplitExpression:\n\texpression = %s>" % \
               (super(SplitExpression, self).__repr__())

class MergeExpression(Expression):
    def __init__(self, filename, lineno, merge_mapping):
        Expression.__init__(self, filename, lineno)
        self.top_mapping = filter(lambda m: isinstance(m, TopMapping),
                                  merge_mapping)
        self.bottom_mapping = filter(lambda m: isinstance(m, BottomMapping),
                                     merge_mapping)
        self.literal_mapping = filter(lambda m: isinstance(m, LiteralMapping),
                                      merge_mapping)
        for m in self.top_mapping + self.bottom_mapping + self.literal_mapping:
            m.parent = self

    def accept(self, visitor):
        for merge_map in self.top_mapping + self.bottom_mapping + self.literal_mapping:
            merge_map.accept(visitor)
        visitor.visit(self)

    def __repr__(self):
        return "<MergeExpression:\n\ttop = %s,\n\tbottom = %s\n\tliteral = %s, expr = %s>" % \
               (self.top_mapping.__repr__(),
                self.bottom_mapping.__repr__(),
                self.literal_mapping.__repr__(),
                super(MergeExpression, self).__repr__())

class WireExpression(Expression):
    def __init__(self, filename, lineno, wire_mapping):
        Expression.__init__(self, filename, lineno)
        self.mapping = wire_mapping
        for m in self.mapping:
            m.parent = self

    def accept(self, visitor):
        for map_ in self.mapping:
            map_.accept(visitor)
        visitor.visit(self)

    def __repr__(self):
        return "<WireExpression: mapping = %s, expression = %s>" % \
               (self.mapping.__repr__(),
                super(WireExpression, self).__repr__())

class WireTupleExpression(Expression):
    def __init__(self, filename, lineno, top_wire_mapping, bottom_wire_mapping):
        Expression.__init__(self, filename, lineno)
        self.top_mapping = top_wire_mapping
        for tm in self.top_mapping:
            tm.parent = self
        self.bottom_mapping = bottom_wire_mapping
        for bm in self.bottom_mapping:
            bm.parent = self

    def accept(self, visitor):
        for top_map in self.top_mapping:
            top_map.accept(visitor)
        for bottom_map in self.bottom_mapping:
            bottom_map.accept(visitor)
        visitor.visit(self)

    def __repr__(self):
        return "<WireTupleExpression: top mapping = %s, bottom mapping = %s, expression = %s>" % \
               (self.top_mapping.__repr__(),
                self.bottom_mapping.__repr__(),
                super(WireTupleExpression, self).__repr__())

class IdentifierExpression(Expression):
    def __init__(self, filename, lineno, identifier, parent = None):
        Expression.__init__(self, filename, lineno, parent)
        self.identifier = identifier

    def accept(self, visitor):
        visitor.visit(self)

    def __str__(self):
        return str(self.identifier)

    def __repr__(self):
        return "<IdentifierExpression:\n\tidentifier = %s,\n\texpression = %s>" % \
               (self.identifier.__repr__(),
                super(IdentifierExpression, self).__repr__())

    def __hash__(self):
        return self.identifier.__hash__()

    def __eq__(self, other):
        return self.identifier.__eq__(other.identifier)

class LiteralExpression(Expression):
    def __init__(self, filename, lineno, literal):
        Expression.__init__(self, filename, lineno)
        self.literal = literal

    def accept(self, visitor):
        visitor.visit(self)

    def __str__(self):
        return str(self.literal)

    def __repr__(self):
        return "<LiteralExpression:\n\tliteral = %s,\n\texpression = %s>" % \
               (self.literal.__repr__(),
                super(LiteralExpression, self).__repr__())
