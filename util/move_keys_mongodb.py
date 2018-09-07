import argparse

from arctic import Arctic
from arctic import TICK_STORE
from arctic import CHUNK_STORE
from arctic.date import DateRange, CLOSED_CLOSED, CLOSED_OPEN, OPEN_CLOSED, OPEN_OPEN

storeKey = 'chunkstore'
maxDBStorage = 1024 #1024 GB max size of the database

def getChunkstore(db):
	chunkStore = getLibrary(storeKey, db)
	if(chunkStore == None):
		initLibrary(storeKey, db, CHUNK_STORE)
		chunkStore = getLibrary(storeKey, db)
		#turn GB to bytes and set the max quota of storage. Arctic's default is 10GB
		chunkStore._arctic_lib.set_quota(maxDBStorage * 1024 * 1024 * 1024)
	return chunkStore

def initLibrary(key, db, libType = None):
	if(libType != None):
		db.initialize_library(key, lib_type=libType)
	else:
		db.initialize_library(key)

def getLibrary(lib, db):
	try:
		return(db[lib])
	except:
		return None

if __name__ == "__main__": #if this is the main file, parse the command args
	parser = argparse.ArgumentParser(description="Module that moves differnet key writes from one mongodb to another.")
	parser.add_argument('address1', type=str, help='The address of the first mongodb.')
	parser.add_argument('address2', type=str, help='The address of the first mongodb.')
	parser.add_argument('properties', type=str, help='List of comma-separated database keys to move to the second.')
	parser.add_argument('--cut', dest='cut', action="store_true", help="If the original writes should be removed from the first database.")
	parser.set_defaults(cut=False)
	
	args, _ = parser.parse_known_args()

	db1 = Arctic(args.address1)
	db2 = Arctic(args.address2)

	ch1 = getChunkstore(db1)
	ch2 = getChunkstore(db2)

	props = args.properties.split(',')
	symbols = ch1.list_symbols()

	for prop in props:
		if prop not in symbols:
			raise ValueError("Given property %s is not in the symbols of the first database!")
	
	for prop in props:
		data = ch1.read(prop)
		metadata = ch1.read_metadata(prop)

		info = ch1.get_info(prop)

		ch2.write(prop, data, metadata, chunk_size=info['chunk_size'])

		assert(info == ch2.get_info(prop))

		print("Successfully moved %s into the second database!" % prop)

		if args.cut:
			#TODO
			pass