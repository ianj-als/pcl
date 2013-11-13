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
#
# Pipeline Creation Language Parser
#
import ply.yacc as yacc
import sys

from pcl_lexer import tokens, PCLLexer
from import_spec import Import
from component import Component
from declaration import Declaration
from command import Command, Function, Return, IfCommand, LetCommand
from conditional_expressions import AndConditionalExpression, \
     OrConditionalExpression, \
     XorConditionalExpression, \
     EqualsConditionalExpression, \
     NotEqualsConditionalExpression, \
     GreaterThanConditionalExpression, \
     LessThanConditionalExpression, \
     GreaterThanEqualToConditionalExpression, \
     LessThanEqualToConditionalExpression, \
     UnaryConditionalExpression, \
     TerminalConditionalExpression
from expressions import Literal, \
     Identifier, \
     StateIdentifier, \
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
     IfExpression, \
     IdentifierExpression
from mappings import Mapping, \
     TopMapping, \
     BottomMapping, \
     LiteralMapping, \
     ReturnMapping
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
    '''component_definition : COMPONENT IDENTIFIER INPUTS scalar_or_tuple_identifier_comma_list OUTPUTS scalar_or_tuple_identifier_comma_list opt_configuration opt_declarations AS arrow_expression
                            | COMPONENT IDENTIFIER INPUTS scalar_or_tuple_identifier_comma_list OUTPUTS scalar_or_tuple_identifier_comma_list opt_configuration DO do_commands'''
    lineno = p.lineno(1)
    identifier = Identifier(p.parser.filename, p.lineno(2), p[2])
    if len(p) > 10:
        p[0] = Component.getNodeComponent(p.parser.filename,
                                          lineno,
                                          identifier,
                                          p[4],
                                          p[6],
                                          p[7],
                                          p[8],
                                          p[10])
    else:
        p[0] = Component.getLeafComponent(p.parser.filename,
                                          lineno,
                                          identifier,
                                          p[4],
                                          p[6],
                                          p[7],
                                          p[9])

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
                       p[5] if p[5] else list())

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

def p_arrow_expression(p):
    '''arrow_expression : composition_expression'''
    p[0] = p[1]

def p_composition_expression(p):
    '''composition_expression : parallel_with_tuple_expression
                              | composition_expression COMPOSITION parallel_with_tuple_expression'''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = CompositionExpression(p.parser.filename, p.lineno(2), p[1], p[3])

def p_parallel_with_tuple_expression(p):
    '''parallel_with_tuple_expression : parallel_with_scalar_expression
                                      | parallel_with_tuple_expression PARALLEL_WITH_TUPLE parallel_with_scalar_expression'''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = ParallelWithTupleExpression(p.parser.filename, p.lineno(2), p[1], p[3])

def p_parallel_with_scalar_expression(p):
    '''parallel_with_scalar_expression : unary_expression
                                       | parallel_with_scalar_expression PARALLEL_WITH_SCALAR unary_expression'''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = ParallelWithScalarExpression(p.parser.filename, p.lineno(2), p[1], p[3])

def p_unary_expression(p):
    '''unary_expression : first_expression
                        | second_expression
                        | split_expression
                        | merge_expression
                        | wire_expression
                        | if_expression
                        | identifier_expression
                        | '(' arrow_expression ')' '''
    if len(p) > 2:
        p[0] = UnaryExpression(p.parser.filename, p[2].lineno, p[2])
    else:
        p[0] = p[1]

def p_first_expression(p):
    '''first_expression : FIRST arrow_expression %prec UNARY'''
    p[0] = FirstExpression(p.parser.filename, p.lineno(1), p[2])

def p_second_expression(p):
     '''second_expression : SECOND arrow_expression %prec UNARY'''
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

def p_if_expression(p):
    '''if_expression : IF conditional_expression arrow_expression arrow_expression'''
    p[0] = IfExpression(p.parser.filename, p.lineno(1), p[2], p[3], p[4])

def p_identifier_expression(p):
    '''identifier_expression : identifier_or_qual_identifier'''
    p[0] = IdentifierExpression(p.parser.filename, p[1].lineno, p[1])

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
    '''wire_mapping : identifier_or_qual_identifier MAPS_TO identifier_or_qual_identifier
                    | literal MAPS_TO identifier_or_qual_identifier'''
    if isinstance(p[1], Literal):
        p[0] = LiteralMapping(p.parser.filename, p[1].lineno, p[1], p[3])
    else:
        p[0] = Mapping(p.parser.filename, p[1].lineno, p[1], p[3])

def p_conditional_expression(p):
    '''conditional_expression : or_conditional_expression'''
    p[0] = p[1]

