import numpy as np

from .postprocessor import Postprocessor


class PostprocessorDistribution(Postprocessor):

	def __init__(self):
		super().__init__()

		self.name = "%s_dist"
		self.requires = ['balanceLastSeenDistribution_log1_2']
		self.scale = True
		self.scaleF = np.log2

	def calculateAction(self, data):
		assert(len(data) == 1)
		data = data[0]

		xAxis, yAxis = [':', '1:']

		strToSlice = lambda string: slice(*map(lambda x: int(x.strip()) if x.strip() else None, string.split(':')))

		xAxis = strToSlice(xAxis)
		yAxis = strToSlice(yAxis)

		data = data[yAxis, xAxis]
		minV = np.min(data)

		if minV < 0:
			raise NotImplementedError()

		data = self.scaleF(data)
		data[data<0] = 0 #log if 0 is -inf
		
		return data