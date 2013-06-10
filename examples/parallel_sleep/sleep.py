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
import subprocess

def get_name():
  return "sleep"

def get_inputs():
  return ['sleep_time']

def get_outputs():
  return ['complete']

def get_configuration():
  return ['sleep_command']

def configure(args):
  return {'sleep_command' : args['sleep_command']}

def initialise(config):
  def sleep_function(a, s):
    proc = subprocess.Popen([config['sleep_command'], str(a['sleep_time'])])
    proc.communicate()
    return {'complete' : True}

  return sleep_function