def p_or_conditional_expression(p):
    '''or_conditional_expression : and_conditional_expression
                                 | or_conditional_expression OR and_conditional_expression'''
    if len(p) > 2:
        p[0] = OrConditionalExpression(p.parser.filename, p.lineno(2), p[1], p[3])
    else:
        p[0] = p[1]

def p_and_conditional_expression(p):
    '''and_conditional_expression : xor_conditional_expression
                                  | and_conditional_expression AND xor_conditional_expression'''
    if len(p) > 2:
        p[0] = AndConditionalExpression(p.parser.filename, p.lineno(2), p[1], p[3])
    else:
        p[0] = p[1]

def p_xor_conditional_expression(p):
    '''xor_conditional_expression : equals_conditional_expression
                                  | xor_conditional_expression XOR equals_conditional_expression'''
    if len(p) > 2:
        p[0] = XorConditionalExpression(p.parser.filename, p.lineno(2), p[1], p[3])
    else:
        p[0] = p[1]

def p_equals_conditional_expression(p):
    '''equals_conditional_expression : not_equals_conditional_expression
                                     | equals_conditional_expression EQUALS not_equals_conditional_expression'''
    if len(p) > 2:
        p[0] = EqualsConditionalExpression(p.parser.filename, p.lineno(2), p[1], p[3])
    else:
        p[0] = p[1]

def p_not_equals_conditional_expression(p):
    '''not_equals_conditional_expression : greater_than_conditional_expression
                                         | not_equals_conditional_expression NOT_EQUALS greater_than_conditional_expression'''
    if len(p) > 2:
        p[0] = NotEqualsConditionalExpression(p.parser.filename, p.lineno(2), p[1], p[3])
    else:
        p[0] = p[1]

def p_greater_than_conditional_expression(p):
    '''greater_than_conditional_expression : less_than_conditional_expression
                                           | greater_than_conditional_expression GT less_than_conditional_expression'''
    if len(p) > 2:
        p[0] = GreaterThanConditionalExpression(p.parser.filename, p.lineno(2), p[1], p[3])
    else:
        p[0] = p[1]

def p_less_than_conditional_expression(p):
    '''less_than_conditional_expression : greater_than_equal_conditional_expression
                                        | less_than_conditional_expression LT greater_than_conditional_expression'''
    if len(p) > 2:
        p[0] = LessThanConditionalExpression(p.parser.filename, p.lineno(2), p[1], p[3])
    else:
        p[0] = p[1]

def p_greater_than_equal_conditional_expression(p):
    '''greater_than_equal_conditional_expression : less_than_equal_condition_expression
                                                 | greater_than_equal_conditional_expression G_EQUAL less_than_conditional_expression'''
    if len(p) > 2:
        p[0] = GreaterThanEqualToConditionalExpression(p.parser.filename, p.lineno(2), p[1], p[3])
    else:
        p[0] = p[1]

def p_less_than_equal_condition_expression(p):
    '''less_than_equal_condition_expression : unary_conditional_expression
                                            | less_than_conditional_expression L_EQUAL unary_conditional_expression'''
    if len(p) > 2:
        p[0] = LessThanEqualToConditionalExpression(p.parser.filename, p.lineno(2), p[1], p[3])
    else:
        p[0] = p[1]

def p_unary_conditional_expression(p):
    '''unary_conditional_expression : identifier_or_literal
                                    | state_identifier
                                    | '(' conditional_expression ')' '''
    if len(p) > 2:
        p[0] = UnaryConditionalExpression(p.parser.filename, p[2].lineno, p[2])
    else:
        p[0] = TerminalConditionalExpression(p[1])

def p_do_commands(p):
    '''do_commands : opt_do_command_list RETURN return_mapping_list'''
    p[1].append(Return(p.parser.filename, p.lineno(2), None, p[3]))
    p[0] = p[1]

def p_opt_do_commmand_list(p):
    '''opt_do_command_list : do_command_list
                           | '''
    if len(p) > 1:
        p[0] = p[1]
    else:
        p[0] = list()

def p_do_command_list(p):
    '''do_command_list : do_command do_command_list
                       | do_command'''
    if len(p) > 2:
        p[0] = p[1] + p[2]
    else:
        p[0] = p[1]

