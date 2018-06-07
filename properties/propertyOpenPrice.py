from .property import Property

class PropertyOpenPrice(Property):
	def __init__(self):
		super().__init__()
		self.name = "openPrice"
		self.requires = ['tick']

	def processTick(self, data):
		return self.averageOfColumn(data[self.requires[0]], 'open')
