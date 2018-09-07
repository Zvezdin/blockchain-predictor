from .property import Property

import math

import numpy as np

log10_1_2base = math.log10(1.2)

class PropertyAccountBalanceDistribution(Property):
	def __init__(self):
		super().__init__()
		self.name = "accountBalanceDistribution_log1_2"
		self.requires = ['trace']
		self.requiresHistoricalData  = True
		self.accounts = {}
		self.balanceCutoff = 100000000000000000 # -> 0.1ETH
		self.maxBalance = 1000000000000000000000000 // self.balanceCutoff #1M ETH
		self.subPropertyCount = 3 #vol to, vol from, tx count

		self.scalingFunction = self.log1_2

		self.tickCount = int(self.scalingFunction(self.maxBalance))

	def log1_2(self, x):
		return math.log10(x) / log10_1_2base

	def processTick(self, data):
		traces = data['trace']

		res = np.zeros((self.subPropertyCount, self.tickCount))

		fromCol = data['trace'].columns.get_loc('from')+1

		#update our global dictionary of balances
		for trace in traces.itertuples():

			val = int(trace.value, 0)

			sender = getattr(trace, '_'+str(fromCol)) #the field is named 'from', but it is renamed to its index in the tuple
							#due to it being a python keyword. Beware, this will break if the raw data changes.
			receiver = trace.to

			if isinstance(receiver, float) and math.isnan(receiver):
						receiver = None #receiver is None when the TX is contract publishing

			if isinstance(sender, float) and math.isnan(sender):
				sender = None #receiver is None when the TX is contract publishing

			if receiver is not None and receiver not in self.accounts:
				self.accounts[receiver] = val
			else:
				self.accounts[receiver] += val

			#updating the balance that way is problematic. Better use max(dict)
			#self.maxBalance = max(self.accounts[receiver], self.maxBalance)

			if sender is not None and sender in self.accounts:
				self.accounts[sender] -= val

				if self.accounts[sender] < 0:
					self.accounts[sender] = 0
			else:
				self.accounts[sender] = 0

		if self.maxBalance != 0:
			for trace in traces.itertuples():

				val = int(trace.value, 0)
				sender = getattr(trace, '_'+str(fromCol))
				receiver = trace.to

				
				if not isinstance(sender, float): #if it's not a NaN
					fromBal = 0
					if self.accounts[sender] > self.balanceCutoff:
						fromBal = self.scalingFunction(self.accounts[sender] / self.balanceCutoff)
					fromI = min(int(fromBal), self.tickCount-1)

					res[1][fromI] += val / self.balanceCutoff #value from in ETH
					res[2][fromI] += 1 #tx count

				if not isinstance(receiver, float):
					toBal = 0
					if self.accounts[receiver] > self.balanceCutoff:
						toBal = self.scalingFunction(self.accounts[receiver] / self.balanceCutoff)
					toI = min(int(toBal), self.tickCount-1)

					res[0][toI] += val / self.balanceCutoff #value to in ETH
				

		return res