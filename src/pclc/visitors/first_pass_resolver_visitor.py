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
import collections
import glob
import inspect
import os
import sys
import types

from multimethod import multimethod, multimethodclass
from parser.import_spec import Import
from parser.command import Function, Command, Return, IfCommand, LetCommand
from parser.component import Component
from parser.conditional_expressions import AndConditionalExpression, \
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
from parser.declaration import Declaration
from parser.expressions import Literal, \
     Identifier, \
     StateIdentifier, \
     Expression, \
     UnaryExpression, \
     BinaryExpression, \
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
from parser.mappings import Mapping, \
     TopMapping, \
     BottomMapping, \
     LiteralMapping
from parser.module import Module
from parser.helpers import parse_component
from pypeline.core.types.just import Just
from pypeline.core.types.nothing import Nothing
from resolver_visitor import ResolverVisitor
from symbol_table import SymbolTable


# Decorator to prevent resolving more than once
def resolve_expression_once(method):
    def resolve_once_wrapper(target_obj, *args, **kwargs):
        expr = args[0]
        if isinstance(expr, Expression) and \
           (expr.resolution_symbols.has_key('inputs') is False or \
            expr.resolution_symbols.has_key('outputs') is False or \
            isinstance(expr.resolution_symbols['inputs'], Nothing) or \
            isinstance(expr.resolution_symbols['outputs'], Nothing)):
            return method(target_obj, *args, **kwargs)

    return resolve_once_wrapper


# Format component types
type_formatting_fn = lambda c: "(%s), (%s)" % (", ".join([i.identifier for i in c[0]]), \
                                            ", ".join([i.identifier for i in c[1]])) \
                    if isinstance(c, tuple) \
                    else ", ".join([i.identifier for i in c])


