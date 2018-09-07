from .postprocessor import Postprocessor

class PostprocessorRelative(Postprocessor):

	def __init__(self):
		super().__init__()

		self.name = "postprocessorRelative"
		self.previousTicks = 1

	def processTick(self, data):
		assert(len(data.keys()) == 1) #we can do relative of only one data source

		for key in data:
			df = data[key]
			assert(df.shape[1] == (2, 1)) #only one data column and 2 values

			val = df[df.columns[0]].values

			return val[1] - val[0]