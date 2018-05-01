import sys, os
sys.path.insert(0, os.path.realpath('./properties'))

from property import Property

class BlockchainState(Property):
	def __init__(self):
		pass

	#balance lookup
	#top x% lookup (list & map)
	#local top x% lookup
	#address -> list of transactions/traces/logs
	#address -> amount sent/received in this period
	#active accs
	#total accs
	#ordered dict address -> timestamp (date of creation)
	#accounts active in last x days lookup

	#local top x% contracts in amount of times used (map & list)
	#address -> bool if this address is created within last x ticks
	#list/map of active accounts/contracts
	#list/map of local rich accounts/contracts
	#list/map of local new accounts/contracts
	#list/map of local receiving/sending money accounts/contracts
	#isContract method
	#total ETH in existence

	def processTick(self, data):
		pass

#singleton
state = BlockchainState()
