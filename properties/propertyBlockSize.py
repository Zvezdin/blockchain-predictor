from property import Property

class PropertyBlockSize(Property):
	def __init__(self):
		self.name = "blockSize"
		self.requires = ['block']

	def processTick(self, data):
		return self.averageOfColumn(data[self.requires[0]], 'size')
