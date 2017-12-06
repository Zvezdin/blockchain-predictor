from property import Property

import pickle
import codecs
import time #for debug timing
import math

import numpy as np

fakeData = False

class PropertyAccountNumberDistribution(Property):
	def __init__(self):
		super().__init__()
		self.name = "accountNumberDistribution"
		self.requires = ['tx']
		self.requiresHistoricalData = True
		self.accounts = {} #dict, holding an array of feature values for each account
		self.groupCount = [10, 10] 
		self.features = ['balance', 'lastSeen']
		self.max = [None, None]
		self.scaling = [self.noScaling, self.noScaling] #or self.scaleLog
		self.lastTimestamp = 0 #will be updated

		self.contractData = False #to load contract data or not
		self.ignoreTx = False #if we do not require usage of Tx data, we can ignore it for better performance

		self.actualMax = [None, None]

		self.useCache = False #we can cache the groups of each account that hasn't changed since last time to speed up performance
		#keep in mind that caching shouldn't be used when the max values are dynamic,
		#which denotes that groups can change, even if the account is not active.

		self.groupCache = {}

		if fakeData: #we can generate fake accounts with fake data for debug purposes
			for i in range(10_000_000): #random accounts with random feature values
				self.setAccFeat(str(0x8d12A197cB00D4947a1fe02325095ce2A5CC6819 + i), 0, \
				1_000_000 * 1000000000000000000)

				self.setAccFeat(str(0x8d12A197cB00D4947a1fe02325095ce2A5CC6819 + i), 1, \
				1_000_000 * 1000000000000000000)

	def updateConfig(self):
		if self.contractData:
			if 'logs' not in self.requires:
				self.requires.append('logs')
			self.contracts = {}

		if self.ignoreTx and 'tx' in self.requires:
			self.requires.remove('tx')

	def processTick(self, data):
		txs = data['tx']

		lastTime = 0

		if self.contractData:
			logs = data['logs']
			for log in logs.itertuples():
				contract = log.address
				new = False
				if contract not in self.contracts:
					self.contracts[contract] = True
					new = True

				timestamp = log.date.value // 10**9 #EPOCH time

				for i, feature in enumerate(self.features):
					if feature == 'erc20':
						if log.topic0 == '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef': #Signature ERC20 Transfer
							self.addAccFeat(contract, i, 1) #add one to the total counter of that contract
					if feature == 'contractLastSeen':
						self.setAccFeat(contract, i, timestamp)
					if feature == 'contractAge' and new:
						self.setAccFeat(contract, i, timestamp)
					#TODO: bal, avg tx val, vol of txs, avg acc bal.

		start = time.time()

		#replay the transactions to update our state

		if not fakeData:
			inVolume = {}
			outVolume = {}
			avgValue = {}
			numTxs = {}

			for tx in txs.itertuples():
				try:
					sender = tx._3 #the field is named 'from', but it is renamed to its index in the tuple
								#due to it being a python keyword. Beware, this will break if the raw data changes.
				except AttributeError:
					print(tx) #debug info to change the attribute
					raise

				receiver = tx.to

				if type(receiver) == float and math.isnan(receiver):
					receiver = None #receiver is None when the TX is contract publishing

				if self.useCache:
					self.groupCache[sender] = None #clear the cache for this person, as their feature values will change
					if receiver is not None:
						self.groupCache[receiver] = None

				timestamp = tx.date.value // 10**9 #EPOCH time

				self.lastTimestamp = max(self.lastTimestamp, timestamp)

				for i, feature in enumerate(self.features):
					val = float(tx.value)

					if int(val) != val:
						raise ValueError("Transaction value of tx %s is not castable to integer!" % str(tx))
					val = int(val)

					if feature == 'balance':
						if receiver is not None:
							self.addAccFeat(receiver, i, val)				
						self.subAccFeat(sender, i, val)

					if feature == 'contractBalance': #track the balance of contracts
						if sender in self.contracts:
							self.subAccFeat(sender, i, val)
						if receiver in self.contracts:
							self.addAccFeat(receiver, i, val)

					if feature == 'contractInVolume':
						if receiver in self.contracts:
							inVolume.setdefault(receiver, 0)
							inVolume[receiver] = inVolume[receiver] + val

					if feature == 'contractOutVolume':
						if sender in self.contracts:
							print("Outgoing transaction from %s with value %d and TX hash" % (sender, val, tx.hash))
							outVolume.setdefault(sender, 0)
							outVolume[sender] += val

					if feature == 'contractTx' or feature == 'contractAvgValue': #avgTxValue needs the amount of transactions
						if receiver in self.contracts:
							numTx.setdefault(receiver, 0)
							numTx[receiver] += 1
						#TODO: What about outgoing transactions?
					if feature == 'contractAvgValue':
						if receiver in self.contracs:
							avgVal.setdefault(receiver, 0)
							avgVal[receiver] += val
						#TODO: Outgoing?
					if feature == 'lastSeen':
						if receiver is not None: 
							self.setAccFeat(receiver, i, timestamp)
						self.setAccFeat(sender, i, timestamp)
			if 'contractTx' in self.features:
				for contract in numTx:
					#method of keeping only the sum of the values for previous x time ticks:
					#self.subAccFeat ... 
					#self.addAccFeat(contract, self.features.index('contractTx'), numTx[contract])
					self.setAccFeat(contract, self.features.index('contractTx'), numTx[contract])
			if 'contractAvgValue' in self.features:
				for contract in avgValue:
					self.setAccFeat(contract, self.features.index('contractAvgValue'), avgValue[contract] / numTx[contract])
			if 'contractInVolume' in self.features:
				for contract in inVolume:
					self.setAccFeat(contract, self.features.index('contractInVolume'), inVolume[contract])
			if 'contractOutVolume' in self.features:
				for contract in outVolume:
					self.setAccFeat(contract, self.features.index('contractOutVolume'), outVolume[contract])
		else:
			print("Running group assignments with fake data.")

		txReplayTime = time.time() - start

		start = time.time()

		for i, maxVal in enumerate(self.max):
			if maxVal is None: #if no max has been given, calculate it
				self.actualMax[i] = self.getMax(i)
			else:
				self.actualMax[i] = maxVal

		self.beforeDistribution() #here we can place logic that is supposed to execute before the distribution process

		#we have updated our accounts, let's create the double distribution.
		#by assigning two group numbers to each one of them

		res = self.createDistribution()

		groupTime = time.time() - start

		print("TX replay %3f, grouping %3f" % (txReplayTime, groupTime))

		return res

	#methods with default implementations that don't require override

	def getGroupByVal(self, val, index): #our default grouping
		return min(int((self.scaling[index](val) / self.scaling[index](self.actualMax[index])) * self.groupCount[index]), self.groupCount[index]-1)

	def getGroup0(self, acc): #wrappers for our default grouping. Feel free to override if needed
		return self.getGroupByVal(self.accounts[acc][0], 0)

	def getGroup1(self, acc):
		return self.getGroupByVal(self.accounts[acc][1], 1)

	def getMax(self, index):
		return max(self.accounts.values(), key=lambda x: x[index])[index]

	def getMin(self, index):
		return min(self.accounts.values(), key=lambda x: x[index])[index]


	#logic that is supposed to execute before the distribution process
	#feel free to override
	def beforeDistribution(self):
		pass

	#methods that require override

	#modifiers of account features that set a new value, or subtract or add to the current one.
	def setAccFeat(self, acc, index, value):
		raise NotImplementedError

	def subAccFeat(self, acc, index, value):
		raise NotImplementedError

	def addAccFeat(self, acc, index, value):
		raise NotImplementedError

	#method that creates the distribution, given the accounts dict and other data. Must be overridden by child.
	def createDistribution(self):
		raise NotImplementedError
