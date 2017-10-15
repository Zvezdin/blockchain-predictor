from property import Property

class PropertyNetworkHashrate(Property):
	def __init__(self):
		self.name = "blockDifficulty"
		self.requires = ['block']

	def processTick(self, data):
		bl = data[self.requires[0]]

		if (bl.shape[0] > 1): #if we have one or zero rows, we will divide by zero.
			avgDifficulty =  self.averageOfColumn(bl, 'difficulty')
			start = bl.get_value(bl.index[0], 'date')
			end = bl.get_value(bl.index[bl.shape[0]-1], 'date')
			avgBlockTime = (end - start).total_seconds()

			return (avgDifficulty / avgBlockTime)
		return 0