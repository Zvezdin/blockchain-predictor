from ..properties.property import Property

class Postprocessor(Property):
	
	def __init__(self):
		super().__init__()

	def calculateAction(self, data):
		raise NotImplementedError()
	
	def processTick(self, data):
		assert(len(data.keys()) == 1) #we can do postprocessing of only one data source

		for key in data:
			df = data[key]
			assert(df.shape == (self.previousTicks + 1 + self.nextTicks, 1)) #only one data column and x values

			val = df[df.columns[0]].values

			return self.calculateAction(val)
