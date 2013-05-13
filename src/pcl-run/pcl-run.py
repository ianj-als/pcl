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
import sys

from concurrent.futures import ThreadPoolExecutor
from pypeline.core.arrows.kleisli_arrow import KleisliArrow
from pypeline.helpers.parallel_helpers import eval_pipeline, cons_function_component


def get_configuration(section, config_key):
    try:
        value = config_parser.get(section, config_key)
    except ConfigParser.NoOptionError as ex:
        print "ERROR: Configuration file %s: %s" % (config_filename, ex)
        sys.exit(1)
    except ConfigParser.NoSectionError:
        print "ERROR: Configuration file %s is missing the '%s' section" % \
              (config_filename, section)
        sys.exit(1)

    try:
        value = int(value)
    except ValueError:
        try:
            value = float(value)
        except ValueError:
            pass

    return value


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print "Usage:"
        print "\t%s [PCL configuration filename]" % os.path.basename(sys.argv[0])
        print
        sys.exit(2)

    # Add the PCL extension is one is missing
    basename = os.path.basename(sys.argv[1])
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
        print "ERROR: Failed to import PCL module %s: %s" % (pcl_module, ex)
        sys.exit(1)

    # Get the pipeline
    try:
        get_inputs_fn = getattr(pcl, "get_inputs")
        get_configuration_fn = getattr(pcl, "get_configuration")
        configure_fn = getattr(pcl, "configure")
        initialise_fn = getattr(pcl, "initialise")
    except AttributeError as ex:
        print "ERROR: PCL module %s does not have required functions: %s" % \
              (pcl_module, ex)
        sys.exit(1)

    # Inputs, configuration types
    inputs = get_inputs_fn()
    configurations = get_configuration_fn()

    # Read the configuration from the configuration file
    configuration = dict()
    for config_key in configurations:
        configuration[config_key] = get_configuration('Configuration', config_key)

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
            input_dict[an_input] = get_configuration('Inputs', an_input)
        return input_dict

    if isinstance(inputs, tuple):
        pipeline_inputs = list()
        for set_inputs in inputs:
            pipeline_inputs.append(build_inputs_fn(set_inputs))
    else:
        pipeline_inputs = build_inputs_fn(inputs)

    executor = ThreadPoolExecutor(max_workers = 3)
    print >> sys.stderr, "Evaluating pipeline..."
    try:
        print eval_pipeline(executor, pipeline, tuple(pipeline_inputs), list())
    finally:
        executor.shutdown(True)
