import abc
import time
from datetime import datetime as dt

import pandas as pd

class Database(abc.ABC):
	def __init__(self):
		self.timeseries = ['block', 'tick', 'tx', 'log', 'trace'] #the stored keys of our time raw data time series

	@abc.abstractmethod
	def open(self, store):
		pass

	@abc.abstractmethod
	def close(self):
		pass

	@abc.abstractmethod
	def remove(self, key):
		pass

	@abc.abstractmethod
	def getFirstRow(self, key):
		pass

	@abc.abstractmethod
	def get(self, key, start=None, end=None, iterator=False):
		pass

	@abc.abstractmethod
	def getMeatdata(self, key):
		pass

	@abc.abstractmethod
	def setMetadata(self, key, metadata):
		pass

	@abc.abstractmethod
	def _save(self, key, data, **kwargs):
		pass

	@abc.abstractmethod
	def getLatestRow(self, key):
		pass

	@abc.abstractmethod
	def has_key(self, key):
		pass

	@abc.abstractmethod
	def list_keys(self):
		pass

	###METHODS WITH DEFAULT IMPLEMENTATIONS

	def save(self, key, data):
		if not isinstance(data, pd.DataFrame):
			raise ValueError("Given data to save is not a dataframe!")

		assert(isinstance(data.index[0], dt))

		start = time.time()
		#if we have started writing this data before
		if self.has_key(key):
			trimIndex = 0

			#read the last saved timestamp
			try:
				newestDate = self.getMeatdata(key)['end']
			except:
				newestDate = 0
			print("newest date is ")
			print(newestDate)

			#find out where to trim the data so we don't write the same items, in case of an overlap
			while trimIndex < len(data) and newestDate >= data.index[trimIndex] :
				trimIndex+=1

			#if there is nothing new to write
			if(len(data) == trimIndex): print("Data already written!")
			else:
				#update the metadata and save the trimmed data
				metadata = self.getMeatdata(key)
				print("Got metadata", metadata)
				
				assert(metadata['end'] == newestDate)

				metadata['end'] = data.index[-1]
				
				self._save(key, data[trimIndex:])
				self.setMetadata(key, metadata)
		else:
			self._save(key, data)
			self.setMetadata(key, {'start': data.index[0], 'end': data.index[-1]})
		print("Saving the data took "+str(time.time() - start)+" seconds")

	def getMasterInterval(self, keys, start=None, end=None):
		"""Checks the min/max dates for each key and returns the overlap. If start and end are given, returns the overlap with them as well."""
		startAll = max([self.getMeatdata(key)['start'] for key in keys])

		endAll = min([self.getMeatdata(key)['end'] for key in keys])

		if start:
			start = max(start, startAll) #make sure we don't go out of bounds
		else:
			start = startAll

		if end:
			end = min(end, endAll)
		else: end = endAll

		return (start, end)
