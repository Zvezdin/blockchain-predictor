from .property import Property

class PropertyStickPrice(Property):
	def __init__(self):
		super().__init__()
		self.name = "stickPrice"
		self.requires = ['tick']
		self.isRelative = True

	def processTick(self, data):
		index = data[self.requires[0]].index.values

		openP = data[self.requires[0]].get_value(index[0], 'open')
		closeP = data[self.requires[0]].get_value(index[len(index)-1], 'close')

		return closeP - openP
