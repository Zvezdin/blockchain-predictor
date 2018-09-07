from .db import Database
import pandas as pd

from util.encode_decode import encodeDataFrame, decodeDataframe

minSizes = {
	'trace': {'from': 42, 'to': 42, 'subtype': 12, 'transactionHash': 66, 'value': 40, 'type': 10, 'gas': 10, 'gasUsed': 10}, #TODO: same with 'value'
	#for value, the holdings of the largest account (~1.5% of total eth) * 100 = 0x340aad21b3b70000. This is len 22
	'tx': {'from': 42, 'to': 42, 'hash': 66, 'value': 40, 'gasPrice': 25}, #TODO: potential issue with 'value' and 'gasPrice' overflowing as min length!!!
	'log': {'address': 42, 'hash': 66, 'topic0': 66, 'topic1': 66, 'topic2': 66, 'topic3': 66, 'type': 10}, #TODO: Same for 'type' field!
	'block': {'miner': 42, 'difficulty': 20, 'totalDifficulty': 25}, #TODO: Same for 'difficulty' and 'totalDifficulty'.
}

class HDFSStoreDatabase(Database):
	def __init__(self):
		super().__init__()
		self.store = None

	#TODO: Have this filepath in a config file somewhere
	def open(self, store='/storage/programming/db_h5/db.h5'):
		self.store = pd.HDFStore(store)

	def close(self):
		self.store.close()

	def remove(self, key):
		self.store.remove(key)

	def getMeatdata(self, key):
		return self.store.get_storer(key).attrs.metadata

	def setMetadata(self, key, metadata):
		self.store.get_storer(key).attrs.metadata = metadata

	def _save(self, key, data):
		data = encodeDataFrame(data)

		if not self.has_key(key) and key in minSizes:
			self.store.append(key, data, min_itemsize=minSizes[key])
		else:
			self.store.append(key, data)

	def get(self, key, start=None, end=None, iterator=False):
		if start is not None:
 			start = "index >= '"+str(start)+"'"
		if end is not None:
			end = "index <= '"+str(end)+"'"
		query = start + (" and " + (end if end is not None else "")) if start is not None else "" + end if end is not None else ""
		if query == "":
			query = None

		print(query)

		res = self.store.select(key, where=query, iterator=iterator, chunksize=(None if not iterator else 10000))
		if iterator:
			res = iter(res)
			#TODO: Handle the case where we need to decode this iterator
		else:
			res = decodeDataframe(res)

		return res

	def getLatestRow(self, key):
		nrows = self.store.get_storer(key).nrows
		return self.store.select(key, start=nrows-1, end=nrows)

	def getFirstRow(self, key):
		return self.store.select(key, start=0, stop=1)

	def has_key(self, key):
		return key in self.store

	def list_keys(self):
		return [key.replace('/', '') for key in self.store.keys()]
