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

storeKey = 'chunkstore'
propKey = 'prop'



chunkStore = getStore(storeKey)
if(chunkStore == None):
	print("Unable to load database store! Make sure that the data has been downloaded and saved.")



def printHelp():
    print("Script that uses downloaded blockchain and course data to generate and save data properties.")
    print("Arguments:")
    print("remove : removes the database entries of generated properties.")


for i, arg in enumerate(sys.argv):
	if arg.find('help') >= 0 or len(sys.argv) == 1: printHelp()
	elif arg == 'remove':
		removeDB(propKey, storeKey)