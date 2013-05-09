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
import logging
import ply.yacc as yacc

from pcl_lexer import PCLLexer
from pcl_parser import PCLParser

logging.basicConfig(
    level = logging.DEBUG,
    filename = "pclc.log",
    filemode = "w",
    format = "%(asctime)s: %(levelname)s: %(filename)s at line %(lineno)d: %(message)s",
    datefmt='%d %b %Y %H:%M:%S'
)
logger = logging.getLogger()

def parse_component(filename):
    lexer = PCLLexer(debug = 1, debuglog = logger)
    parser = PCLParser(lexer, logger, debug = 1, write_tables = 0)
    ast = parser.parseFile(filename)

    return ast

def get_logger():
    global logger
    return logger
