import numpy as np

from normalizer import Normalizer

class BasicNormalizer(Normalizer):
	def __init__(self, data):
		self.minVal = np.min(data)
		self.maxVal = np.max(data)

	def transform(self, data):
		if self.maxVal - self.minVal == 0: #can't normalize if the whole array is zeroes
			return data
		
		return (data - self.minVal) / (self.maxVal - self.minVal)

	def inverse_transform(self, data):
		return data * (self.maxVal - self.minVal) + self.minVal
