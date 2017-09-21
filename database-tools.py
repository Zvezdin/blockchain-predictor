from arctic import Arctic
from arctic import TICK_STORE
from arctic import CHUNK_STORE
from arctic.date import DateRange

import pandas as pd
from datetime import timezone, datetime as dt
import time

store = None

def init():
	print("Initializing")
	store = Arctic('localhost')

def getStore(key):
	try:
		return(store[key])
	except:
		return None

def removeDB(key, dataStore):
	if store[dataStore].has_symbol(key):
		store[dataStore].delete(key) #used for debugging
		print("Removed database")


def initLibrary(key, libType = None):
	if(libType != none):
		store.initialize_library(key, lib_type=libType)
	else:
		store.initialize_library(key)