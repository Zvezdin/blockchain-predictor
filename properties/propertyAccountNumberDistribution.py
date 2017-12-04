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

	def processTick(self, data):
		txs = data['tx']

		res = np.zeros((self.groupCount[0], self.groupCount[1]))

		lastTime = 0

		start = time.time()

		#update our global dictionary of accounts

		if not fakeData:
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

				#if sender not in self.accounts:
				#	self.accounts[sender] = np.zeros(len(self.features))
				#if receiver is not None and receiver not in self.accounts:
				#	self.accounts[receiver] = np.zeros(len(self.features))

				for i, feature in enumerate(self.features):
					if feature == 'balance':
						val = float(tx.value)

						if int(val) != val:
							raise ValueError("Transaction value of tx %s is not castable to integer!" % str(tx))
						val = int(val)

						if receiver is not None:
							self.addAccFeat(receiver, i, val)
							#self.accounts[receiver][i] += val #update the receiver's bal
			
						self.subAccFeat(sender, i, val)

						#bal = self.accounts[sender] #update the sender's bal
						#bal[i] -= val
						#if bal[i] < 0:
						#	bal[i] = 0

					if feature == 'lastSeen':
						if receiver is not None: 
							self.setAccFeat(receiver, i, timestamp)
							#self.accounts[receiver][i] = max(self.accounts[receiver][i], timestamp) #update their last active timestamps
						self.setAccFeat(sender, i, timestamp)
						#self.accounts[sender][i] = max(self.accounts[sender][i], timestamp)
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

		self.createDistribution(res)

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


	#methods that require override

	#logic that is supposed to execute before the distribution process
	#feel free to override
	def beforeDistribution(self):
		pass

	def setAccFeat(self, acc, index, value):
		raise NotImplementedError

	def subAccFeat(self, acc, index, value):
		raise NotImplementedError

	def addAccFeat(self, acc, index, value):
		raise NotImplementedError

	#method that creates the distribution, given the accounts dict and other data. Must be overridden by child.
	def createDistribution(self, res):
		raise NotImplementedError