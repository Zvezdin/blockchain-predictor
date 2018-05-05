import math
import sys, os
sys.path.insert(0, os.path.realpath('./properties'))

from sorted_value_dict import SortedValueDict

from property import Property

class BlockchainState(Property):
	def __init__(self):
		self._init_state()
		self._clear_state()

	def _init_state(self):
		self.recentLengthDays = 3
		self.recentLength = self.recentLengthDays*86400 # 3 days in seconds
		self.topXFraction = 0.0001
		self.topUsedFraction = 0.0001

		self.initialSupply = 72_000_000 * 1000000000000000000 #72M ETH in wei. The ETH created at genesis

		#total ETH in existence
		#we start at genesis and add every reward to the total supply
		self.totalETH = self.initialSupply

		#total amount of times where an account has been the initiator or receiver of an action
		self.totalTimesUsed = 0

		#contract lookup
		self.isContract = {}

		#balance lookup
		self.balances = SortedValueDict()

		#amount of transactions this acc participates in
		self.timesUsed = SortedValueDict()

		#total accs
		self.totalAccountsAmount = 0

		#ordered dict address -> timestamp (date of creation)
		self.dateCreated = SortedValueDict()

		#ordered dict address -> timestamp (date of last activity)
		self.dateActive = SortedValueDict()

		#in order ETHRecentlyExchanged to be calculated, we'll keep a list of the past x hours, each element being
		#the amount of ETH exchanged within that hour. Then our variable will be the sum of that list
		self.ETHRecentlyExchangedList = [0] * self.recentLengthDays


	#clears everything that has to be cleared for every processTick call
	def _clear_state(self):
		#TOP IN BALANCE/USED GLOBAL/LOCAL CONTRACTS/ACCOUNTS LIST/MAP

		#top x% lookup (list & map)
		self.isTopX = {}
		self.topX = []

		#for contracts
		self.isContractTopX = {}
		self.contractTopX = []

		#local top X lookup
		self.isLocalTopX = {}
		self.localTopX = []

		#for contracts
		self.isContractLocalTopX = {}
		self.contractLocalTopX = []
		
		#top x% in usage (list & map)
		self.isTopUsed = {}
		self.topUsed = []

		#for contracts
		self.isContractTopUsed = {}
		self.contractTopUsed = []

		#local top X in usage lookup
		self.isLocalTopUsed = {}
		self.localTopUsed = []

		#for contracts
		self.isContractLocalTopUsed = {}
		self.contractLocalTopUsed = []

		#local structures to achieve local top scores
		self.localBalances = SortedValueDict()
		self.localTotalETH = 0
		self.localTimesUsed = SortedValueDict()
		self.localTotalTimesUsed = 0

		#list of local accounts
		self.isLocalAccount = {}
		self.localAccounts = []

		#list/map of local new accounts/contracts
		self.isAccountNew = {}
		self.newAccounts = []
		self.isContractNew = {}
		self.newContracts = []

		#address -> list of transactions/traces/logs
		self.localTransactionsOf = {}
		self.localTracesOf = {}
		self.localLogsOf = {}

		#address -> amount and list of sent/received in this period
		self.amountSentBy = {}
		self.senders = []
		self.amountReceivedBy = {}
		self.receivers = []


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

		#amount of ETH that has been recently exchanged
		self.ETHRecentlyExchanged = 0

