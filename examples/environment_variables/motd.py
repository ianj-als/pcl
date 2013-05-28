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

def get_name():
  return 'motd'

def get_inputs():
  return ['string']

def get_outputs():
  return ['string']

def get_configuration():
  return ['message']

def configure(args):
  return {'motd' : args['message']}

def initialise(config):
  def echo_fn(a, s):
    print >> sys.stdout, "%s: %s" % (config['motd'], a['string'])
    return {'string' : a['string']}

  return echo_fn

