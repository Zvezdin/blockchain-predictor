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
	def basic_normalization(arr):
		print("Normalizing array with shape", arr.shape)
		minVal = np.min(arr)
		maxVal = np.max(arr)

		return (arr - minVal) / (maxVal - minVal)

