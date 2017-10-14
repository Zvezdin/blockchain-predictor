from property import Property

class PropertyGasPrice(Property):
	def __init__(self):
		self.name = "gasPrice"
		self.requires=['tx']

	def processTick(self, data):
		return self.averageOfColumn(data[self.requires[0]], 'gasPrice')