@multimethodclass
class FirstPassResolverVisitor(ResolverVisitor):
    def __init__(self, pcl_import_path = []):
        ResolverVisitor.__init__(self)
        self.__pcl_import_paths = list()
        if pcl_import_path is not None:
            if pcl_import_path:
                self.__pcl_import_paths.extend(pcl_import_path.split(":"))
            self.__pcl_import_paths.append(".")
            sys.path.extend(self.__pcl_import_paths)

    @staticmethod
    def __check_scalar_or_tuple_collection(collection):
        if isinstance(collection, list):
            return [x for x, y in collections.Counter(collection).items() if y > 1]
        elif isinstance(collection, tuple):
            a = [x for x, y in collections.Counter(collection[0]).items() if y > 1]
            a.extend([x for x, y in collections.Counter(collection[1]).items() if y > 1])
            return a

        return list()

    @staticmethod
    def __check_declarations(configuration, declarations, imports):
        # The configuration identifier to count map
        config = dict()
        if configuration:
            for c in configuration:
                config[c] = 0

        dups = dict()
        missing_config = []
        unknown_imports = []
        unknown_module_configuration = []
        python_module_interface = []

        if declarations:
            for decl in declarations:
                # Count occurrences of declaration identifiers
                try:
                    dups[decl] += 1
                except KeyError:
                    dups[decl] = 1

                import_module_name = None
                import_module_config = []

                # Lookup component alias in module symbol table
                try:
                    import_module_spec = imports[decl.component_alias]
                    # Get the module inputs from the Python module's
                    # get_inputs() function
                    import_module_name = import_module_spec['module_name_id'].identifier
                    # If the module was not found, it was not imported and so
                    # the module spec will *not* have the Python module stored
                    if import_module_spec.has_key('module'):
                        try:
                            # The Python module's component inputs
                            import_module_config = [Identifier(import_module_spec['module'].__name__, 0, c) \
                                                    for c in import_module_spec['get_configuration_fn']()]
                        except AttributeError:
                            python_module_interface.append({'module_name' : import_module_name,
                                                            'missing_function' : 'get_configuration'})
                except KeyError:
                    # Ensures we have imported an alias that is being used
                    # in this declaration
                    unknown_imports.append(decl.component_alias)

                # Ensure the 'from' end of a declaration mapping
                # exits in the configuration
                if decl.configuration_mappings:
                    for config_map in decl.configuration_mappings:
                        # Ensure we have the identifier configured
                        if isinstance(config_map.from_, Identifier):
                            if config_map.from_ in config:
                                config[config_map.from_] += 1
                            else:
                                missing_config.append(config_map.from_)

                        # Ensure that the module being used has the inputs
                        # we expect on construction
                        if config_map.to not in import_module_config:
                            unknown_module_configuration.append({'module_name' : import_module_name,
                                                                 'config_map' : config_map})

        unused_config = filter(lambda ce: config[ce] == 0, config)
        duplicate_declarations = filter(lambda de: dups[de] > 1, dups)

        return (tuple(missing_config),
                set(unused_config),
                tuple(unknown_imports),
                tuple(duplicate_declarations),
                tuple(unknown_module_configuration),
                tuple(python_module_interface))

    def __add_identifiers_to_symbol_table(self, things, symbol_group_key):
        """Check for duplicate identifiers in a collection and add them
           to the module's symbol table. Return a tuple of duplicated
           identifiers."""
        symbol_dict = self._module.resolution_symbols[symbol_group_key]
        returns = list()
        for thing in things:
            if thing in symbol_dict:
                returns.append(thing)
            symbol_dict[thing] = thing
        return tuple(returns)

    @multimethod(Module)
    def visit(self, module):
        self._module = module
        if not self._module.__dict__.has_key("resolution_symbols"):
            global_symbol_table = SymbolTable()
            self._module.resolution_symbols = {'imports' : dict(),
                                               'components' : dict(),
                                               'used_components' : dict(),
                                               'used_imports' : dict(),
                                               'configuration' : dict(),
                                               'unused_configuration' : list(),
                                               'command_table' : list(),
                                               'symbol_table' : global_symbol_table}
            self._current_scope = global_symbol_table
        if not self.__dict__.has_key("__resolve_import"):
            self.__resolve_import = self.__resolve_runtime_import if self._module.definition.is_leaf \
                                    else self.__resolve_pcl_import

    @multimethod(Import)
    def visit(self, an_import):
        # Hu rah, we're about to import something. Very exciting
        import_symbol_dict = an_import.module.resolution_symbols['imports']

        # Add, only uniquely aliased, Python modules to symbol table
        if import_symbol_dict.has_key(an_import.alias):
            self._add_errors("ERROR: %(filename)s at line %(lineno)d, duplicate import alias found %(alias)s",
                             [an_import],
                             lambda i: {'filename' : i.filename,
                                        'lineno' : i.lineno,
                                        'alias' : i.alias})
        else:
            # Resolve the import
            module_spec = self.__resolve_import(an_import)

            # Always add the module alias as a key to the import dictionary
            import_symbol_dict[an_import.alias] = module_spec

            # Mark the import as not used for now ;)
            self._module.resolution_symbols['used_imports'][an_import.alias] = (an_import, False)

    def __resolve_runtime_import(self, an_import):
        imported_module = None
        try:
            imported_module = __import__(str(an_import.module_name), globals(), locals(), ['*'], -1)
        except Exception as ie:
            self._add_errors("ERROR: %(filename)s at line %(lineno)d, error importing " \
                             "module %(module_name)s: %(exception)s",
                             [an_import],
                             lambda i: {'filename' : i.filename,
                                        'lineno' : i.lineno,
                                        'module_name' : i.module_name,
                                        'exception' : str(ie)})

        module_spec = {}
        if imported_module:
            funcs_and_specs = [(o[0], inspect.getargspec(o[1])) \
                               for o in inspect.getmembers(imported_module, \
                                                           lambda t: inspect.isfunction(t))]
            for k, v in funcs_and_specs:
                if v.keywords:
                    self._add_warnings("WARNING: %(filename)s at line %(lineno)d, " \
                                       "dropping function %(func_name)s imported " \
                                       "from module %(module_name)s since arguments " \
                                       "are unsupported.",
                                       [k],
                                       lambda n: {'filename' : an_import.filename,
                                                  'lineno' : an_import.lineno,
                                                  'func_name' : k,
                                                  'module_name' : an_import.module_name})
                else:
                    module_spec[k] = v

        return module_spec

    def __resolve_pcl_import(self, an_import):
        # Import the Python module
        module_spec = {'module_name_id' : an_import.module_name}
        imported_module = None
        try:
            imported_module = __import__(str(an_import.module_name),
                                         fromlist = ['get_inputs',
                                                     'get_outputs',
                                                     'get_configuration',
                                                     'configure',
                                                     'initialise'])
        except Exception as ie:
            self._add_errors("ERROR: %(filename)s at line %(lineno)d, error importing " \
                             "module %(module_name)s: %(exception)s",
                             [an_import],
                             lambda i: {'filename' : i.filename,
                                        'lineno' : i.lineno,
                                        'module_name' : i.module_name,
                                        'exception' : str(ie)})

        # Default, or dummy, functions
        get_inputs_fn = lambda : []
        get_outputs_fn = lambda : []
        get_configuration_fn = lambda : []

        # Was the module imported?
        if imported_module:
            # Yes!
            try:
                get_inputs_fn = getattr(imported_module, 'get_inputs')
            except AttributeError:
                self._add_errors("ERROR: %(filename)s at line %(lineno)d, imported Python module %(module)s " \
                                 "does not define get_inputs function",
                                 [an_import],
                                 lambda i: {'filename' : i.filename,
                                            'lineno' : i.lineno,
                                            'module' : i.module_name})
            try:
                get_outputs_fn = getattr(imported_module, 'get_outputs')
            except AttributeError:
                self._add_errors("ERROR: %(filename)s at line %(lineno)d, imported Python module %(module)s " \
                                 "does not define get_outputs function",
                                 [an_import],
                                 lambda i: {'filename' : i.filename,
                                            'lineno' : i.lineno,
                                            'module' : i.module_name})
            try:
                get_configuration_fn = getattr(imported_module, 'get_configuration')
            except AttributeError:
                self._add_errors("ERROR: %(filename)s at line %(lineno)d, imported Python module %(module)s " \
                                 "does not define get_configuration function",
                                 [an_import],
                                 lambda i: {'filename' : i.filename,
                                            'lineno' : i.lineno,
                                            'module' : i.module_name})
            try:
                configure_fn = getattr(imported_module, 'configure')
            except AttributeError:
                self._errors.append("ERROR: %(filename)s at line %(lineno)d, imported Python module %(module)s " \
                                    "does not define configure function",
                                    [an_import],
                                    lambda i: {'filename' : i.filename,
                                               'lineno' : i.lineno,
                                               'module' : i.module_name})
            try:
                initialise_fn = getattr(imported_module, 'initialise')
            except AttributeError:
                self._errors.append("ERROR: %(filename)s at line %(lineno)d, imported Python module %(module)s " \
                                    "does not define initialise function",
                                    [an_import],
                                    lambda i: {'filename' : i.filename,
                                               'lineno' : i.lineno,
                                               'module' : i.module_name})

            # Record stuff from the imported Python module
            module_spec.update({'module' : imported_module,
                                'get_inputs_fn' : get_inputs_fn,
                                'get_outputs_fn' : get_outputs_fn,
                                'get_configuration_fn' : get_configuration_fn})
        else:
            # Record a dummy module
            module_spec.update({'get_inputs_fn' : get_inputs_fn,
                                'get_outputs_fn' : get_outputs_fn,
                                'get_configuration_fn' : get_configuration_fn})

        return module_spec

    @multimethod(Component)
    def visit(self, component):
        # Component name *must* be the same as the file name
        if str(component.identifier) != ".".join(os.path.basename(component.filename).split(".")[:-1]):
            self._add_errors("ERROR: %(filename)s at line %(lineno)d, component %(component)s should be " \
                             "declared in a file called %(component)s.pcl",
                             [component],
                             lambda e: {'filename' : component.filename,
                                        'lineno' : component.lineno,
                                        'component' : component.identifier})

        # Add the inputs, outputs, configuration and declaration identifiers to
        # the module's symbol table
        duplicate_inputs = FirstPassResolverVisitor.__check_scalar_or_tuple_collection(component.inputs)
        duplicate_outputs = FirstPassResolverVisitor.__check_scalar_or_tuple_collection(component.outputs)
        duplicate_config = self.__add_identifiers_to_symbol_table(component.configuration, 'configuration')
        duplicate_decl_identifiers = self.__add_identifiers_to_symbol_table(component.declarations, 'components')

        # Check that all the used configuration in declarations exist, and is used
        missing_configuration, \
        self._module.resolution_symbols['unused_configuration'], \
        unknown_imports, \
        duplicate_declarations, \
        unknown_module_configuration, \
        python_module_interace = FirstPassResolverVisitor.__check_declarations(component.configuration,
                                                                               component.declarations,
                                                                               component.module.resolution_symbols['imports'])

        self._add_errors("ERROR: %(filename)s at line %(lineno)d, only one input is supported",
                         [component.inputs[0]] if isinstance(component.inputs, tuple) and component.is_leaf else [],
                         lambda i: {'filename' : i.filename,
                                    'lineno' : i.lineno})
        self._add_errors("ERROR: %(filename)s at line %(lineno)d, only one output is supported",
                         [component.output[0]] if isinstance(component.outputs, tuple) and component.is_leaf else [],
                         lambda o: {'filename' : o.filename,
                                    'lineno' : o.lineno})
        self._add_errors("ERROR: %(filename)s at line %(lineno)d, input " \
                         "declaration contains duplicate identifier %(entity)s",
                         duplicate_inputs,
                         lambda e: {'entity' : e,
                                    'filename' : e.filename,
                                    'lineno' : e.lineno})
        self._add_errors("ERROR: %(filename)s at line %(lineno)d, output " \
                         "declaration contains duplicate identifier %(entity)s",
                         duplicate_outputs,
                         lambda e: {'entity' : e,
                                    'filename' : e.filename,
                                    'lineno' : e.lineno})
        self._add_errors("ERROR: %(filename)s at line %(lineno)d, configuration " \
                         "declaration contains duplicate identifier %(entity)s",
                         duplicate_config,
                         lambda e: {'entity' : e,
                                    'filename' : e.filename,
                                    'lineno' : e.lineno})
        self._add_errors("ERROR: %(filename)s at line %(lineno)d, component " \
                         "declaration contains duplicate identifier %(entity)s",
                         duplicate_decl_identifiers,
                         lambda e: {'entity' : e,
                                    'filename' : e.filename,
                                    'lineno' : e.lineno})
        self._add_errors("ERROR: %(filename)s at line %(lineno)d, component " \
                         "configuration does not exist %(entity)s",
                         missing_configuration,
                         lambda e: {'entity' : e,
                                    'filename' : e.filename,
                                    'lineno' : e.lineno})
        self._add_errors("ERROR: %(filename)s at line %(lineno)d, import not found " \
                         "in declaration of %(entity)s",
                         unknown_imports,
                         lambda e: {'entity' : e,
                                    'filename' : e.filename,
                                    'lineno' : e.lineno})
        self._add_errors("ERROR: %(filename)s at line %(lineno)d, duplicate declaration " \
                         "found %(entity)s",
                         duplicate_declarations,
                         lambda e: {'entity' : e,
                                    'filename' : e.filename,
                                    'lineno' : e.lineno})
        self._add_errors("ERROR: %(filename)s at line %(lineno)d, configuration %(entity)s " \
                         "used which is not defined in module %(module_name)s",
                         unknown_module_configuration,
                         lambda e: {'entity' : e['config_map'].to,
                                    'module_name' : e['module_name'],
                                    'filename' : e['config_map'].filename,
                                    'lineno' : e['config_map'].lineno})
        self._add_errors("ERROR: Python module %(module_name)s does not define " \
                         "mandatory function %(missing_function)s",
                         python_module_interace,
                         lambda e: e)

    @multimethod(Declaration)
    def visit(self, decl):
        # Check for missing construction configuration in a declaration
        imports_sym_table = self._module.resolution_symbols['imports']
        module_spec = imports_sym_table[decl.component_alias]
        expected_used_configuration = frozenset([Identifier(None, 0, c) for c in module_spec['get_configuration_fn']()])
        got_used_configuration = frozenset([m.to for m in decl.configuration_mappings])
        unused_configuration = expected_used_configuration - got_used_configuration
        if len(unused_configuration) > 0:
            self._add_errors("ERROR: %(filename)s at line %(lineno)d, missing configuration in declaration " \
                             "of component %(component)s with alias %(import_alias)s: %(missing)s",
                             [decl],
                             lambda d: {'filename' : d.filename,
                                        'lineno' : d.lineno,
                                        'component' : d.identifier,
                                        'import_alias' : d.component_alias,
                                        'missing' : ", ".join([str(i) for i in unused_configuration])})

        # Mark the declaration as not used, yet. ;)
        self._module.resolution_symbols['used_components'][decl.identifier] = False

        # Mark the import as used
        self._module.resolution_symbols['used_imports'][decl.component_alias] = (self._module.resolution_symbols['used_imports'][decl.component_alias][0],
                                                                                 True)

    @multimethod(object)
    def visit(self, nowt):
        # Look for unused components
        unused_component_aliases = reduce(lambda acc, e: acc + [e[0]],
                                          filter(lambda e: e[1] == False,
                                                 self._module.resolution_symbols['used_components'].iteritems()),
                                          list())
        # Look for unused imports
        unused_imports = reduce(lambda acc, e: acc + [e[0]],
                                filter(lambda e: e[1] == False,
                                       self._module.resolution_symbols['used_imports'].itervalues()),
                                list())
        self._add_warnings("WARNING: %(filename)s at line %(lineno)s, imported component %(component)s is not used",
                           unused_imports,
                           lambda e: {'filename' : e.filename,
                                      'lineno' : e.lineno,
                                      'component' : e.module_name})
        self._add_warnings("WARNING: %(filename)s at line %(lineno)d, component %(component)s is defined " \
                           "but not used",
                           unused_component_aliases,
                           lambda e: {'filename' : e.filename,
                                      'lineno' : e.lineno,
                                      'component' : e})
        self._add_warnings("WARNING: %(filename)s at line %(lineno)d, component " \
                           "configuration %(entity)s is not used",
                           self._module.resolution_symbols['unused_configuration'],
                           lambda e: {'entity' : e,
                                      'filename' : e.filename,
                                      'lineno' : e.lineno})

    @multimethod(UnaryExpression)
    def visit(self, unary_expr):
        # Unary expressions have the same inputs and outputs as thier expression
        unary_expr.resolution_symbols['inputs'] = unary_expr.expression.resolution_symbols['inputs']
        unary_expr.resolution_symbols['outputs'] = unary_expr.expression.resolution_symbols['outputs']

    # (>>>) :: Arrow c => a b c -> a c d -> a b d
    @multimethod(CompositionExpression)
    def visit(self, comp_expr):
        # The inputs and outputs for this composed component
        comp_expr.resolution_symbols['inputs'] = comp_expr.left.resolution_symbols['inputs']
        comp_expr.resolution_symbols['outputs'] = comp_expr.right.resolution_symbols['outputs']

    # *** :: Arrow a => a b c -> a b' c' -> a (b, b') (c, c')
    @multimethod(ParallelWithTupleExpression)
    def visit(self, para_tuple_expr):
        # Inputs and outputs of the top and bottom components
        top_inputs = para_tuple_expr.left.resolution_symbols['inputs']
        top_outputs = para_tuple_expr.left.resolution_symbols['outputs']
        bottom_inputs = para_tuple_expr.right.resolution_symbols['inputs']
        bottom_outputs = para_tuple_expr.right.resolution_symbols['outputs']

        # The inputs and outputs for this composed component
        para_tuple_expr.resolution_symbols['inputs'] = top_inputs >= \
                                                       (lambda tins: bottom_inputs >= \
                                                        (lambda bins: Just((tins, bins))))
        para_tuple_expr.resolution_symbols['outputs'] = top_outputs >= \
                                                        (lambda touts: bottom_outputs >= \
                                                         (lambda bouts: Just((touts, bouts))))

    # &&& : Arrow a => a b c -> a b c' -> a b (c c')
    @multimethod(ParallelWithScalarExpression)
    def visit(self, para_scalar_expr):
        # Use the available left and right component inputs to
        # construct the fanout input types, i.e., best guess.
        top_inputs = para_scalar_expr.left.resolution_symbols['inputs']
        bottom_inputs = para_scalar_expr.right.resolution_symbols['inputs']
        if top_inputs and bottom_inputs:
            inputs = top_inputs >= \
                     (lambda tins: bottom_inputs >= \
                      (lambda bins: Just(frozenset([i for i in tins.union(bins)]))))
        elif top_inputs:
            inputs = top_inputs
        else:
            inputs = bottom_inputs

        top_outputs = para_scalar_expr.left.resolution_symbols['outputs']
        bottom_outputs = para_scalar_expr.right.resolution_symbols['outputs']

        para_scalar_expr.resolution_symbols['inputs'] = inputs
        para_scalar_expr.resolution_symbols['outputs'] = top_outputs >= \
                                                         (lambda touts: bottom_outputs >= \
                                                          (lambda bouts: Just((touts, bouts))))

    @multimethod(FirstExpression)
    @resolve_expression_once
    def visit(self, first_expr):
        first_expr.resolution_symbols['inputs'] = Nothing()
        first_expr.resolution_symbols['outputs'] = Nothing()

    @multimethod(SecondExpression)
    @resolve_expression_once
    def visit(self, second_expr):
        second_expr.resolution_symbols['inputs'] = Nothing()
        second_expr.resolution_symbols['outputs'] = Nothing()

    @multimethod(SplitExpression)
    @resolve_expression_once
    def visit(self, split_expr):
        split_expr.resolution_symbols['inputs'] = Nothing()
        split_expr.resolution_symbols['outputs'] = Nothing()

    @multimethod(MergeExpression)
    @resolve_expression_once
    def visit(self, merge_expr):
        top_from_identifiers = [m.from_ for m in merge_expr.top_mapping]
        bottom_from_identifiers = [m.from_ for m in merge_expr.bottom_mapping]
        duplicate_top_in_identifiers = FirstPassResolverVisitor.__check_scalar_or_tuple_collection(top_from_identifiers)
        duplicate_bottom_in_identifiers = FirstPassResolverVisitor.__check_scalar_or_tuple_collection(bottom_from_identifiers)

        all_out_mappings = list(merge_expr.top_mapping)
        all_out_mappings.extend(merge_expr.bottom_mapping)
        all_out_mappings.extend(merge_expr.literal_mapping)

        all_to_identifiers = [m.to for m in all_out_mappings if str(m.to) != '_']
        duplicate_out_identifiers = FirstPassResolverVisitor.__check_scalar_or_tuple_collection(all_to_identifiers)

        if duplicate_top_in_identifiers or \
           duplicate_bottom_in_identifiers or \
           duplicate_out_identifiers:
            self._add_errors("ERROR: %(filename)s at line %(lineno)d, merge top mapping " \
                             "contains duplicate identifier %(entity)s",
                             duplicate_top_in_identifiers,
                             lambda e: {'entity' : e,
                                        'filename' : e.filename,
                                        'lineno' : e.lineno})
            self._add_errors("ERROR: %(filename)s at line %(lineno)d, merge bottom mapping " \
                             "contains duplicate identifier %(entity)s",
                             duplicate_bottom_in_identifiers,
                             lambda e: {'entity' : e,
                                        'filename' : e.filename,
                                        'lineno' : e.lineno})
            self._add_errors("ERROR: %(filename)s at line %(lineno)d, merge output mapping " \
                             "contains duplicate identifier %(entity)s",
                             duplicate_out_identifiers,
                             lambda e: {'entity' : e,
                                        'filename' : e.filename,
                                        'lineno' : e.lineno})

        merge_expr.resolution_symbols['inputs'] = Just((frozenset(top_from_identifiers), frozenset(bottom_from_identifiers)))
        merge_expr.resolution_symbols['outputs'] = Just(frozenset(all_to_identifiers))

    @multimethod(WireExpression)
    @resolve_expression_once
    def visit(self, wire_expr):
        inputs = [m.from_ for m in wire_expr.mapping if isinstance(m, Mapping)]
        outputs = [m.to for m in wire_expr.mapping if str(m.to) != '_']

        # Catch duplicates
        duplicate_in_identifiers = FirstPassResolverVisitor.__check_scalar_or_tuple_collection(inputs)
        duplicate_out_identifiers = FirstPassResolverVisitor.__check_scalar_or_tuple_collection(outputs)

        if duplicate_in_identifiers or duplicate_out_identifiers:
            self._add_errors("ERROR: %(filename)s at line %(lineno)d wire mapping " \
                             "contains duplicate input identifier %(entity)s",
                             duplicate_in_identifiers,
                             lambda e: {'entity' : e,
                                        'filename' : e.filename,
                                        'lineno' : e.lineno})
            self._add_errors("ERROR: %(filename)s at line %(lineno)d wire mapping " \
                             "contains duplicate outputs identifier %(entity)s",
                             duplicate_out_identifiers,
                             lambda e: {'entity' : e,
                                        'filename' : e.filename,
                                        'lineno' : e.lineno})

        wire_expr.resolution_symbols['inputs'] = Just(frozenset(inputs))
        wire_expr.resolution_symbols['outputs'] = Just(frozenset(outputs))

    @multimethod(WireTupleExpression)
    @resolve_expression_once
    def visit(self, wire_tuple_expr):
        top_inputs = [m.from_ for m in wire_tuple_expr.top_mapping if isinstance(m, Mapping)]
        top_outputs = [m.to for m in wire_tuple_expr.top_mapping if m.to.identifier != '_']
        bottom_inputs = [m.from_ for m in wire_tuple_expr.bottom_mapping if isinstance(m, Mapping)]
        bottom_outputs = [m.to for m in wire_tuple_expr.bottom_mapping if m.to.identifier != '_']

        # Catch duplicates
        duplicate_top_in_identifiers = FirstPassResolverVisitor.__check_scalar_or_tuple_collection(top_inputs)
        duplicate_top_out_identifiers = FirstPassResolverVisitor.__check_scalar_or_tuple_collection(top_outputs)
        duplicate_bottom_in_identifiers = FirstPassResolverVisitor.__check_scalar_or_tuple_collection(bottom_inputs)
        duplicate_bottom_out_identifier = FirstPassResolverVisitor.__check_scalar_or_tuple_collection(bottom_outputs)

        if duplicate_top_in_identifiers or \
           duplicate_top_out_identifiers or \
           duplicate_bottom_in_identifiers or \
           duplicate_bottom_out_identifier:
            self._add_errors("ERROR: %(filename)s at line %(lineno)d, tuple wire mapping " \
                             "contains duplicate top input identifier %(entity)s",
                             duplicate_top_in_identifiers,
                             lambda e: {'entity' : e,
                                        'filename' : e.filename,
                                        'lineno' : e.lineno})
            self._add_errors("ERROR: %(filename)s at line %(lineno)d, tuple wire mapping " \
                             "contains duplicate top output identifier %(entity)s",
                             duplicate_top_out_identifiers,
                             lambda e: {'entity' : e,
                                        'filename' : e.filename,
                                        'lineno' : e.lineno})
            self._add_errors("ERROR: %(filename)s at line %(lineno)d, tuple wire mapping " \
                             "contains duplicate bottom input identifier %(entity)s",
                             duplicate_bottom_in_identifiers,
                             lambda e: {'entity' : e,
                                        'filename' : e.filename,
                                        'lineno' : e.lineno})
            self._add_errors("ERROR: %(filename)s at line %(lineno)d, tuple wire mapping " \
                             "contains duplicate bottom output identifier %(entity)s",
                             duplicate_bottom_out_identifier,
                             lambda e: {'entity' : e,
                                        'filename' : e.filename,
                                        'lineno' : e.lineno})

        wire_tuple_expr.resolution_symbols['inputs'] = Just((frozenset(top_inputs), frozenset(bottom_inputs)))
        wire_tuple_expr.resolution_symbols['outputs'] = Just((frozenset(top_outputs), frozenset(bottom_outputs)))

    @multimethod(IfExpression)
    @resolve_expression_once
    def visit(self, if_expr):
        if_expr.resolution_symbols['inputs'] = Nothing()
        if_expr.resolution_symbols['outputs'] = Nothing()

    @multimethod(AndConditionalExpression)
    def visit(self, cond_expr):
        pass

    @multimethod(OrConditionalExpression)
    def visit(self, cond_expr):
        pass

    @multimethod(XorConditionalExpression)
    def visit(self, cond_expr):
        pass

    @multimethod(EqualsConditionalExpression)
    def visit(self, cond_expr):
        pass

    @multimethod(NotEqualsConditionalExpression)
    def visit(self, cond_expr):
        pass

    @multimethod(GreaterThanConditionalExpression)
    def visit(self, cond_expr):
        pass

    @multimethod(LessThanConditionalExpression)
    def visit(self, cond_expr):
        pass

    @multimethod(GreaterThanEqualToConditionalExpression)
    def visit(self, cond_expr):
        pass

    @multimethod(LessThanEqualToConditionalExpression)
    def visit(self, cond_expr):
        pass

    @multimethod(UnaryConditionalExpression)
    def visit(self, unary_cond_expr):
        pass

    @multimethod(TerminalConditionalExpression)
    def visit(self, term_cond_expr):
        term_cond_expr.scope = self._current_scope
        terminal = term_cond_expr.terminal
        if isinstance(terminal, StateIdentifier) and \
           terminal in self._module.resolution_symbols['unused_configuration']:
            self._module.resolution_symbols['unused_configuration'].remove(terminal)

    @multimethod(Mapping)
    def visit(self, mapping):
        pass

    @multimethod(TopMapping)
    def visit(self, mapping):
        pass

    @multimethod(BottomMapping)
    def visit(self, mapping):
        pass

    @multimethod(LiteralMapping)
    def visit(self, mapping):
        pass

    @multimethod(IdentifierExpression)
    @resolve_expression_once
    def visit(self, iden_expr):
        # Imports and components symbol tables are needed
        imports_sym_table = self._module.resolution_symbols['imports']
        comp_sym_table = self._module.resolution_symbols['components']

        # Lookup the declaration that made this identifier expression possible
        try:
            declaration = comp_sym_table[Declaration(None,
                                                     0,
                                                     iden_expr.identifier,
                                                     None,
                                                     [])]
        except KeyError:
            self._add_errors("ERROR: %(filename)s at line %(lineno)d, unknown component %(expr)s",
                             [iden_expr],
                             lambda i: {'filename' : i.filename,
                                        'lineno' : i.lineno,
                                        'expr' : i})
            iden_expr.resolution_symbols['inputs'] = Nothing()
            iden_expr.resolution_symbols['outputs'] = Nothing()
            return

        module_alias = declaration.component_alias
        module_spec = imports_sym_table[module_alias]

        # Mark component as used
        self._module.resolution_symbols['used_components'][declaration.identifier] = True

        # Create types
        transform_fn = lambda stuff: Nothing() if stuff is None \
                                     else Just((frozenset([Identifier(None, 0, i) for i in stuff[0]]),
                                                frozenset([Identifier(None, 0, i) for i in stuff[1]]))) \
                                     if isinstance(stuff, tuple) \
                                     else Just(frozenset([Identifier(None, 0, i) for i in stuff]))
        inputs_fn = module_spec.get('get_inputs_fn', lambda: None)
        outputs_fn = module_spec.get('get_outputs_fn', lambda: None)
        inputs = inputs_fn()
        outputs = outputs_fn()

        # Identifier's types
        iden_expr.resolution_symbols['inputs'] = transform_fn(inputs)
        iden_expr.resolution_symbols['outputs'] = transform_fn(outputs)

    @multimethod(Function)
    def visit(self, function):
        # Record the current scope in the entity's resolution symbols
        function['scope'] = self._current_scope

        # Get the package alias and function name
        package_alias, name = function.name.split(".")

        # The imports
        import_symbol_dict = self._module.resolution_symbols['imports']

        # Check the package alias has been imported
        if not import_symbol_dict.has_key(Identifier(None, -1, package_alias)):
            self._add_errors("ERROR: %(filename)s at line %(lineno)d, unknown function package alias %(alias)s",
                             [function],
                             lambda f: {'filename' : f.filename,
                                        'lineno' : f.lineno,
                                        'alias' : package_alias})

        # The key for the imports is an Identifier, so create an Identifier
        # from the string package alias derived from the function call.
        alias_identifier = Identifier(None, -1, package_alias)
        if import_symbol_dict.has_key(alias_identifier):
            functions = import_symbol_dict[alias_identifier]
            if not functions.has_key(name):
                self._add_errors("ERROR: %(filename)s at line %(lineno)d, unknown function %(alias)s.%(name)s",
                                 [function],
                                 lambda f: {'filename' : f.filename,
                                            'lineno' : f.lineno,
                                            'alias' : package_alias,
                                            'name' : name})
            else:
                # The argument spec from the imported module
                function_arg_spec = functions[name]
                no_defaults = len(function_arg_spec.defaults) if function_arg_spec.defaults else 0
                min_no_args = len(function_arg_spec.args) - no_defaults

                # If there are no argument default values and no var-args, then if the
                # the number of arguments does *not* match the function's definition
                # then that is an error.
                if no_defaults < 1 and not function_arg_spec.varargs:
                    # The number of expected arguments *is* the length of the ArgSpec.args
                    if len(function_arg_spec.args) != len(function.arguments):
                        self._add_errors("ERROR: %(filename)s at line %(lineno)d, function %(name)s called with " \
                                         "%(given)d arguments, expected %(required)d",
                                         [function],
                                         lambda f: {'filename' : f.filename,
                                                    'lineno' : f.lineno,
                                                    'name' : f.name,
                                                    'given' : len(f.arguments),
                                                    'required' : len(function_arg_spec.args)})
                elif no_defaults > 0 or function_arg_spec.varargs:
                    # If we have at least one default argument value or at least one var-args then
                    # if the minimum number of arguments expected for this function is less than
                    # the number of arguments in the function call then this is an error.
                    if len(function.arguments) < min_no_args:
                        self._add_errors("ERROR: %(filename)s at line %(lineno)d, function %(name)s called with " \
                                         "%(given)d arguments, expected at least %(required)d",
                                         [function],
                                         lambda f: {'filename' : f.filename,
                                                    'lineno' : f.lineno,
                                                    'name' : f.name,
                                                    'given' : len(f.arguments),
                                                    'required' : min_no_args})

            # Mark the import as used
            self._module.resolution_symbols['used_imports'][alias_identifier] = (self._module.resolution_symbols['used_imports'][alias_identifier][0],
                                                                                 True)

        # Check that the arguments are either inputs, configuration or assignment
        for argument in function.arguments:
            if isinstance(argument, StateIdentifier):
                if argument not in self._module.resolution_symbols['configuration']:
                    self._add_errors("ERROR: %(filename)s at line %(lineno)d, unknown function argument %(arg_name)s",
                                     [argument],
                                     lambda a: {'filename' : a.filename,
                                                'lineno' : a.lineno,
                                                'arg_name' : a})
                else:
                    # Mark the configuration as used
                    try:
                        self._module.resolution_symbols['unused_configuration'].remove(argument)
                    except KeyError:
                        # We may well have removed this state identifier already
                        pass
            elif isinstance(argument, Identifier):
                if argument not in self._module.definition.inputs and \
                   argument not in self._current_scope:
                    self._add_errors("ERROR: %(filename)s at line %(lineno)d, unknown function argument %(arg_name)s",
                                     [argument],
                                     lambda a: {'filename' : a.filename,
                                                'lineno' : a.lineno,
                                                'arg_name' : a})

    def __resolve_assignment(self, identifier, assign_object):
        # Check the assigned variable is *not* an input. Inputs are immutable.
        if identifier in self._module.definition.inputs:
            self._add_errors("ERROR: %(filename)s at line %(lineno)d, attempt to write read-only input %(input)s",
                             [assign_object],
                             lambda o: {'filename' : o.filename,
                                        'lineno' : o.lineno,
                                        'input' : identifier})

        # Check the assigned variable is *not* an output.
        if identifier in self._module.definition.outputs:
            self._add_errors("ERROR: %(filename)s at line %(lineno)d, attempt to write output %(output)s outside a return",
                             [assign_object],
                             lambda o: {'filename' : o.filename,
                                        'lineno' : o.lineno,
                                        'output' : identifier})

        # Check if assignment variable has been used already. Code generation may not
        # generate all code to provide the previous use!
        if self._current_scope.in_current_scope(identifier):
            self._add_errors("ERROR: %(filename)s at line %(lineno)d, duplicate assignment variable %(var_name)s",
                             [identifier],
                             lambda i: {'filename' : i.filename,
                                        'lineno' : i.lineno,
                                        'var_name' : i})
        else:
            # Record the assignment and the command
            self._current_scope[identifier] = assign_object

    @multimethod(Command)
    def visit(self, command):
        # Record the current scope in the entity's resolution symbols
        command['scope'] = self._current_scope

        # If no assignment then we don't need to do anything.
        if command.identifier:
            self.__resolve_assignment(command.identifier, command)

    @multimethod(Return)
    def visit(self, ret):
        # Record the current scope in the entity's resolution symbols
        ret['scope'] = self._current_scope

        if ret.value:
            if isinstance(ret.value, StateIdentifier):
                self._add_errors("ERROR: %(filename)s at line %(lineno)d, unknown configuration in return %(unknown)s",
                                 [ret.value] if ret.value not in self._module.resolution_symbols['configuration'] else [],
                                 lambda v: {'filename' : v.filename,
                                            'lineno' : v.lineno,
                                            'unknown' : str(ret.value)})
            elif isinstance(ret.value, Identifier):
                if ret.value in self._module.definition.outputs:
                    self._add_errors("ERROR: %(filename)s at line %(lineno)d, output signal used in return %(unknown)s",
                                     [ret.value],
                                     lambda v: {'filename' : v.filename,
                                                'lineno' : v.lineno,
                                                'unknown' : str(ret.value)})
                else:
                    self._add_errors("ERROR: %(filename)s at line %(lineno)d, unknown variable in return %(unknown)s",
                                     [ret.value] if ret.value not in self._current_scope else [],
                                     lambda v: {'filename' : v.filename,
                                                'lineno' : v.lineno,
                                                'unknown' : str(ret.value)})
                

        if not ret.mappings:
            return

        # Duplicate 'to' maps
        duplicate_to = dict()
        missing_froms = list()

        # Check the mapping contains all the outputs and that assignments exist
        for mapping in ret.mappings:
            # Duplicate to?
            if mapping.to in duplicate_to:
                duplicate_to[mapping.to] += 1
            else:
                duplicate_to[mapping.to] = 1

            # Does the 'from' exist?
            if mapping.from_ not in self._current_scope and \
               mapping.from_ not in self._module.definition.inputs:
                missing_froms.append(mapping.from_)

        # Record duplicate 'to' maps
        self._add_errors("ERROR: %(filename)s at line %(lineno)d, duplicate output in return %(duplicate)s",
                         [duplicate_to[key] for key in filter(lambda k: duplicate_to[k] > 1, duplicate_to.keys())],
                         lambda t: {'filename' : t.filename,
                                    'lineno' : t.lineno,
                                    'duplicate' : str(t)})

        # Missing 'to' maps
        self._add_errors("ERROR: %(filename)s at line %(lineno)d, defined output is missing in return %(missing)s",
                         frozenset(self._module.definition.outputs) - frozenset(duplicate_to.keys()),
                         lambda t: {'filename' : t.filename,
                                    'lineno' : t.lineno,
                                    'missing' : str(t)})

        # Unknown 'to' maps
        self._add_errors("ERROR: %(filename)s at line %(lineno)d, unknown output in return %(unknown)s",
                         frozenset([mapping.to for mapping in ret.mappings if mapping.to not in self._module.definition.outputs]),
                         lambda m: {'filename' : m.filename,
                                    'lineno' : m.lineno,
                                    'unknown' : m})

        # Missing 'from' maps
        self._add_errors("ERROR: %(filename)s at line %(lineno)d, unknown variable in return %(unknown)s",
                         [mf for mf in missing_froms if not isinstance(mf, Literal)],
                         lambda m: {'filename' : m.filename,
                                    'lineno' : m.lineno,
                                    'unknown' : str(m)})

    @multimethod(IfCommand)
    def visit(self, if_command):
        # Record the current scope in the entity's resolution symbols
        if_command['scope'] = self._current_scope

        # Resolve the assignment if there is one
        if if_command.identifier:
            self.__resolve_assignment(if_command.identifier, if_command)

    @multimethod(IfCommand.ThenBlock)
    def visit(self, then_block):
        then_scope = SymbolTable()
        self._current_scope.add_nested_scope(then_scope)
        self._current_scope = then_scope

    @multimethod(IfCommand.ElseBlock)
    def visit(self, else_block):
        previous_scope = self._current_scope.get_parent()
        else_scope = SymbolTable()
        previous_scope.add_nested_scope(else_scope)
        self._current_scope = else_scope

    @multimethod(IfCommand.EndIf)
    def visit(self, end_if):
        self._current_scope = self._current_scope.get_parent()

    @multimethod(LetCommand)
    def visit(self, let_command):
        # Record the current scope in the entity's resolution symbols
        let_command['scope'] = self._current_scope

        if let_command.identifier:
            self.__resolve_assignment(let_command.identifier, let_command)

    @multimethod(LetCommand.LetBindings)
    def visit(self, let_bindings):
        let_scope = SymbolTable()
        self._current_scope.add_nested_scope(let_scope)
        self._current_scope = let_scope

    @multimethod(LetCommand.LetEnd)
    def visit(self, let_end):
        self._current_scope = self._current_scope.get_parent()
