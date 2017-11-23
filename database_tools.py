import sys
from datetime import timezone, datetime as dt
import time
import argparse
import pickle
import codecs

import pandas as pd
from arctic import Arctic
from arctic import TICK_STORE
from arctic import CHUNK_STORE
from arctic.date import DateRange, CLOSED_CLOSED, CLOSED_OPEN, OPEN_CLOSED, OPEN_OPEN

masterKey="_all_logs"

dbKeys = {'tick': '', 'tx': '', 'block': '', 'logs': ''}

blockChunkSize = 'W'
txChunkSize = 'D'
receiptChunkSize = 'D'
courseChunkSize = 'M'
logsChunkSize = 'D'

storeKey = 'chunkstore'

db = None

maxDBStorage = 1024 #1024 GB max size of the database

def updateKeys(masterKey):
	for key in dbKeys:
		dbKeys[key] = key+masterKey

#Methods for db management

def init():
	global db
	db = Arctic('localhost')
	updateKeys(masterKey)

def getChunkstore():
	chunkStore = getLibrary(storeKey)
	if(chunkStore == None):
		initLibrary(storeKey, CHUNK_STORE)
		chunkStore = getLibrary(storeKey)
		#turn GB to bytes and set the max quota of storage. Arctic's default is 10GB
		chunkStore._arctic_lib.set_quota(maxDBStorage * 1024 * 1024 * 1024)
	return chunkStore

def getLibrary(lib):
	try:
		return(db[lib])
	except:
		return None

def removeDB(lib, key):
	if lib.has_symbol(key):
		lib.delete(key) #used for debugging
		print("Removed key "+key+" in database")


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

def loadData(lib, key, startDate, endDate, filter, interval = CLOSED_CLOSED):
	return lib.read(key, chunk_range = DateRange(startDate, endDate, interval), filter_data = filter)

def loadMetadata(lib, key):
	return lib.read_metadata(key)

def getMasterInterval(lib, keys, start=None, end=None):
	"""Checks the min/max dates for each key and returns the overlap. If start and end are given, returns the overlap with them as well."""
	startAll = max([loadMetadata(lib, key)['start'] for key in keys])

	endAll = min([loadMetadata(lib, key)['end'] for key in keys])

	if start: start = max(start, startAll) #make sure we don't go out of bounds
	else: start = startAll

	if end:
		end = min(end, endAll)
	else: end = endAll

	return (start, end)
#reads all data in memory. Eats all the ram.

def encodeObject(obj):
	return codecs.encode(pickle.dumps(obj, -1), "base64").decode()

def decodeObject(encoded):
	return pickle.loads(codecs.decode(encoded.encode(), "base64"))

def readAllData(lib, key):
	start = time.time()
	try:
		df = lib.read(key)
	except:
		print("Error:", sys.exc_info()[0])
		return
	print("Loading took "+str(time.time() - start)+"s")
	start = time.time()
	print("The data is", df)

	values = df.values

	print(values[4])
	print("Getting the values took "+str(time.time() - start)+"s")
	print("The metadata is", loadMetadata(lib, key))

#Pandas config for debug display
pd.set_option("display.max_columns",999)
pd.set_option('expand_frame_repr', False)

#Init the module
init()

if __name__ == "__main__": #if this is the main file, parse the command args
	parser = argparse.ArgumentParser(description="Module that manages database storage and retrieval.")
	parser.add_argument('--key', type=str, help='The database symbol.')
	parser.add_argument('--list', dest='list', action="store_true", help="Print the available symbols in the database.")
	parser.add_argument('--peek', dest='peek', action="store_true", help="Print the first and last rows of a symbol.")
	parser.add_argument('--read', dest='read', action="store_true", help="Load and print the whole symbol.")
	parser.add_argument('--remove', dest='remove', action="store_true", help="Remove a certain symbol from the database.")
	parser.add_argument('--removeBlockchain', dest='removeBlockchain', action="store_true", help="Remove all downloaded raw blockchain data.")
	parser.set_defaults(list=False)
	parser.set_defaults(peek=False)
	parser.set_defaults(read=False)
	parser.set_defaults(remove=False)
	parser.set_defaults(removeBlockchain=False)


	args, _ = parser.parse_known_args()

	if args.removeBlockchain:
			for key in dbKeys:
				removeDB(getChunkstore(), dbKeys[key])

	elif args.key == None or args.list:
		print("Available symbols: ", getChunkstore().list_symbols())
	else:
		if args.peek:
			try:
				peekData(getChunkstore(), args.key)
			except:
				print("There was an error while peeking. Did you enter the correct key?")
		if args.read:
			try:
				readAllData(getChunkstore(), args.key)
			except:
				print("There was an error while reading. Did you enter the correct key?")
		if args.remove:
			try:
				removeDB(getChunkstore(), args.key)
			except:
				print("There was an error while removing. Did you enter the correct key?")