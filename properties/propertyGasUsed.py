from property import Property

class PropertyGasUsed(Property):
	def __init__(self):
		self.name = "gasUsed"
		self.requires = ['block']

	def processTick(self, data):
		return self.averageOfColumn(data[self.requires[0]], 'gasUsed')
