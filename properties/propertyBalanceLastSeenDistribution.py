from propertyAccountNumberDistribution import PropertyAccountNumberDistribution

import math

class PropertyBalanceLastSeenDistribution(PropertyAccountNumberDistribution):
	"""
	An implementation of the PropertyAccountNumberDistribution, that distributes accounts based on:
	1- Balance
	2- Time since last transaction
	"""
	def __init__(self):
		super().__init__()
		self.name = "balanceLastSeenDistribution"

		self.groupCount = [10, 10]
		self.features = ['balance', 'lastSeen']
		self.max = [1_000_000 * 1000000000000000000, 2592000] #1M ETH in wei, 30 days in seconds
		self.scaling = [self.scaleLog, self.scaleLog] #or self.noScaling

		self.useCache = True #we will use group caching to speed up distributions

	#override the default groups
	#use the default logic for the balance group
	
	def getGroup1(self, acc): #custom logic for the last seen group
		#offset by the last timestamp, denoting the amount of seconds since last activity
		return self.getGroupByVal(abs(self.accounts[acc][1] - self.lastTimestamp), 1)

	def createDistribution(self, res):
		max1 = math.log(self.max[0], 10)
		max2 = math.log(self.max[1], 10)
		for acc, val in self.accounts.items():
			if self.groupCache[acc] == None:
				try:
					group0 = min(int((math.log(val[0], 10) / max1) * 10), 9) #excuse the constants - with them as variables, the execution will take much longer
				except ValueError: #in case of log(0)
					group0 = 0
				self.groupCache[acc] = group0 #for this case, we can only cache group0, as group1 depends on time
			else:
				group0 = self.groupCache[acc]

			try:
				group1 = min(int((math.log(abs(val[1] - self.lastTimestamp), 10) / max2) * 10), 9)
			except ValueError:
				group1 = 0

			res[group0][group1] += 1 #add that account to the correct distribution location
	#the rest of the logic is inherited from the base class