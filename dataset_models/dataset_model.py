import abc

import numpy as np

class DatasetModel(abc.ABC):
	"""An abstract class that is inherited by all dataset models."""

	def __init__(self):
			self.name = ""
			self.requires = []

	@abc.abstractmethod
	def generate(self, properties, args):
		"""Generates a dataset using the properties provided"""
	
	@staticmethod
	def basic_normalization(arr, base = None):
		if base is None: base = arr

		minVal = np.min(base)
		maxVal = np.max(arr)

		return (arr - minVal) / (maxVal - minVal)

	@staticmethod
	def around_zero_normalization(arr, base = None):
		if base is None: base = arr

		minVal = np.min(base)
		maxVal = np.max(base)

		maxVal = max(abs(maxVal), abs(minVal))

		#make arr [-1;1]
		arr /= maxVal
		arr += 1
		arr /= 2
		#is within [0;1] and 0.5 is 0

		return arr
