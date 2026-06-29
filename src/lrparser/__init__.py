"""LRParser - A Python LR(1) shift/reduce parser generator library."""

from .rule import *
from .state import State
from .parser import generate, Parser
