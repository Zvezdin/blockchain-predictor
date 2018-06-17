import math
import sys, os
sys.path.insert(0, os.path.realpath('./properties'))

from time import time as now
from collections import deque

#from sorted_value_dict import SortedValueDict
SortedValueDict=dict #temp debug

from property import Property

class BlockchainState():
	def __init__(self):
		self.requires = ['trace']#, 'tx', 'log']
		self.requiresHistoricalData  = True

		self._init_state()
		self._clear_state()

	def _init_state(self):
		self.recentLengthDays = 3
		self.recentLength = self.recentLengthDays*86400 # 3 days in seconds
		self.topXFraction = 0.000005
		self.topUsedFraction = 0.000005

		self.initialSupply = 72_000_000 * 1000000000000000000 #72M ETH in wei. The ETH created at genesis

		#total ETH in existence
		#we start at genesis and add every reward to the total supply
		self.totalETH = self.initialSupply

		#total amount of times where an account has been the initiator or receiver of an action
		self.totalTimesUsed = 0

		#contract lookup
		self.isContract = {}

		#balance lookup
		self.balances = {}

		#amount of transactions this acc participates in
		self.timesUsed = {}

		#total accs
		self.totalAccountsAmount = 0

		#recently active/created accounts.
		#We push to the front the most recent accounts and pop from the back the older ones
		#self.recentlyActive = deque()
		#self.isRecentlyActive = {}
		self.recentlyCreated = deque()
		self.isRecentlyCreated = {}

		#dicts to hold account timestamps. Used when calculating recently active/created
		self.dateCreated = {}
		#self.dateActive = {}

		#in order ETHRecentlyExchanged to be calculated, we'll keep a list of the past x hours, each element being
		#the amount of ETH exchanged within that hour. Then our variable will be the sum of that list
		self.ETHRecentlyExchangedList = [0] * self.recentLengthDays


	#clears everything that has to be cleared for every processTick call
	def _clear_state(self):
		#TOP IN BALANCE/USED GLOBAL/LOCAL CONTRACTS/ACCOUNTS LIST/MAP


		#IS TOP X FROM THE ACTIVE ACCOUNTS
		#THIS IS THE ONLY WAY

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

		# tx hash -> true/undefined whether this transaction exists
		self.isTransaction = {}

		#block N -> bool
		self.isBlock = {}

		#address -> gas used total in this period
		self.gasUsedBy = {}

		#address -> amount and list of sent/received in this period
		self.amountSentBy = {}
		self.senders = []
		self.amountReceivedBy = {}
		self.receivers = []

		#active accs
		self.localAccountsAmount = 0

		#amount of ETH that has been recently exchanged
		self.ETHRecentlyExchanged = 0

		#time of last block
		self.lastTimestamp = 0