def p_do_command(p):
    '''do_command : identifier_or_qual_identifier LEFT_ARROW function
                  | function
                  | LET let_bindings IN function
                  | identifier_or_qual_identifier LEFT_ARROW LET let_bindings IN function
                  | IF conditional_expression THEN opt_do_command_list return_command ELSE opt_do_command_list return_command ENDIF
                  | identifier_or_qual_identifier LEFT_ARROW IF conditional_expression THEN opt_do_command_list return_command ELSE opt_do_command_list return_command ENDIF'''
    p[0] = list()
    if len(p) > 10:
        # len(p) == 12
        p[6].append(p[7])
        p[9].append(p[10])
        p[0].append(IfCommand(p.parser.filename, p[1].lineno, p[1], p[4], p[6], p[9], p.lineno(11)))
    elif len(p) > 9:
        # len(p) == 10
        p[4].append(p[5])
        p[7].append(p[8])
        p[0].append(IfCommand(p.parser.filename, p.lineno(1), None, p[2], p[4], p[7], p.lineno(9)))
    elif len(p) > 6:
        # len(p) == 7
        p[0].append(LetCommand(p.parser.filename, p.lineno(1), p[1], p[4], p[6]))
    elif len(p) > 4:
        # len(p) == 5
        p[0].append(LetCommand(p.parser.filename, p.lineno(1), None, p[2], p[4]))
    elif len(p) > 3:
        # len(p) == 4
        p[0].append(Command(p.parser.filename, p[1].lineno, p[1], p[3]))
    else:
        # len(p) == 2
        p[0].append(Command(p.parser.filename, p[1].lineno, None, p[1]))

def p_let_bindings(p):
    '''let_bindings : let_binding let_bindings
                    | let_binding'''
    if len(p) > 2:
        p[0] = [p[1]] + p[2]
    else:
        p[0] = [p[1]]

def p_let_binding(p):
    '''let_binding : identifier_or_qual_identifier LEFT_ARROW function'''
    p[0] = Command(p.parser.filename, p[1].lineno, p[1], p[3])

def p_function(p):
    '''function : QUALIFIED_IDENTIFIER '(' opt_function_args ')' '''
    p[0] = Function(p.parser.filename, p.lineno(1), p[1], p[3])

def p_opt_function_args(p):
    '''opt_function_args : function_arg_list
                         | '''
    if len(p) > 1:
        p[0] = p[1]
    else:
        p[0] = list()

def p_function_arg_list(p):
    '''function_arg_list : function_arg ',' function_arg_list
                         | function_arg'''
    if len(p) > 2:
        p[0] = [p[1]] + p[3]
    else:
        p[0] = [p[1]]

def p_function_arg(p):
    '''function_arg : identifier_or_literal
                    | state_identifier'''
    p[0] = p[1]

def p_return_command(p):
    '''return_command : RETURN '(' ')'
                      | RETURN function_arg
                      | RETURN literal'''
    if len(p) > 3:
        p[0] = Return(p.parser.filename, p.lineno(1))
    else:
        p[0] = Return(p.parser.filename, p.lineno(1), p[2])

def p_return_mapping_list(p):
    '''return_mapping_list : return_mapping ',' return_mapping_list
                           | return_mapping'''
    if len(p) > 2:
        p[0] = [p[1]] + p[3]
    else:
        p[0] = [p[1]]

def p_return_mapping(p):
    '''return_mapping : identifier_or_qual_identifier LEFT_ARROW identifier_or_literal
                      | identifier_or_qual_identifier LEFT_ARROW state_identifier'''
    p[0] = ReturnMapping(p.parser.filename,
                         p[1].lineno,
                         p[3],
                         p[1])

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

def p_state_identifier(p):
    '''state_identifier : '@' identifier_or_qual_identifier'''
    p[0] = StateIdentifier(p.parser.filename, p[2].lineno, p[2].identifier)

def p_identifier_or_qual_identifier(p):
    '''identifier_or_qual_identifier : IDENTIFIER
                                     | QUALIFIED_IDENTIFIER'''
    p[0] = Identifier(p.parser.filename, p.lineno(1), p[1])

def p_literal(p):
    '''literal : INTEGER
               | FLOAT
               | STRING
               | BOOLEAN'''
    p[0] = Literal(p.parser.filename, p.lineno(1), p[1])

recovery_tokens = (')',
                   'COMPOSITION',
                   'PARALLEL_WITH_TUPLE',
                   'PARALLEL_WITH_SCALAR',
                   'AS',
                   'DECLARE',
                   'DO',
                   'IF',
                   'RETURN')

def p_error(token):
    if not token:
        print >> sys.stderr, "ERROR: Unexpected EOF"
    else:
        print >> sys.stderr, "ERROR: line %d parser failure at or near %s" % \
                             (token.lineno, token.type)

        while True:
            tok = yacc.token()
            if not tok or tok.type in recovery_tokens:
                break
        yacc.restart()

class PCLParser(object):
    def __init__(self, lexer, logger, **kwargs):
        self.__lexer = lexer
        self.__logger = logger
        if 'debuglog' not in kwargs:
            kwargs['debuglog'] = logger
        if 'errorlog' not in kwargs:
            kwargs['errorlog'] = logger
        self.__parser = yacc.yacc(**kwargs)

    def parseFile(self, filename, **kwargs):
        self.__parser.filename = filename
        f = open(filename, "r")
        return self.__parser.parse(input = f.read(),
                                   lexer = self.__lexer,
                                   debug = self.__logger)
