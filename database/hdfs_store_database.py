from database import Database
import pandas as pd

class HDFSStoreDatabase(Database):
	def __init__(self):
		super().__init__()
		self.store = None

	def open(self, store='test'):
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

		return self.store.select(key, where=query, iterator=iterator)

	def getLatestRow(self, key):
		nrows = self.store.get_storer(key).nrows
		return self.store.select(key, start=nrows-1, end=nrows)

	def getFirstRow(self, key):
		return self.store.select(key, start=0, stop=1)

	def has_key(self, key):
		return key in self.store

	def list_keys(self):
		return [key.replace('/', '') for key in self.store.keys()]
