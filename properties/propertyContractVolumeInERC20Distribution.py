from propertyAccountNumberDistribution import PropertyAccountNumberDistribution

import math
import sys
#because python is stupid, this path is not relative to this script, but to the execution start point.
sys.path.insert(0, 'c++/build') #include our C++ implementation

import numpy as np

import cppContractVolumeInERC20 as cpp

class PropertyContractVolumeInERC20Distribution(PropertyAccountNumberDistribution):
	"""
	An implementation of the PropertyContractAccountNumberDistribution, that distributes contract accounts based on:
	1- Volume of funds transferred to that contract within a past time frame
	2- Number of ERC20 transfers within a past time frame
	"""
	def __init__(self):
		super().__init__()
		self.name = "contractVolumeInERC20Distribution_log2_v2_stateless"

		self.contractData = True

		self.features = ['contractInVolume', 'erc20']
		self.max = [0, 0] #our real maximum values are in the C++ backend
		self.balanceCutoff = 100000000000000000 # -> 0.1ETH

		self.useCache = False #group caching to speed up distributions. This is moved to the C++ side

		super().updateConfig()

	def setAccFeat(self, acc, index, value):
		if index == 0:
			value = value // self.balanceCutoff
		cpp.setInt(acc, index, value, False, False, False)

	def subAccFeat(self, acc, index, value):
		if index == 0:
			cpp.setInt(acc, index, value // self.balanceCutoff, False, True, False) #convert to ETH and pass to C++
		else: #TODO this is an impossible case, but still implement it
			raise NotImplementedError

	def addAccFeat(self, acc, index, value):
		if index == 0:
			cpp.setInt(acc, index, value // self.balanceCutoff, True, False, False) #convert to ETH and pass to C++
		elif index == 1:
			cpp.setInt(acc, index, value, True, False, False)
		else: #our indices should only be 0 or 2
			raise NotImplementedError

	def createDistribution(self):
		res = np.array(cpp.createDistribution(self.lastTimestamp)) #use C++ backend
		print("Number of contracts is %d." % (cpp.len()))
		cpp.clear() #clear the state
		return res

	#the rest of the logic is inherited from the base class
