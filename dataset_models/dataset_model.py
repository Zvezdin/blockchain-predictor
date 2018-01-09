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
	def mean_std_image_normalization(img, localStd):
		raise NotImplementedError

	@staticmethod
	def local_normalization(frame, initialTarget, target):
		normTarget = np.divide(target, initialTarget, where=initialTarget!=0) - 1.0
		normFrame = np.ndarray(frame.shape)

		for i in range(normFrame.shape[0]): #every timestep
			normFrame[i] = np.divide(frame[i], frame[0], where=frame[0]!=0) - 1.0

		return (normFrame, normTarget)

	@staticmethod
	def basic_normalization(arr, base = None):
		if base is None: base = arr

		minVal = np.min(base)
		maxVal = np.max(arr)

		if maxVal - minVal == 0: #can't normalize if the whole array is zeroes
			return arr

		print("Normalized with %d min and %d max." % (minVal, maxVal))

		return (arr - minVal) / (maxVal - minVal)

	@staticmethod
	def around_zero_normalization(arr, base = None):
		if base is None: base = arr

		minVal = np.min(base)
		maxVal = np.max(base)

		maxVal = max(abs(maxVal), abs(minVal))

		if maxVal != 0:
			#make arr [-1;1]
			arr = arr / maxVal
			arr += 1
			arr /= 2
			#is within [0;1] and 0.5 is 0

		return arr

	@staticmethod
	def conver_to_binary(arr):
		return (arr >= 0.5).astype(np.float32)

	@staticmethod
	def normalize(arr, method, base = None):
		if method == 'basic':
			return DatasetModel.basic_normalization(arr, base)
		elif method == 'around_zero':
			return DatasetModel.around_zero_normalization(arr, base)
		elif method == 'auto':
			if np.sum(arr < 0) > 0: #if we have negative values
				return DatasetModel.around_zero_normalization(arr, base) #around_zero method is recommended for signed values
			else:
				return DatasetModel.basic_normalization(arr, base) #basic works in any case