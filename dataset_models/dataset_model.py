import abc

from imageNormalizer import ImageNormalizer
from basicNormalizer import BasicNormalizer
from aroundZeroNormalizer import AroundZeroNormalizer

import numpy as np

class DatasetModel(abc.ABC):
	"""An abstract class that is inherited by all dataset models."""

	def __init__(self):
			self.name = ""
			self.requires = []

	@abc.abstractmethod
	def generate(self, properties, targets, args):
		"""Generates a dataset using the properties provided"""

	@staticmethod
	def local_normalization(frame, initialTarget, target):
		normTarget = np.divide(target, initialTarget, where=initialTarget!=0) - 1.0
		normFrame = np.ndarray(frame.shape)

		for i in range(normFrame.shape[0]): #every timestep
			normFrame[i] = np.divide(frame[i], frame[0], where=frame[0]!=0) - 1.0

		return (normFrame, normTarget)

	@staticmethod
	def basic_normalization(arr):
		return BasicNormalizer(arr)

	@staticmethod
	def around_zero_normalization(arr):
		return AroundZeroNormalizer(arr)

	@staticmethod
	def conver_to_binary(arr):
		return (arr >= 0.5).astype(np.float32)

	@staticmethod
	def normalize(arr, method):
		if method == 'basic':
			return DatasetModel.basic_normalization(arr)
		elif method == 'around_zero':
			return DatasetModel.around_zero_normalization(arr)
		elif method == 'auto':
			if np.sum(arr < 0) > 0: #if we have negative values
				return DatasetModel.around_zero_normalization(arr) #around_zero method is recommended for signed values
			else:
				return DatasetModel.basic_normalization(arr) #basic works in any case
		else:
			raise ValueError("Unsupported normalization algorithm %s!" % method)