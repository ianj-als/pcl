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
import os

# exists :: String -> Bool
exists = lambda p: os.path.exists(p.__str__())

# join :: String -> String -> String
join = lambda *args: os.path.join(*[str(a) for a in args])

# mkdir :: String -> ()
mkdir = lambda p: os.mkdir(p.__str__())

# makedirs :: String > ()
makedirs = lambda p: os.makedirs(p.__str__())

# basename :: String -> String
basename = lambda s: os.path.basename(s.__str__())

# splitext :: String -> [String]
def splitext(s):
  t = os.path.splitext(s.__str__())
  return [t[0], t[1].split('.')[-1]]
