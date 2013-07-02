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
import sys

from pypeline.core.arrows.kleisli_arrow import KleisliArrow
from pypeline.helpers.parallel_helpers import eval_pipeline, cons_function_component


class PCLImportError(Exception):
    def __init__(self, cause):
        self.__cause = cause

    def __str__(self):
        return self.__cause.__str__()

    def __repr__(self):
        return "PCLImportError(cause = %s)" % self.__cause.__repr__()


def execute_module(executor, pcl_import_path, pcl_module, get_configuration_fn, get_inputs_fn):
    """Executes a PCL component in a concurrent environment. Provide a the concurrent execution environment, a colon separated PCL import path, the fully qualified PCL module name, and getter two functions. The configuration function receives the expected configuration keys and should return a dictionary, whose keys are the expected configuration, with appropriate values. The input function received the expected inputs and should return a dictionary, whose keys are the expected inputs, with appropriate values."""
    # Set up Python path to import compiled PCL modules
    pcl_import_path_bits = pcl_import_path.split(":")
    for pcl_import_path_bit in pcl_import_path_bits:
        if pcl_import_path_bit not in sys.path:
            sys.path.append(pcl_import_path_bit)

    # Import PCL
    try:
        pcl = __import__(pcl_module, fromlist = ['get_inputs',
                                                 'get_outputs',
                                                 'get_configuration',
                                                 'configure',
                                                 'initialise'])
    except Exception as ex:
        raise PCLImportError(ex)

    # Get the pipeline
    get_expected_inputs_fn = getattr(pcl, "get_inputs")
    get_expected_outputs_fn = getattr(pcl, "get_outputs")
    get_expected_configuration_fn = getattr(pcl, "get_configuration")
    configure_fn = getattr(pcl, "configure")
    initialise_fn = getattr(pcl, "initialise")

    # Inputs, configuration values from the provided functions
    pipeline_inputs = get_inputs_fn(get_expected_inputs_fn())
    pipeline_configuration = get_configuration_fn(get_expected_configuration_fn())

    # The expected outputs from the component
    expected_outputs = get_expected_outputs_fn()

    # Configure the PCL...
    filtered_config = configure_fn(pipeline_configuration)
    # ...and initialise
    pipeline = initialise_fn(filtered_config)
    if not isinstance(pipeline, KleisliArrow):
        pipeline = cons_function_component(pipeline)

    return (expected_outputs,
            eval_pipeline(executor, pipeline, pipeline_inputs, pipeline_configuration))
    
