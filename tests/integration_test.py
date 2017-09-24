import pytest

import sys, os
sys.path.insert(0, os.path.realpath('./'))

import database_tools as db
import arcticdb as downloader
import property_generator as properties

def test_connection():
    lib = db.getChunkstore()
    assert lib