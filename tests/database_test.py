import pytest

import sys, os
sys.path.insert(0, os.path.realpath('./'))

import database_tools as db

def test_connection():
    lib = db.getChunkstore()
    assert lib