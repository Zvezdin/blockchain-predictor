from .property import Property

import math

import numpy as np

class PropertyUniqueAccounts(Property):
	def __init__(self):
		super().__init__()
		self.name = "uniqueAccounts"
		self.requires = ['tx']
		self.requiresHistoricalData  = True
		self.accounts = {}
		self.uniqueAccounts = 0

	def processTick(self, data):
		txs = data['tx']

		#update our global dictionary of accounts
		for tx in txs.itertuples():

			sender = tx._4 #the field is named 'from', but it is renamed to its index in the tuple
							#due to it being a python keyword. Beware, this will break if the raw data changes.
			receiver = tx.to

			if receiver not in self.accounts:
				self.accounts[receiver] = True
				self.uniqueAccounts += 1
		
		return self.uniqueAccounts