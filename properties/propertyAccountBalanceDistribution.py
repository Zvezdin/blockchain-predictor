from property import Property

import math

import numpy as np


class PropertyAccountBalanceDistribution(Property):
	def __init__(self):
		super().__init__()
		self.name = "accountBalanceDistribution"
		self.requires = ['tx']
		self.requiresHistoricalData  = True
		self.accounts = {}
		self.balanceCutoff = 100000000000000000 # -> 0.1ETH
		self.maxBalance = 1000000000000000000000000 // self.balanceCutoff #1M ETH
		self.subPropertyCount = 3 #vol to, vol from, tx count

		self.scalingFunction = math.log2

		self.tickCount = int(self.scalingFunction(self.maxBalance))

	def processTick(self, data):
		txs = data['tx']

		res = np.zeros((self.subPropertyCount, self.tickCount))

		#update our global dictionary of balances
		for tx in txs.itertuples():

			val = float(tx.value)

			if int(val) != val:
				raise ValueError("Transaction value of tx %s is not castable to integer!" % str(tx))
			val = int(val)

			sender = tx._3 #the field is named 'from', but it is renamed to its index in the tuple
							#due to it being a python keyword. Beware, this will break if the raw data changes.
			receiver = tx.to

			if receiver not in self.accounts:
				self.accounts[receiver] = val
			else:
				self.accounts[receiver] += val

			#updating the balance that way is problematic. Better use max(dict)
			#self.maxBalance = max(self.accounts[receiver], self.maxBalance)

			if sender in self.accounts:
				self.accounts[sender] -= val

				if self.accounts[sender] < 0:
					self.accounts[sender] = 0
			else:
				self.accounts[sender] = 0

		if self.maxBalance != 0:
			for tx in txs.itertuples():

				val = float(tx.value)
				sender = tx._3
				receiver = tx.to

				fromBal = 0
				if self.accounts[sender] > self.balanceCutoff:
					fromBal = self.scalingFunction(self.accounts[sender] / self.balanceCutoff)
				toBal = 0
				if self.accounts[receiver] > self.balanceCutoff:
					toBal = self.scalingFunction(self.accounts[receiver] / self.balanceCutoff)

				fromI = min(int(fromBal), self.tickCount-1)
				toI = min(int(toBal), self.tickCount-1)


				res[0][toI] += val / self.balanceCutoff #value to in ETH
				res[1][fromI] += val / self.balanceCutoff #value from in ETH
				res[2][fromI] += 1 #tx count

		return res