from property import Property

class PropertyGasLimit(Property):
	def __init__(self):
		self.name = "gasLimit"
		self.requires = ['block']

	def processTick(self, data):
		return self.averageOfColumn(data[self.requires[0]], 'gasLimit')
