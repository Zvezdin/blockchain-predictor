from arctic import Arctic
from arctic import TICK_STORE
from arctic import CHUNK_STORE
from arctic.date import DateRange

import pandas as pd
from datetime import timezone, datetime as dt
import time

tickKey = 'test2'
txKey = 'tx'
blKey = 'block'
propKey = 'prop'

blockChunkSize = 'W'
txChunkSize = 'D'
courseChunkSize = 'M'

storeKey = 'chunkstore'

db = None

#Methods for db management

def init():
	global db
	db = Arctic('localhost')

def getChunkstore():
	chunkStore = getLibrary(storeKey)
	if(chunkStore == None):
		initLibrary(storeKey, CHUNK_STORE)
		chunkStore = getLibrary(storeKey)
	return chunkStore

def getLibrary(lib):
	try:
		return(db[lib])
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

#Methods for saving

def saveData(lib, key, data, chunkSize):
	start = time.time()

	#if we have started writing this data before
	if lib.has_symbol(key):
		trimIndex = 0

		#read the last saved timestamp
		try:
			newestDate = lib.read_metadata(key)['end']
		except:
			newestDate = 0
		print("newest date is ")
		print(newestDate)

		#find out where to trim the data so we don't write the same items, in case of an overlap
		while trimIndex < len(data) and newestDate >= data[trimIndex]['date'] :
			trimIndex+=1

		#if there is nothing new to write
		if(len(data) == trimIndex): print("Data already written!")
		else:
			#update the metadata and save the trimmed data
			metadata = lib.read_metadata(key)
			print("Got metadata", metadata)
			
			metadata['end'] = data[len(data)-1]['date']
			
			lib.append(key, getDataFrame(data[trimIndex:]), metadata)
			lib.write_metadata(key, metadata)
	else:
		#create the store of this new data
		df = getDataFrame(data)
		lib.write(key, df, {'start': data[0]['date'], 'end': data[len(data)-1]['date'] }, chunk_size=chunkSize)
	print("Saving the data took "+str(time.time() - start)+" seconds")

def getDataFrame(data):
	return pd.DataFrame(data)

#Methods for reading

#Prints the start and end of the data
def peekData(lib, key, n = 5 ):
	start = time.time()

	try:
		#df = chunkStore.read(key)
		head = getLatestRow(lib, key, False)
		tail = getFirstRow(lib, key, False)
	except:
		print("Error:", sys.exc_info()[0])
		return
	print(tail.head(n))
	print('...')
	print(head.tail(n))
	print(len(head.values), len(tail.values))
	print("Displaying the data took "+str(time.time() - start)+" seconds")

def getLatestRow(lib, key, filter = True):
	latestDate = lib.read_metadata(key)['end']
	return loadData(lib, key, latestDate, None, filter)

def getFirstRow(lib, key, filter = True):
	firstDate = lib.read_metadata(key)['start']
	return loadData(lib, key, None, firstDate, filter)

def loadData(lib, key, startDate, endDate, filter):
	return lib.read(key, chunk_range = DateRange(startDate, endDate), filter_data = filter)

def loadMetadata(lib, key):
	return lib.read_metadata(key)

#reads all data in memory. Eats all the ram.
def readAllData(lib, key):
	start = time.time()
	try:
		df = lib.read(key)
	except:
		print("Error:", sys.exc_info()[0])
		return
	print("Loading took "+str(time.time() - start)+"s")
	start = time.time()
	print("Reading the fifth row")

	values = df.values

	print(values[4])
	print("Getting the values took "+str(time.time() - start)+"s")

#Init the module
init()