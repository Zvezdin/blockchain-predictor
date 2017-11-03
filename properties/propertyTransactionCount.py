from property import Property

class PropertyTransactionCount(Property):
	def __init__(self):
		super().__init__()
		self.name = "transactionCount"
		self.requires = ['tx']

	def processTick(self, data):
		return data[self.requires[0]].shape[0]
