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
import sys

# callAndCheck :: * -> File -> File -> File
def callAndCheck(program,
                 stdin_stream = sys.stdin,
                 stdout_stream = sys.stdout,
                 stderr_stream = sys.stderr):
    is_shell = False
    if hasattr(program, "__iter__"):
        cmd_line = [str(c) for c in program]
    else:
        cmd_line = str(program)
        is_shell = True

    subprocess.check_call(cmd_line,
                          stdin = stdin_stream,
                          stdout = stdout_stream,
                          stderr = stderr_stream,
                          shell = is_shell)
