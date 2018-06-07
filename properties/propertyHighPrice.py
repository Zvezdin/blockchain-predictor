from .property import Property

class PropertyHighPrice(Property):
	def __init__(self):
		super().__init__()
		self.name = "highPrice"
		self.requires = ['tick']

	def processTick(self, data):
		return self.maxOfColumn(data[self.requires[0]], 'high')
