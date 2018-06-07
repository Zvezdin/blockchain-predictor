import sys
sys.path.append("..") #TODO: Temporary workaround

from .db import Database
import pandas as pd

from arctic import Arctic
from arctic import CHUNK_STORE
from arctic.date import DateRange, CLOSED_CLOSED, CLOSED_OPEN, OPEN_CLOSED, OPEN_OPEN

from tools.encode_decode import encodeDataFrame, decodeDataframe

#constants for config
masterKey=""
maxDBStorage = 1024 #1024 GB max size of the database

chunkSizes = {
	'tick': 'M',
	'tx': 'D',
	'block': 'W',
	'log': 'D',
	'trace': 'D',
}

class ArcticStoreDatabase(Database):
	def __init__(self):
		super().__init__()
		self.db = None
		self.store = None

	def open(self, store='chunkstore'):
		self.db = Arctic('localhost')
		try:
			self.store = self.db[store]
		except:
			self.db.initialize_library(store, lib_type=CHUNK_STORE)
			self.store = self.db[store]
			self.store._arctic_lib.set_quota(maxDBStorage * 1024 * 1024 * 1024)

	def close(self):
		pass #no need to close arctic connection

	def remove(self, key):
		self.store.delete(key) #used for debugging
		
	def getMeatdata(self, key):
		return self.store.read_metadata(key)

	def setMetadata(self, key, metadata):
		self.store.write_metadata(key, metadata)

	def _save(self, key, data):
		if self.has_key(key):
			self.store.append(key, data)
		else:
			self.store.write(key, data, chunk_size=chunkSizes.get(key, 'M'))
	
	def get(self, key, start=None, end=None, iterator=False):
		if not iterator:
			return self.store.read(key, chunk_range=DateRange(start, end, CLOSED_CLOSED))
		else:
			return self.store.iterator(key, chunk_range=DateRange(start, end, CLOSED_CLOSED))

	def getLatestRow(self, key):
		latestDate = self.store.read_metadata(key)['end']
		return self.get(key, start=latestDate, end=None)

	def getFirstRow(self, key):
		firstDate = self.store.read_metadata(key)['start']
		return self.get(key, start=None, end=firstDate)

	def has_key(self, key):
		return self.store.has_symbol(key)

	def list_keys(self):
		return self.store.list_symbols()
