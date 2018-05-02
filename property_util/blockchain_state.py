import sys, os
sys.path.insert(0, os.path.realpath('./properties'))

from sorted_value_dict import SortedValueDict

from property import Property

class BlockchainState(Property):
	def __init__(self):
		self._init_state()
		self._clear_state()

	def _init_state(self):
		#contract lookup
		self.isContract = {}
		
		#balance lookup
		self.balances = SortedValueDict()

		#total accs
		self.totalAccountsAmount = 0

		#ordered dict address -> timestamp (date of creation)
		self.dateCreated = SortedValueDict()


		#in order ETHRecentlyExchanged to be calculated, we'll keep a list of the past x hours, each element being
		#the amount of ETH exchanged within that hour. Then our variable will be the sum of that list
		self.ETHRecentlyExchangedList = []


	#clears everything that has to be cleared for every processTick call
	def _clear_state(self):
		#top x% lookup (list & map)
		self.isTopX = {}
		self.topX = []

		#local top X lookup
		self.isLocalTopX = {}
		self.localTopX = []

		#local top x% contracts in amount of times used (map & list)
		self.isContractLocalTopUsed = {}
		self.contractLocalTopUsed = []

		#list/map of local rich accounts/contracts
		self.isLocalContractRich = {}
		self.richLocalContracts = []

		#list/map of local new accounts/contracts
		self.isAccountNew = {}
		self.newAccounts = []
		self.isContractNew = {}
		self.newContracts = []

		#address -> list of transactions/traces/logs
		self.localTransactionsOf = {}
		self.localTracesOf = {}
		self.localLogsOf = {}

		#address -> amount sent/received in this period
		self.amountSentBy = {}
		self.amountReceivedBy = {}

		#list/map of local receiving/sending money accounts/contracts
		self.isReceivingMoney = {}
		self.receivers = []
		self.isSendingMoney = {}
		self.senders = []
		self.isContractReceivingMoney = {}
		self.contractReceivers = []
		self.isSendingMoney = {}
		self.contractSender = []

		#accounts active in last x days lookup
		self.recentlyActive = []
		self.isRecentlyActive = {}
		
		#address -> bool if this address is created within last x ticks
		self.isRecentlyCreated = {}

		#active accs
		self.activeAccountsAmount = 0

		#list/map of active accounts/contracts
		self.activeAccounts = []
		self.isActiveAccount = {}
		self.activeContracts = []
		self.isActiveContract = {}

		#not sure how to approach this
		#maybe call sum(self.balances.values()) from time to time
		#and in the meantime add block rewards to the sum?
		self.totalETH = 0
		#amount of ETH that has been recently exchanged
		self.ETHRecentlyExchanged = 0

	def processTick(self, data):
		pass

#singleton
state = BlockchainState()
