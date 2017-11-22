from propertyAccountNumberDistribution import PropertyAccountNumberDistribution


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

	#override the default groups
	#use the default logic for the balance group
	
	def getGroup1(self, acc): #custom logic for the last seen group
		#offset by the last timestamp, denoting the amount of seconds since last activity
		return self.getGroupByVal(abs(self.accounts[acc][1] - self.lastTimestamp), 1)


	#the rest of the logic is inherited from the base class