from property import Property

class PropertyVolume(Property):
	def __init__(self):
		self.name = "volume"
		self.requires = ['tick']

	def processTick(self, data):
		return self.averageOfColumn(data[self.requires[0]], 'volume')
