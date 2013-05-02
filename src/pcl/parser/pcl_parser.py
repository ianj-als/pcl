#
# Pipeline Creation Language Parser
#
import ply.yacc as yacc

from pcl_lexer import tokens, PCLLexer
from import_spec import Import
from component import Component
from declaration import Declaration
from expressions import Literal, \
     Identifier, \
     UnaryExpression, \
     CompositionExpression, \
     ParallelWithTupleExpression, \
     ParallelWithScalarExpression, \
     FirstExpression, \
     SecondExpression, \
     SplitExpression, \
     MergeExpression, \
     WireExpression, \
     WireTupleExpression, \
     IdentifierExpression, \
     LiteralExpression
from mappings import Mapping, \
     TopMapping, \
     BottomMapping, \
     LiteralMapping
from module import Module


precedence = (('nonassoc', 'NONASSOC'),
              ('left', 'COMPOSITION', 'PARALLEL_WITH_TUPLE', 'PARALLEL_WITH_SCALAR'),
              ('right', 'UNARY'))

def p_module(p):
    '''module : opt_imports_list component_definition'''
    p[0] = Module(p.parser.filename, p.lineno(1), p[1], p[2])
    # Store the parent module in the imports and definition objects
    for import_ in p[1]:
        import_.module = p[0]
    p[2].module = p[0]

def p_opt_imports_list(p):
    '''opt_imports_list : imports_list
                        | '''
    if len(p) > 1:
        p[0] = p[1]
    else:
        p[0] = list()

def p_imports_list(p):
    '''imports_list : import_spec imports_list
                    | import_spec'''
    if len(p) > 2:
        p[0] = [p[1]] + p[2]
    else:
        p[0] = [p[1]]

def p_import_spec(p):
    '''import_spec : IMPORT identifier_or_qual_identifier AS IDENTIFIER'''
    p[0] = Import(p.parser.filename,
                  p.lineno(1),
                  p[2],
                  Identifier(p.parser.filename, p.lineno(4), p[4]))

def p_component_definition(p):
    '''component_definition : COMPONENT IDENTIFIER INPUTS scalar_or_tuple_identifier_comma_list OUTPUTS scalar_or_tuple_identifier_comma_list opt_configuration opt_declarations AS component_body_expression'''
    p[0] = Component(p.parser.filename,
                     p.lineno(1),
                     Identifier(p.parser.filename, p.lineno(2), p[2]),
                     p[4],
                     p[6],
                     p[7],
                     p[8],
                     p[10])

def p_opt_configuration(p):
    '''opt_configuration : CONFIGURATION identifier_comma_list
                         | '''
    if len(p) > 1:
        p[0] = p[2]
    else:
        p[0] = list()

def p_opt_declarations(p):
    '''opt_declarations : DECLARE declarations
                        | '''
    if len(p) > 1:
        p[0] = p[2]
    else:
        p[0] = list()

def p_declarations(p):
    '''declarations : declaration declarations
                    | declaration'''
    if len(p) > 2:
        p[0] = [p[1]] + p[2]
    else:
        p[0] = [p[1]]

def p_declaration(p):
    '''declaration : IDENTIFIER ASSIGN NEW IDENTIFIER opt_with_clause'''
    p[0] = Declaration(p.parser.filename,
                       p.lineno(1),
                       Identifier(p.parser.filename, p.lineno(1), p[1]),
                       Identifier(p.parser.filename, p.lineno(4), p[4]),
                       p[5])

def p_opt_with_clause(p):
    '''opt_with_clause : WITH configuration_mappings
                       | '''
    if len(p) > 1:
        p[0] = p[2]

def p_configuration_mappings(p):
    '''configuration_mappings : mapping ',' configuration_mappings
                              | mapping'''
    if len(p) > 2:
        p[0] = [p[1]] + p[3]
    else:
        p[0] = [p[1]]

def p_mapping(p):
    '''mapping : identifier_or_literal MAPS_TO identifier_or_qual_identifier'''
    p[0] = Mapping(p.parser.filename, p[1].lineno, p[1], p[3])

def p_component_body(p):
    '''component_body_expression : expression'''
    p[0] = p[1]

def p_expression(p):
    '''expression : composition_expression'''
    p[0] = p[1]

def p_composition_expression(p):
    '''composition_expression : parallel_with_tuple_expression
                              | composition_expression COMPOSITION parallel_with_tuple_expression'''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = CompositionExpression(p.parser.filename, p[1].lineno, p[1], p[3])

def p_parallel_with_tuple_expression(p):
    '''parallel_with_tuple_expression : parallel_with_scalar_expression
                                      | parallel_with_tuple_expression PARALLEL_WITH_TUPLE parallel_with_scalar_expression'''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = ParallelWithTupleExpression(p.parser.filename, p[1].lineno, p[1], p[3])

def p_parallel_with_scalar_expression(p):
    '''parallel_with_scalar_expression : unary_expression
                                       | parallel_with_scalar_expression PARALLEL_WITH_SCALAR unary_expression'''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = ParallelWithScalarExpression(p.parser.filename, p[1].lineno, p[1], p[3])

def p_unary_expression(p):
    '''unary_expression : first_expression
                        | second_expression
                        | split_expression
                        | merge_expression
                        | wire_expression
                        | identifier_expression
                        | literal_expression
                        | '(' expression ')' '''
    if len(p) > 2:
        p[0] = UnaryExpression(p.parser.filename, p[2].lineno, p[2])
    else:
        p[0] = p[1]

