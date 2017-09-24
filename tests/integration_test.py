import pytest

import sys, os
sys.path.insert(0, os.path.realpath('./'))

from database_tools import *
from arcticdb import *
from property_generator import *

def test_connection():
    lib = getChunkstore()
    assert lib