import numpy as np

from .postprocessor import Postprocessor


class Postprocessor10max(Postprocessor):

	def __init__(self):
		super().__init__()

		self.name = "%s_10max"
		self.nextTicks = 9 #total of 10 periods processed at once

	def calculateAction(self, data):
		if not isinstance(data[0], np.ndarray):
			return max(data)
		else:
			data = np.array([x for x in data])
			print(data, type(data), data.shape)
			res = data.max(0)
			
			return res