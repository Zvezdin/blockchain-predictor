from property import Property

class PropertyBlockDifficulty(Property):
	def __init__(self):
		super().__init__()
		self.name = "blockDifficulty"
		self.requires = ['block']

	def processTick(self, data):
		return self.averageOfColumn(data[self.requires[0]], 'difficulty')
