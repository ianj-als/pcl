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

# cons :: []
cons = lambda *args: [a for a in args] if args else list()

# concat :: [*] -> [*] -> [*]
concat = lambda l, m: l + m

# append :: [a] -> a -> a
append = lambda l, x: l.append(x) or x

# length :: [*] -> Int
length = lambda l: len(l)

# insert :: [a] -> Int -> a
insert = lambda l, i, x: l.insert(int(i), x) or x

# head :: [a] -> a
head = lambda l: l[0]

# tail :: [a] -> [a]
tail = lambda l: l[1:]

# last :: [a] -> a
last = lambda l: l[-1]

# init :: [a] -> [a]
init = lambda l: l[0:-1]

# reverse :: [a] -> [a]
reverse = lambda l: l[::-1]

# take :: [a] -> Int -> [a]
take = lambda l, t: l[:t]

# drop :: [a] -> Int -> [a]
drop = lambda l, d: l[d:]

# elem :: [a] -> a -> Boolean
elem = lambda l, e: e in l

# index :: [a] -> Int -> a
index = lambda l, i: l[i]
