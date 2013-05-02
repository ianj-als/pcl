import collections
import glob
import os
import sys

from multimethod import multimethod, multimethodclass
from parser.import_spec import Import
from parser.component import Component
from parser.declaration import Declaration
from parser.expressions import Literal, \
     Identifier, \
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
     IdentifierExpression, \
     LiteralExpression
from parser.mappings import Mapping, \
     TopMapping, \
     BottomMapping, \
     LiteralMapping
from parser.module import Module
from parser.helpers import parse_component
from pypeline.core.types.just import Just
from pypeline.core.types.nothing import Nothing
from resolver_visitor import ResolverVisitor


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


@multimethodclass
class FirstPassResolverVisitor(ResolverVisitor):
    def __init__(self,
                 resolver_factory,
                 pcl_import_path = []):
        ResolverVisitor.__init__(self)
        self.__resolver_factory = resolver_factory
        if pcl_import_path:
            self.__pcl_import_paths = pcl_import_path.split(";")
        else:
            self.__pcl_import_paths = ["."]
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
                tuple(unused_config),
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
            self._module.resolution_symbols = {'imports' : dict(),
                                               'components' : dict(),
                                               'configuration' : dict()}

    @multimethod(Import)
    def visit(self, an_import):
        # Hu rah, we're about to import something. Very exciting
        import_symbol_dict = an_import.module.resolution_symbols['imports']
        # Add, only uniquely aliased, Python modules to symbol table
        if import_symbol_dict.has_key(an_import.alias):
            self._errors.append("ERROR: %s at line %d, duplicate import alias found %s" % \
                                (an_import.filename, an_import.lineno, an_import.alias))
        else:
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
                self._errors.append("ERROR: %s at line %d, error importing module %s: %s" % \
                                    (an_import.filename,
                                     an_import.lineno,
                                     an_import.module_name,
                                     str(ie)))

            # Was the module imported?
            if imported_module:
                # Yes!
                try:
                    get_inputs_fn = getattr(imported_module, 'get_inputs')
                except AttributeError:
                    get_inputs_fn = lambda _: []
                    self._errors.append("ERROR: %s at line %d, imported Python module %s " \
                                        "does not define get_inputs function" % \
                                        (an_import.filename, an_import.lineno,
                                         an_import.module_name))
                try:
                    get_outputs_fn = getattr(imported_module, 'get_outputs')
                except AttributeError:
                    get_outputs_fn = lambda _: []
                    self._errors.append("ERROR: %s at line %d, imported Python module %s " \
                                        "does not define get_outputs function" % \
                                        (an_import.filename, an_import.lineno,
                                         an_import.module_name))
                try:
                    get_configuration_fn = getattr(imported_module, 'get_configuration')
                except AttributeError:
                    get_configuration_fn = lambda _: []
                    self._errors.append("ERROR: %s at line %d, imported Python module %s " \
                                        "does not define get_configuration function" % \
                                        (an_import.filename, an_import.lineno,
                                         an_import.module_name))
                try:
                    configure_fn = getattr(imported_module, 'configure')
                except AttributeError:
                    configure_fn = lambda _: None
                    self._errors.append("ERROR: %s at line %d, imported Python module %s " \
                                        "does not define configure function" % \
                                        (an_import.filename, an_import.lineno,
                                         an_import.module_name))
                try:
                    initialise_fn = getattr(imported_module, 'initialise')
                except AttributeError:
                    initialise_fn = lambda _: (lambda a, s: dict())
                    self._errors.append("ERROR: %s at line %d, imported Python module %s " \
                                        "does not define initialise function" % \
                                        (an_import.filename, an_import.lineno,
                                         an_import.module_name))

                # Record stuff from the imported Python module
                module_spec.update({'module' : imported_module,
                                    'get_inputs_fn' : get_inputs_fn,
                                    'get_outputs_fn' : get_outputs_fn,
                                    'get_configuration_fn' : get_configuration_fn,
                                    'configure_fn' : configure_fn,
                                    'initialise_fn' : initialise_fn})

            # Always add the module alias as a key to the import dictionary
            import_symbol_dict[an_import.alias] = module_spec

    @multimethod(Component)
    def visit(self, component):
        # Component name *must* be the same as te file name

        # Add the inputs, outputs, configuration and declaration identifiers to
        # the module's symbol table
        duplicate_inputs = FirstPassResolverVisitor.__check_scalar_or_tuple_collection(component.inputs)
        duplicate_outputs = FirstPassResolverVisitor.__check_scalar_or_tuple_collection(component.outputs)
        duplicate_config = self.__add_identifiers_to_symbol_table(component.configuration, 'configuration')
        duplicate_decl_identifiers = self.__add_identifiers_to_symbol_table(component.declarations, 'components')

        # Check that all the used configuration in declarations exist, and is used
        missing_configuration, \
        unused_configuration, \
        unknown_imports, \
        duplicate_declarations, \
        unknown_module_configuration, \
        python_module_interace = FirstPassResolverVisitor.__check_declarations(component.configuration,
                                                                               component.declarations,
                                                                               component.module.resolution_symbols['imports'])
        if duplicate_inputs or \
           duplicate_outputs or \
           duplicate_config or \
           duplicate_decl_identifiers or \
           missing_configuration or \
           unused_configuration or \
           unknown_imports or \
           duplicate_declarations or \
           unknown_module_configuration or \
           python_module_interace:
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
            self._add_warnings("WARNING: %(filename)s at line %(lineno)d, component " \
                               "configuration is not used %(entity)s",
                               unused_configuration,
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
        pass

    @multimethod(object)
    def visit(self, nowt):
        pass

    @multimethod(UnaryExpression)
    def visit(self, unary_expr):
        # Unary expressions have the same inputs and outputs as thier expression
        unary_expr.resolution_symbols['inputs'] = unary_expr.expression.resolution_symbols['inputs']
        unary_expr.resolution_symbols['outputs'] = unary_expr.expression.resolution_symbols['outputs']

    @multimethod(CompositionExpression)
    def visit(self, comp_expr):
        # The inputs and outputs for this composed component
        comp_expr.resolution_symbols['inputs'] = comp_expr.left.resolution_symbols['inputs']
        comp_expr.resolution_symbols['outputs'] = comp_expr.right.resolution_symbols['outputs']

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

    @multimethod(ParallelWithScalarExpression)
    def visit(self, para_scalar_expr):
        # Inputs are all the union of the top and bottom component inputs
        top_inputs = para_scalar_expr.left.resolution_symbols['inputs']
        bottom_inputs = para_scalar_expr.right.resolution_symbol['inputs']
        inputs = top_inputs >= \
                 (lambda tins: bottom_inputs >= \
                  (lambda bins: Just(set([i for i in tins.union(bins)]))))

        # Outputs of component is the top and bottom components' outputs
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

        all_to_identifiers = [m.to for m in all_out_mappings]
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

        merge_expr.resolution_symbols['inputs'] = Just((set(top_from_identifiers), set(bottom_from_identifiers)))
        merge_expr.resolution_symbols['outputs'] = Just(set(all_to_identifiers))

    @multimethod(WireExpression)
    @resolve_expression_once
    def visit(self, wire_expr):
        inputs = [m.from_ for m in wire_expr.mapping]
        outputs = [m.to for m in wire_expr.mapping]

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

        wire_expr.resolution_symbols['inputs'] = Just(set(inputs))
        wire_expr.resolution_symbols['outputs'] = Just(set(outputs))

    @multimethod(WireTupleExpression)
    @resolve_expression_once
    def visit(self, wire_tuple_expr):
        top_inputs = [m.from_ for m in wire_tuple_expr.top_mapping]
        top_outputs = [m.to for m in wire_tuple_expr.top_mapping]
        bottom_inputs = [m.from_ for m in wire_tuple_expr.bottom_mapping]
        bottom_outputs = [m.to for m in wire_tuple_expr.bottom_mapping]

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

        wire_tuple_expr.resolution_symbols['inputs'] = Just((set(top_inputs), set(bottom_inputs)))
        wire_tuple_expr.resolution_symbols['outputs'] = Just((set(top_outputs), set(bottom_outputs)))

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
            self._errors.append("ERROR: %s at line %d, unknown component %s" % \
                                (iden_expr.filename,
                                 iden_expr.lineno,
                                 iden_expr))

        module_alias = declaration.component_alias
        module_spec = imports_sym_table[module_alias]

        root = Just(0) if module_spec.has_key('module') else Nothing()
        iden_expr.resolution_symbols['inputs'] = root >= (lambda _: Just(set([Identifier(None, 0, i) \
                                                                              for i in module_spec['get_inputs_fn']()])))
        iden_expr.resolution_symbols['outputs'] = root >= (lambda _: Just(set([Identifier(None, 0, i) \
                                                                               for i in module_spec['get_outputs_fn']()])))

    @multimethod(LiteralExpression)
    def visit(self, literal_expr):
        pass
