from arctic import Arctic
from arctic import TICK_STORE
from arctic import CHUNK_STORE
from arctic.date import DateRange

import pandas as pd
from datetime import timezone, datetime as dt
import time

db = Arctic('localhost')

def init():
	print("Initializing")
	db = Arctic('localhost')

def getLibrary(key):
	try:
		return(db[key])
	except:
		return None

def removeDB(key, dataStore):
	if db[dataStore].has_symbol(key):
		db[dataStore].delete(key) #used for debugging
		print("Removed database")


def initLibrary(key, libType = None):
	if(libType != None):
		db.initialize_library(key, lib_type=libType)
	else:
		db.initialize_library(key)