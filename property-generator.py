from arctic import Arctic
from arctic import TICK_STORE
from arctic import CHUNK_STORE
from arctic.date import DateRange

import pandas as pd
from datetime import timezone, datetime as dt
import time

import pickle
import json

import sys
import os
from Naked.toolshed.shell import execute_js, muterun_js

from database_tools import *

from propertyGasPrice import *
from property import *

chunkStore = getChunkstore()

def generateProperties():
	gas = PropertyGasPrice()

	block, tx, course = loadDataForTick(chunkStore, dt(2017,7,9,23,52,47), dt(2017, 7, 10))

	val = gas.processTick(block, tx, course)

	print("Got value", val)

def loadDataForTick(lib, start, end):
	return loadData(lib, blKey, start, end, True), loadData(lib, txKey, start, end, True), loadData(lib, tickKey, start, end, True)

def printHelp():
	print("Script that uses downloaded blockchain and course data to generate and save data properties.")
	print("Arguments:")
	print("remove : removes the database entries of generated properties.")


for i, arg in enumerate(sys.argv):
	if arg.find('help') >= 0 or len(sys.argv) == 1: printHelp()
	elif arg == 'remove':
		removeDB(propKey, storeKey)
	elif arg == 'generate':
		generateProperties()