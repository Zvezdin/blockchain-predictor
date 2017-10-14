from property import Property

class PropertyClosePrice(Property):
	def __init__(self):
		self.name = "closePrice"
		self.requires = ['tick']

	def processTick(self, data):
		return self.averageOfColumn(data[self.requires[0]], 'close')
