import logging

from pcl_lexer import PCLLexer
from pcl_parser import PCLParser

logging.basicConfig(
    level = logging.DEBUG,
    filename = "pcl.log",
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