#TODO: Avg bal of just created accs (avg value of first tx to acc?)
#TODO: when working with ETH, also have a USD version of the same property

	def processTick(self, data):
		t = now()
		self._clear_state()
		print("Clear state took %4fs" % (now() - t))

		ethExchanged = 0

		fromI = data['trace'].columns.get_loc('from')+1

		if 'trace' in data:
			t = now()
			for trace in data['trace'].itertuples():
				sender = getattr(trace, '_'+str(fromI))
				receiver = trace.to

				sender = self.noneIfInf(sender)
				receiver = self.noneIfInf(receiver)

				value = int(trace.value, 0)

				gasUsed = self.noneIfInf(trace.gasUsed)
				if gasUsed is not None:
					gasUsed = int(trace.gasUsed, 0)
				timestamp = trace.Index.value // 10**9 #EPOCH time

				ethExchanged += value

				self.isTransaction[trace.transactionHash] = True
				self.isBlock[trace.blockNumber] = True

				if gasUsed is not None:
					self.gasUsedBy[sender] = self.gasUsedBy.get(sender, 0) + gasUsed

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
						self.recentlyCreated.appendleft(acc)
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

					#update local accounts
					if acc not in self.isLocalAccount:
						self.isLocalAccount[acc] = True
						self.localAccounts.append(acc)

					#update usage info
					self.totalTimesUsed += 1
					self.timesUsed[acc] += 1
					self.localTimesUsed.setdefault(acc, 0)
					self.localTimesUsed[acc] += 1

					#update active times
					#lastActive = self.dateActive.get(acc, 0)
					#assert(lastActive <= timestamp)
					#if lastActive < timestamp:
					#	self.dateActive[acc] = timestamp
					#	self.recentlyActive.push_left(acc)

					assert(self.lastTimestamp <= timestamp)
					self.lastTimestamp = timestamp

			print("Replaying traces took %4fs" % (now() - t))

		if 'tx' in data:
			t = now()
			fromITX = data['tx'].columns.get_loc('from')+1
			for tx in data['tx'].itertuples():
				sender = self.noneIfInf(getattr(tx, '_'+str(fromITX)))

				if sender is not None:
					self.localTransactionsOf.setdefault(sender, [])
					self.localTransactionsOf[sender].append(tx)
			print("Iterating TXs took %4fs" % (now() - t))
		if 'log' in data:
			t = now()
			for log in data['log'].itertuples():
				adr = self.noneIfInf(log.address)

				if adr is not None:
					self.localLogsOf.setdefault(adr, [])
					self.localLogsOf[adr].append(log)
			print("Iterating logs took %4fs" % (now() - t))

		t = now()

		self.localAccountsAmount = len(self.localAccounts)
	
		print("Getting recent records took %4fs" % (now() - t))
		t = now()

		#update local balances
		for acc in self.localAccounts:
			val = self.balances[acc]
			self.localBalances[acc] = val
			self.localTotalETH += val

			#update top records
			#TODO: Hold the previous top records and remove the no-longer top records before proceeding
			#maybe by having a sorted dict and remove the last ones or just sort and remove?
			if self.isTop(self.balances[acc], self.topXFraction, self.totalETH):
				if self.isContract.get(acc, False):
					self.isContractTopX[acc] = True
					self.contractTopX.append(acc)
				else:
					self.isTopX[acc] = True
					self.topX.append(acc)
			if self.isTop(self.balances[acc], self.topXFraction, self.localTotalETH):
				if self.isContract.get(acc, False):
					self.isContractLocalTopX[acc] = True
					self.contractLocalTopX.append(acc)
				else:
					self.isLocalTopX[acc] = True
					self.localTopX.append(acc)
			if self.isTop(self.timesUsed[acc], self.topUsedFraction, self.totalTimesUsed):
				if self.isContract.get(acc, False):
					self.isContractTopUsed[acc] = True
					self.contractTopUsed.append(acc)
				else:
					self.isTopUsed[acc] = True
					self.topUsed.append(acc)
			if self.isTop(self.timesUsed[acc], self.topUsedFraction, self.localTotalTimesUsed):
				if self.isContract.get(acc, False):
					self.isContractLocalTopUsed[acc] = True
					self.contractLocalTopUsed.append(acc)
				else:
					self.isLocalTopUsed[acc] = True
					self.localTopUsed.append(acc)

		print("Local balance iteration took %4fs" % (now() - t))

		t = now()

		#update recently created by removing the last part of accounts
		self.recentlyCreated = self.removeOldDequeRecords(self.recentlyCreated, self.lastTimestamp - self.recentLength, self.dateCreated)
		self.isRecentlyCreated = self.listToTrueDict(self.recentlyCreated)

		#updated recent ETH exchanged
		# remove the oldest tick and append the latest one
		self.ETHRecentlyExchangedList.pop()
		self.ETHRecentlyExchangedList.insert(0, ethExchanged)
		self.ETHRecentlyExchanged = sum(self.ETHRecentlyExchangedList)

		self.printDebug()

		print("Debug & recently exchanged took %4fs" % (now() - t))

	def noneIfInf(self, a):
		if isinstance(a, float) and math.isnan(a):
			return None
		return a

	def removeOldDequeRecords(self, dq, minVal, valDict=None):
		#the dq should be ordered largest -> smallest values
		while dq:
			val = dq.pop()
			if valDict is not None:
				valCmp = valDict[val]
			else:
				valCmp = val

			if valCmp >= minVal:
				dq.append(val)
				return dq

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

	def isTop(self, value, fraction, total):
		minTarget = total * fraction

		return value >= minTarget

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

			#assert(prevVal is None or val <= prevVal)
			prevVal = val

		return res

	def listToTrueDict(self, lst, dct=None):
		if dct is None:
			dct = {}

		for el in lst:
			dct[el] = True
		
		return dct

	def printDebug(self):
		print("Amount of topX: %d" % len(self.topX))
		print("Amount of topX contracts: %d" % len(self.contractTopX))
		print("Amount of local topX: %d" % len(self.localTopX))
		print("Amount of local topX contracts: %d" % len(self.contractLocalTopX))
		print("Amount of top used: %d" % len(self.topUsed))
		print("Amount of contract top used: %d" % len(self.contractTopUsed))
		print("Amount of local top used: %d" % len(self.localTopUsed))
		print("Amount of contract local top used: %d" % len(self.contractLocalTopUsed))
		print("ETH recently exchanged: %d" % self.ETHRecentlyExchanged)
		#print("Recently active accounts: %d" % len(self.recentlyActive))
		print("Recently created accounts: %d" % len(self.recentlyCreated))

		if self.localAccountsAmount > 0:
			print("Senders %d, with sent val of first being %d" % (len(self.senders), self.amountSentBy[self.senders[0]]))
			print("Receivers %d, with received val of first being %d" % (len(self.receivers), self.amountReceivedBy[self.receivers[0]]))
			acc = self.localAccounts[0]
			print("Local accounts %d, traces from first account %d, logs %d and TXs %d" % (len(self.localAccounts), len(self.localTracesOf.get(acc, [])), \
			len(self.localLogsOf.get(acc, [])), len(self.localTransactionsOf.get(acc, [])) ))
		print("%d new accounts and %d new contracts" % (len(self.newAccounts), len(self.newContracts)))
		print("%d times locally used and %d total local balance" % (self.localTotalTimesUsed, self.localTotalETH))
		print("%d total accounts, %d total times used and %d total ETH" % (self.totalAccountsAmount, self.totalTimesUsed, self.totalETH))

#singleton
state = BlockchainState()
