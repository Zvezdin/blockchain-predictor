from property import Property

class PropertyHighPrice(Property):
	def __init__(self):
		self.name = "highPrice"
		self.requires = ['tick']

	def processTick(self, data):
		return self.averageOfColumn(data[self.requires[0]], 'high')
