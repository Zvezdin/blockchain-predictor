import abc

import math

class Property(abc.ABC):
	"""A processor class with a unified interface on the different data properties and their generation"""

	def __init__(self):
		self.name = ""
		"""ID of the processor"""

		self.provides = None
		"""List of the IDs of any other sub-properties that this may provide"""

		self.requires = []
		"""What kind of data it requires. 'block', 'tx' or 'tick' for example"""

		self.requiresState = False
		""""If this processor will request data from the blockchain_state helper processor"""

		self.flexibleRequires = False
		"""Whether this processor can work with fewer inputs than in his requires list."""

		self.isRelative = False
		"""If the generated properties can be turned relative. True if value is already relative"""

		self.requiresHistoricalData  = False
		"""A flag that shows if the given processor requires all available data for all date intervals to be sent to it. For example, if it does internal storage or calculations and previous processing of ticks has an effect on future processes."""

		self.returnsData = True
		"""Whether this processor returns information or is only a state holder"""

		self.previousTicks = 0
		self.nextTicks = 0
		"""Fields that indicate whether a processor requies any number of ticks prior or after the current one to process a value"""

	@abc.abstractmethod
	def processTick(self, data):
		"""Takes block, transaction and course data for an interval and returns the processor's value"""

	@staticmethod
	def averageOfColumn(df, column):
		index = df.columns.searchsorted(column)

		val = df.values

		avg = 0.0
		for i in range(len(val)):
			avg += float(val[i][index])
		if avg == 0 or len(val) == 0:
			print("Got no real data for column %s from data %s." % (column, df))
		else: avg /= len(val)

		return avg
	
	@staticmethod
	def maxOfColumn(df, column):
		return df.max()[column]

	@staticmethod
	def minOfColumn(df, column):
		return df.min()[column]

	def __str__(self):
		return "Property "+self.name

	def noScaling(self, x):
		return x

	def scaleLog(self, x, base=10):
		if x>=1:
			return math.log(x, base)
		return 0