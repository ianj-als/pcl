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

# cons :: String -> String
cons = lambda s = '': str(s)

# split :: String -> String -> [String]
split = lambda s, ss: str(s).split(ss)

# join :: [String] -> String -> String
join = lambda l, s: s.join([str(e) for e in l])

# lower :: String -> String
lower = lambda s: str(s).lower()

# upper :: String -> String
upper = lambda s: str(s).upper()

# length :: String -> Int
length = lambda s: len(str(s))

# append :: String -> String - String
append = lambda s, append_s: str(s) + str(append_s)
