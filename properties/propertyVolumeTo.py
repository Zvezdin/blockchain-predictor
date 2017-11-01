from property import Property

class PropertyVolumeTo(Property):
	def __init__(self):
		self.name = "volumeTo"
		self.requires = ['tick']

	def processTick(self, data):
		return self.averageOfColumn(data[self.requires[0]], 'volumeto')
