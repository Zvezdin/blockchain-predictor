import abc

class Database(abc.ABC):
	def __init__(self):
		pass

	@abc.abstractmethod
	def open(self):
		pass

	@abc.abstractmethod
	def close(self):
		pass

	@abc.abstractmethod
	def remove(self, key):
		pass

	@abc.abstractmethod
	def save(self, key, data, **kwargs):
		pass

	@abc.abstractmethod
	def getLatestRow(self, key):
		pass

	@abc.abstractmethod
	def getFirstRow(self, key):
		pass

	@abc.abstractmethod
	def loadData(self, key, start=None, end=None):
		pass

	@abc.abstractmethod
	def getMeatdata(self, key):
		pass

	@abc.abstractmethod
	def getMasterInterval(self, keys, start=None, end=None):
		"""Gets the maximum interval that overlaps between the intervals of the given list of keys and also with an optional given interval."""
		pass

	@abc.abstractmethod
	def iterator(self, key):
		pass