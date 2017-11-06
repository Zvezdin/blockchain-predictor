from property import Property
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

		#this property does not have a value. It only provides child properties.
		self.provides = [self.name + str(i) for i in range(self.tickCount * self.subPropertyCount)]

	def processTick(self, data):
		txs = data['tx']

		res = np.zeros((self.subPropertyCount, self.tickCount))

		#update our global dictionary of balances
		for tx in txs.itertuples():

			val = float(tx.value)
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

		#update the max balance
		self.maxBalance = max(self.accounts.values())

		if self.maxBalance != 0:
			for tx in txs.itertuples():

				val = float(tx.value)
				sender = tx._2
				receiver = tx.to

				fromI = min(int((self.accounts[sender] / self.maxBalance) * self.tickCount), self.tickCount-1)
				toI = min(int((self.accounts[receiver] / self.maxBalance) * self.tickCount), self.tickCount-1)


				res[0][toI] += val #value to
				res[1][fromI] += val#value from
				res[2][fromI] += 1 #tx count

		return res.reshape((res.shape[0] * res.shape[1])) #flatten for storage