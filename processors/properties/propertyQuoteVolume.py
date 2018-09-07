from .property import Property

class PropertyQuoteVolume(Property):
	def __init__(self):
		super().__init__()
		self.name = "quoteVolume"
		self.requires = ['tick']

	def processTick(self, data):
		return self.averageOfColumn(data[self.requires[0]], 'quoteVolume')
