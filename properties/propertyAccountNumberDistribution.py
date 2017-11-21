from property import Property

import pickle
import codecs

import numpy as np


class PropertyAccountNumberDistribution(Property):
	def __init__(self):
		super().__init__()
		self.name = "accountNumberDistribution"
		self.requires = ['tx']
		self.requiresHistoricalData = True
		self.accounts = {}
		self.groupCount = [10, 10] 
		self.features = ['balance', 'lastSeen']
		self.max = [None, None]
		self.scaling = [self.noScaling, self.noScaling] #or self.scaleLog

		self.actualMax = [None, None]

	def processTick(self, data):
		txs = data['tx']

		res = np.zeros((self.groupCount[0], self.groupCount[1]))

		lastTime = 0

		#update our global dictionary of accounts
		for tx in txs.itertuples():

			try:
				sender = int(tx._2, 16) #the field is named 'from', but it is renamed to its index in the tuple
								#due to it being a python keyword. Beware, this will break if the raw data changes.
				receiver = int(tx.to, 16)
			except TypeError:
				print("Sender and receiver are:", tx._2, tx.to, type(tx._2), type(tx.to))
				raise
			print("Sender and receiver are %d and %d." % (sender, receiver))

			time = tx.date.value // 10**9 #EPOCH time

			lastTime = max(lastTime, time)

			if sender not in self.accounts:
				self.accounts[sender] = np.zeros(len(self.features))
			if receiver not in self.accounts:
				self.accounts[receiver] = np.zeros(len(self.features))

			for i, feature in enumerate(self.features):
				if feature == 'balance':
					val = float(tx.value)

					if int(val) != val:
						raise ValueError("Transaction value of tx %s is not castable to integer!" % str(tx))
					val = int(val)

					self.accounts[receiver][i] += val #update the receiver's bal

					bal = self.accounts[sender] #update the sender's bal
					bal[i] -= val
					if bal[i] < 0:
						bal[i] = 0

				if feature == 'lastSeen':
					self.accounts[receiver][i] = max(self.accounts[receiver][i], time) #update their last active timestamps
					self.accounts[sender][i] = max(self.accounts[sender][i], time)

		#TODO: separate distributions of only senders and receivers?

		for i, maxVal in enumerate(self.max):
			if maxVal is None: #if no max has been given, calculate it
				self.actualMax[i] = self.getMax(i)
			else: #get the given max
				self.actualMax[i] = maxVal

		#we have updated our accounts, let's create the double distribution.
		#by assigning two group numbers to each one of them

		for acc in self.accounts: #this iteration is the slowest part of the process
			res[self.getGroup1(acc, 0)][self.getGroup2(acc, 1)] += 1 #add that account to the correct distribution location

		serialized = codecs.encode(pickle.dumps(res, -1), "base64").decode()

		return serialized

def getGroup1(self, acc, index):
	return min(int((self.scaling[index](self.accounts[acc][index] + self.offset[index]) / self.scaling[index](self.actualMax[index])) * self.groupCount[index]), self.groupCount[index]-1)

def getGroup2(self, acc, index):
	return self.getGroup1(acc, index)

def getMax(self, index):
	return max(self.accounts.values(), key=lambda x: x[index])[index]

def getMin(self, index):
	return min(self.accounts.values(), key=lambda x: x[index])[index]
