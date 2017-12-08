from propertyAccountNumberDistribution import PropertyAccountNumberDistribution

import math
import sys
#because python is stupid, this path is not relative to this script, but to the execution start point.
sys.path.insert(0, 'c++/build') #include our C++ implementation

import numpy as np

import cppBalanceLastSeen

class PropertyBalanceLastSeenDistribution(PropertyAccountNumberDistribution):
	"""
	An implementation of the PropertyAccountNumberDistribution, that distributes accounts based on:
	1- Balance
	2- Time since last transaction
	"""
	def __init__(self):
		super().__init__()
		self.name = "balanceLastSeenDistribution_log2"

		self.features = ['balance', 'lastSeen']
		self.max = [0, 0] #our real maximum values are in the C++ backend
		self.balanceCutoff = 100000000000000000 # -> 0.1ETH
		self.balanceCache = {}

		self.useCache = False #group caching to speed up distributions. This is moved to the C++ side

		super().updateConfig()

	def setAccFeat(self, acc, index, value):
		if index == 1: #lastSeen feature
			cppBalanceLastSeen.setInt(acc, index, value, False, False, False)
		else: #TODO this is an impossible case, but still implement it
			raise NotImplementedError

	def subAccFeat(self, acc, index, value):
		if index == 0:
			bal = self.balanceCache.get(acc, 0)
			bal -= value
			if bal < 0:
				bal = 0
			self.balanceCache[acc] = bal

			cppBalanceLastSeen.setInt(acc, index, bal // self.balanceCutoff, False, False, False) #convert to ETH and pass to C++
		else: #TODO this is an impossible case, but still implement it
			raise NotImplementedError

	def addAccFeat(self, acc, index, value):
		if index == 0:
			bal = self.balanceCache.get(acc, 0)
			bal += value
			self.balanceCache[acc] = bal

			cppBalanceLastSeen.setInt(acc, index, bal // self.balanceCutoff, False, False, False) #convert to ETH and pass to C++
		else: #TODO this is an impossible case, but still implement it
			raise NotImplementedError

	def createDistribution(self):
		return np.array(cppBalanceLastSeen.createDistribution(self.lastTimestamp)) #use C++ backend

	#the rest of the logic is inherited from the base class
