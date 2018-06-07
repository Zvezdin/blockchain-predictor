from .property import Property

class PropertyVolumeFrom(Property):
	def __init__(self):
		super().__init__()
		self.name = "volumeFrom"
		self.requires = ['tick']

	def processTick(self, data):
		return self.averageOfColumn(data[self.requires[0]], 'volumefrom')
