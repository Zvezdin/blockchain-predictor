import numpy as np

from .normalizer import Normalizer

class AroundZeroNormalizer(Normalizer):
	def __init__(self, data):
		self.minVal = np.min(data)
		self.maxVal = np.max(data)

		self.maxVal = max(abs(self.maxVal), abs(self.minVal))

	def transform(self, data):
		if self.maxVal == 0: #can't normalize if the whole array is zeroes
			return data
		
		return ((data / self.maxVal) + 1) / 2

	def inverse_transform(self, data):
		return ((data * 2) - 1) * self.maxVal
