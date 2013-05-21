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
from pypeline.helpers.parallel_helpers import cons_function_component, cons_if_component


def get_name():
  return 'reverse'

def get_inputs():
  return ['string']

def get_outputs():
  return ['gnirts']

def get_configuration():
  return ['upper_case']

def configure(args):
  return dict()

def initialise(config):
  reverse_comp = cons_function_component(lambda a, s: {'gnirts' : a['string'][::-1]})
  if_comp = cons_if_component(lambda a, s: True if s['upper_case'] else False,
                              cons_function_component(lambda a, s: {'gnirts' : a['gnirts'].upper()}),
                              cons_function_component(lambda a, s: a))

  return reverse_comp >> if_comp
