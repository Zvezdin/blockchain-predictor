from property import Property

import math
import pickle
import io

import numpy as np


class PropertyAccountDistribution(Property):
	def __init__(self):
		super().__init__()
		self.name = "accountDistribution"
		self.requires = ['tx']
		self.requiresHistoricalData  = True
		self.accounts = {}
		self.tickCount = 10
		self.maxBalance = 0
		self.subPropertyCount = 3 #vol to, vol from, tx count

		self.scalingFunction = self.scaleLog #or self.noScaling

	def processTick(self, data):
		txs = data['tx']

		res = np.zeros((self.subPropertyCount, self.tickCount))

		#update our global dictionary of balances
		for tx in txs.itertuples():

			val = float(tx.value)

			if int(val) != val:
				raise ValueError("Transaction value of tx %s is not castable to integer!" % str(tx))
			val = int(val)

			sender = tx._2 #the field is named 'from', but it is renamed to its index in the tuple
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

			if sender == '0x35da6AbcB08F2b6164fE380BB6c47BD8F2304d55'.lower() or receiver == '0x35da6AbcB08F2b6164fE380BB6c47BD8F2304d55'.lower():
				print("DEBUG:")
				print("Transaction with test account", tx)
				print("Current balance is %d." % self.accounts['0x35da6AbcB08F2b6164fE380BB6c47BD8F2304d55'.lower()])

		#update the max balance
		self.maxBalance = self.scalingFunction(max(self.accounts.values()))

		if self.maxBalance != 0:
			for tx in txs.itertuples():

				val = float(tx.value)
				sender = tx._2
				receiver = tx.to
				fromBal = self.scalingFunction(self.accounts[sender])
				toBal = self.scalingFunction(self.accounts[receiver])

				fromI = min(int((fromBal / self.maxBalance) * self.tickCount), self.tickCount-1)
				toI = min(int((toBal / self.maxBalance) * self.tickCount), self.tickCount-1)


				res[0][toI] += val #value to
				res[1][fromI] += val#value from
				res[2][fromI] += 1 #tx count

		output = io.BytesIO()
		np.savetxt(output, res)

		x = output.getvalue()

		return x.decode() 
	
	def noScaling(self, x):
		return x

	def scaleLog(self, x):
		if x>=1:
			return math.log(x, 10)
		return 0