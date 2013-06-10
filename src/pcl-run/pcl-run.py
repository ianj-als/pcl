#!/usr/bin/env python
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
import ConfigParser
import os
import re
import sys

from concurrent.futures import ThreadPoolExecutor
from optparse import OptionParser
from pypeline.core.arrows.kleisli_arrow import KleisliArrow
from pypeline.helpers.parallel_helpers import eval_pipeline, cons_function_component


__VERSION = "1.1.2"


def replace_environment_variables(value):
    pattern = re.compile("\$\((?P<VAR_NAME>\w+)\)")
    m = pattern.search(value)
    while m is not None:
        environ_var = m.group('VAR_NAME')
        try:
            environ_value = os.environ[environ_var]
        except KeyError:
            raise Exception("Environment variable %s is not set" % environ_var)
        value = value[:m.start()] + environ_value + value[m.end():]
        m = pattern.search(value)

    return value


def get_key_from_section(config_parser, section, config_key, replace_environ_vars = True):
    try:
        value = config_parser.getboolean(section, config_key)
    except ValueError:
        try:
            value = config_parser.getint(section, config_key)
        except ValueError:
            try:
                value = config_parser.getfloat(section, config_key)
            except ValueError:
                value = config_parser.get(section, config_key)
                if replace_environ_vars:
                    value = replace_environment_variables(value)
    except ConfigParser.NoOptionError as ex:
        raise Exception("Configuration file %s: %s" % (config_filename, ex))
    except ConfigParser.NoSectionError:
        raise Exception("Configuration file %s is missing the '%s' section" % \
                        (config_filename, section))

    return value


get_configuration = lambda c, k: get_key_from_section(c, 'Configuration', k)
get_input = lambda c, k: get_key_from_section(c, 'Inputs', k, False)


if __name__ == '__main__':
    # The option parser
    parser = OptionParser("Usage: %prog [options] [PCL configuration]")
    parser.add_option("-v",
                      "--version",
                      action = "store_true",
                      default = False,
                      dest = "version",
                      help = "show version and exit")
    parser.add_option("-n",
                      "--noworkers",
                      type = "int",
                      default = 5,
                      dest = "no_workers",
                      help = "number of pipeline evaluation workers [default: %default]")
    (options, args) = parser.parse_args()

    # Show version?
    if options.version is True:
        print >> sys.stdout, __VERSION
        sys.exit(0)

    if len(args) < 1:
        print >> sys.stderr, "ERROR: no configuration file specified"
        sys.exit(2)

    # Add the PCL extension is one is missing
    basename = os.path.basename(args[0])
    basename_bits = basename.split(".")
    if len(basename_bits) == 1:
        # Add the CFG extension on
        basename_bits.append("cfg")

    # PCL import path
    pcl_import_path = os.getenv("PCL_IMPORT_PATH", ".")
    sys.path.extend(pcl_import_path.split(":"))

    # Import the compiled pipeline component.
    # The compiled PCL and configuration file should
    # be next to each other.
    config_filename = ".".join(basename_bits)
    pcl_module = ".".join(basename_bits[0].split(os.path.sep))

    # Open configuration file
    config_parser = ConfigParser.ConfigParser()
    config_parser.read(config_filename)

    # Import PCL
    try:
        pcl = __import__(pcl_module, fromlist = ['get_inputs',
                                                 'get_configuration',
                                                 'configure',
                                                 'initialise'])
    except Exception as ex:
        print >> sys.stderr, "ERROR: Failed to import PCL module %s: %s" % (pcl_module, ex)
        sys.exit(1)

    # Get the pipeline
    try:
        get_inputs_fn = getattr(pcl, "get_inputs")
        get_configuration_fn = getattr(pcl, "get_configuration")
        configure_fn = getattr(pcl, "configure")
        initialise_fn = getattr(pcl, "initialise")
    except AttributeError as ex:
        print >> sys.stderr, "ERROR: PCL module %s does not have required functions: %s" % (pcl_module, ex)
        sys.exit(1)

    # Inputs, configuration types
    inputs = get_inputs_fn()
    configurations = get_configuration_fn()

    # Read the configuration from the configuration file
    configuration = dict()
    configuration_errors = list()
    for config_key in configurations:
        try:
            configuration[config_key] = get_configuration(config_parser, config_key)
        except Exception as ex:
            configuration_errors.append(str(ex))

    # Any configuration errors
    if configuration_errors:
        for configuration_error in configuration_errors:
            print >> sys.stderr, "ERROR: %s" % configuration_error
        sys.exit(1)

    # Configure the PCL...
    filtered_config = configure_fn(configuration)
    # ...and initialise
    pipeline = initialise_fn(filtered_config)
    if not isinstance(pipeline, KleisliArrow):
        pipeline = cons_function_component(pipeline)

    # Create inputs
    def build_inputs_fn(inputs):
        input_dict = dict()
        for an_input in inputs:
            input_dict[an_input] = get_input(config_parser, an_input)
        return input_dict

    if isinstance(inputs, tuple):
        pipeline_inputs = list()
        for set_inputs in inputs:
            pipeline_inputs.append(build_inputs_fn(set_inputs))
        pipeline_inputs = tuple(pipeline_inputs)
    else:
        pipeline_inputs = build_inputs_fn(inputs)

    executor = ThreadPoolExecutor(max_workers = options.no_workers)
    try:
        print >> sys.stdout, eval_pipeline(executor, pipeline, pipeline_inputs, configuration)
    finally:
        executor.shutdown(True)
