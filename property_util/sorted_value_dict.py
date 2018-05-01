from blist import sorteddict

class SortedValueDict(sorteddict):
	"""A quick but memory-inefficient implementation of a dict that is iterable by sorted values.
	Uses a key-sorted dict as a backend and overrides its compare method to the value behind that key."""
	def __dctcmp(self, key):
		return self.dct[key]
	
	def __init__(self, increasing=False):
		self.dct = {}
		self.increasing = increasing
		super().__init__(self.__dctcmp)

	def __setitem__(self, key, val):
		self.dct[key] = val if self.increasing else -val
		super().__setitem__(key, val)
