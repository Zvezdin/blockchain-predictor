from property import Property

class PropertyLowPrice(Property):
	def __init__(self):
		self.name = "lowPrice"
		self.requires = ['tick']

	def processTick(self, data):
		return self.averageOfColumn(data[self.requires[0]], 'low')