def p_first_expression(p):
    '''first_expression : FIRST expression %prec UNARY'''
    p[0] = FirstExpression(p.parser.filename, p.lineno(1), p[2])

def p_second_expression(p):
     '''second_expression : SECOND expression %prec UNARY'''
     p[0] = SecondExpression(p.parser.filename, p.lineno(1), p[2])

def p_split_expression(p):
    '''split_expression : SPLIT %prec NONASSOC'''
    p[0] = SplitExpression(p.parser.filename, p.lineno(1))

def p_merge_expression(p):
    '''merge_expression : MERGE merge_mappings %prec NONASSOC'''
    p[0] = MergeExpression(p.parser.filename, p.lineno(1), p[2])

def p_wire_expression(p):
    '''wire_expression : WIRE wire_mappings %prec NONASSOC
                       | WIRE '(' wire_mappings ')' ',' '(' wire_mappings ')' %prec UNARY'''
    if len(p) < 4:
        p[0] = WireExpression(p.parser.filename, p.lineno(1), tuple(p[2]))
    else:
        p[0] = WireTupleExpression(p.parser.filename,
                                   p.lineno(1),
                                   tuple(p[3]),
                                   tuple(p[7]))

def p_identifier_expression(p):
    '''identifier_expression : identifier_or_qual_identifier'''
    p[0] = IdentifierExpression(p.parser.filename, p[1].lineno, p[1])

def p_literal_expression(p):
    '''literal_expression : literal'''
    p[0] = LiteralExpression(p.parser.filename, p[1].lineno, p[1])

def p_merge_mappings(p):
    '''merge_mappings : merge_mapping ',' merge_mappings
                      | merge_mapping'''
    if len(p) > 2:
        p[0] = [p[1]] + p[3]
    else:
        p[0] = [p[1]]

def p_merge_mapping(p):
    '''merge_mapping : TOP '[' identifier_or_qual_identifier ']' MAPS_TO identifier_or_qual_identifier
                     | BOTTOM '[' identifier_or_qual_identifier ']' MAPS_TO identifier_or_qual_identifier
                     | literal MAPS_TO identifier_or_qual_identifier'''
    if str(p[1]).upper() == 'TOP':
        p[0] = TopMapping(p.parser.filename, p.lineno(1), p[3], p[6])
    elif str(p[1]).upper() == 'BOTTOM':
        p[0] = BottomMapping(p.parser.filename, p.lineno(1), p[3], p[6])
    else:
        p[0] = LiteralMapping(p.parser.filename, p.lineno(1), p[1], p[3])

def p_wire_mappings(p):
    '''wire_mappings : wire_mapping ',' wire_mappings
                     | wire_mapping'''
    if len(p) > 2:
        p[0] = [p[1]] + p[3]
    else:
        p[0] = [p[1]]

def p_wire_mapping(p):
    '''wire_mapping : identifier_or_qual_identifier MAPS_TO identifier_or_qual_identifier'''
    p[0] = Mapping(p.parser.filename, p[1].lineno, p[1], p[3])

def p_scalar_or_tuple_identifier_comma_list(p):
    '''scalar_or_tuple_identifier_comma_list : '(' identifier_comma_list ')' ',' '(' identifier_comma_list ')'
                                             | identifier_comma_list'''
    if len(p) > 2:
        p[0] = (p[2], p[6])
    else:
        p[0] = p[1]

def p_identifier_comma_list(p):
    '''identifier_comma_list : identifier_or_qual_identifier ',' identifier_comma_list
                             | identifier_or_qual_identifier'''
    if len(p) > 2:
        p[0] = [p[1]] + p[3]
    else:
        p[0] = [p[1]]

def p_identifier_or_literal(p):
    '''identifier_or_literal : identifier_or_qual_identifier
                             | literal'''
    p[0] = p[1]

def p_identifier_or_qual_identifier(p):
    '''identifier_or_qual_identifier : IDENTIFIER
                                     | QUALIFIED_IDENTIFIER'''
    p[0] = Identifier(p.parser.filename, p.lineno(1), p[1])

def p_literal(p):
    '''literal : INTEGER
               | FLOAT
               | STRING'''
    p[0] = Literal(p.parser.filename, p.lineno(1), p[1])

def p_error(p):
    print "ERROR: line %d parser failure at or near %s" % \
           (p.lineno,
            p.type)
    yacc.errok()

class PCLParser(object):
    def __init__(self, lexer, logger, **kwargs):
        self.__lexer = lexer
        self.__logger = logger
        kwargs['debuglog'] = logger
        self.__parser = yacc.yacc(**kwargs)

    def parseFile(self, filename, **kwargs):
        self.__parser.filename = filename
        f = open(filename, "r")
        return self.__parser.parse(input = f.read(),
                                   lexer = self.__lexer,
                                   debug = self.__logger)

if __name__ == '__main__':
    lexer = PCLLexer(debug = 1)
    parser = yacc.yacc()
    parser.filename = "internal"
    component = parser.parse(
        input = '''
        import twat.arse.feck as bum
        import feck.arse.twat as feck
        component arse
          inputs a,b,c
          output (a,b,c)
          configuration a,b,c,d
          declare
            a := new arse
            b := new bum with a -> b, c -> d
            irstlm := new lang_model with
              a -> b,
              b -> c,
              c -> d
          as
          a >>> b &&& c *** a >>> wire a -> b, d -> c >>> first (split >>> f >>> merge top[d] -> g, bottom[d] -> f)''',
        lexer = lexer,
        debug = 1)
    if component:
        print "Imports: [%s], Component def: [%s]" % \
              (", ".join([str(e) for e in component['imports']]), component['definition'])