#TODO: Avg bal of just created accs (avg value of first tx to acc?)
#TODO: when working with ETH, also have a USD version of the same property

	def processTick(self, data):
		self._clear_state()

		ethExchanged = 0

		if 'trace' in data:
			for trace in data['trace']:
				sender = trace._3
				receiver = trace.to

				sender = self.noneIfInf(sender)
				receiver = self.noneIfInf(receiver)
				
				value = int(trace.value, 0)
				timestamp = trace.date.value // 10**9 #EPOCH time

				ethExchanged += value

				if trace.type == 'create':
					assert(receiver not in self.isContract)
					self.isContract[receiver] = True
					self.isContractNew[receiver] = True
					self.newContracts.append(receiver)
				elif trace.type == 'reward':
					#rewards can be either block or uncle, each of which is increasing the total supply of Ethereum
					self.totalETH += value
				
				for acc in [sender, receiver]:
					if acc is None:
						continue

					if acc not in self.balances:
						self.totalAccountsAmount += 1
						self.dateCreated[acc] = timestamp
						self.balances[acc] = 0
						self.timesUsed[acc] = 0
						self.isAccountNew[acc] = True
						self.newAccounts.append(acc)
					if acc == sender:
						currBal = self.balances[acc]
						self.balances[acc] = 0 if currBal < value else currBal - value
						#this case is possible because we don't have the genesis transfers
						#TODO: Get the genesis transfers from Etherscan's API or make a web scrape
						self.localTracesOf.setdefault(acc, [])
						self.localTracesOf[acc].append(trace)

						if acc not in self.amountSentBy:
							self.amountSentBy[acc] = 0
							self.senders.append(acc)
						self.amountSentBy[acc] += value

					if acc == receiver:
						self.balances[receiver] += value
				
						if acc not in self.amountReceivedBy:
							self.amountReceivedBy[acc] = 0
							self.receivers.append(acc)
						self.amountReceivedBy[acc] += value
					
					#update active accounts
					if acc not in self.isActiveAccount:
						self.isActiveAccount[acc] = True
						self.activeAccounts.append(acc)

					#update local accounts
					if acc not in self.isLocalAccount:
						self.isLocalAccount[acc] = True
						self.localAccounts.append(acc)

					#update usage info
					self.totalTimesUsed += 1
					self.timesUsed[acc] += 1
					self.localTimesUsed.setdefault(acc, 0)
					self.localTimesUsed[acc] += 1

					assert(self.dateActive.get(acc, 0) <= timestamp)
					self.dateActive[acc] = timestamp
		if 'tx' in data:
			for tx in data['tx']:
				sender = self.noneIfInf(tx._3)

				if sender is not None:
					self.localTransactionsOf.setdefault(sender, [])
					self.localTransactionsOf[sender].append(tx)
		if 'log' in data:
			for log in data['log']:
				adr = self.noneIfInf(log.address)

				if adr is not None:
					self.localLogsOf.setdefault(adr, [])
					self.localLogsOf[adr].append(log)
		self.activeAccountsAmount = len(self.activeAccounts)

		#update statistics about recent accounts
		recentlyCreated = self.getRecentRecords(self.dateCreated, self.recentLength)
		self.isRecentlyCreated = self.listToTrueDict(recentlyCreated)

		self.recentlyActive = self.getRecentRecords(self.dateActive, self.recentLength)
		self.isRecentlyActive = self.listToTrueDict(self.recentlyActive)
	
		#update local balances
		for acc in self.localAccounts:
			val = self.balances[acc]
			self.localBalances[acc] = val
			self.localTotalETH += val
	
		#update global top statistics
		self.topX = self.getTopRecords(self.balances, self.topXFraction, self.totalETH)
		self.isTopX = self.listToTrueDict(self.topX)
		print("Amount of topX: "+len(self.topX))
		
		self.contractTopX = self.getTopRecords(self.balances, self.topXFraction, self.totalETH, restrictorDict=self.isContract)
		self.isContractTopX = self.listToTrueDict(self.contractTopX)

		self.localTopX = self.getTopRecords(self.localBalances, self.topXFraction, self.localTotalETH)
		self.isLocalTopX = self.listToTrueDict(self.localTopX)

		self.contractLocalTopX = self.getTopRecords(self.localBalances, self.topXFraction, self.localTotalETH, restrictorDict=self.isContract)
		self.isContractLocalTopX = self.listToTrueDict(self.contractLocalTopX)

		self.topUsed = self.getTopRecords(self.timesUsed, self.topUsedFraction, self.totalTimesUsed)
		self.isTopUsed = self.listToTrueDict(self.topUsed)

		self.contractTopUsed = self.getTopRecords(self.timesUsed, self.topUsedFraction, self.totalTimesUsed, restrictorDict=self.isContract)
		self.isContractTopUsed = self.listToTrueDict(self.contractTopUsed)

		self.localTopUsed = self.getTopRecords(self.localTimesUsed, self.topUsedFraction, self.localTotalTimesUsed)
		self.isLocalTopUsed = self.listToTrueDict(self.localTopUsed)

		self.contractLocalTopUsed = self.getTopRecords(self.localTimesUsed, self.topUsedFraction, self.localTotalTimesUsed, restrictorDict=self.isContract)
		self.isContractLocalTopUsed = self.listToTrueDict(self.contractLocalTopUsed)

		#updated recent ETH exchanged
		# remove the oldest tick and append the latest one
		self.ETHRecentlyExchangedList.pop()
		self.ETHRecentlyExchangedList.insert(0, ethExchanged)
		self.ETHRecentlyExchanged = sum(self.ETHRecentlyExchangedList)

	def noneIfInf(self, a):
		if isinstance(a, float) and math.isnan(a):
			return None
		return a

	def getRecentRecords(self, dct, interval, currentTime=None):
		target = None
		if currentTime is not None:
			target = currentTime - interval

		res = []
		prevVal = None
		for key in dct:
			val = dct[key]
			if currentTime is None:
				currentTime = val
				target = currentTime - interval

			res.append(key)

			assert(prevVal is None or val <= prevVal)

			prevVal = val
			if val < target:
				break

		return res

	def getTopRecords(self, dct, fraction, total, restrictorDict=None, inverseRestriction=False):
		#we should return all records with values higher than min target
		minTarget = total * fraction

		res = []

		prevVal = None
		for key in dct:
			val = dct[key]

			if val >= minTarget and (restrictorDict is None or restrictorDict.get(key, False) is not inverseRestriction):
				res.append(key)
			else:
				break

			assert(prevVal is None or val <= prevVal)
			prevVal = val

		return res

	def listToTrueDict(self, lst, dct=None):
		if dct is None:
			dct = {}

		for el in lst:
			dct[el] = True
		
		return dct

#singleton
state = BlockchainState()
