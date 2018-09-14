import numpy as np
from itertools import product

from .normalizer import Normalizer

class ImageNormalizer(Normalizer):
	def __init__(self, data, localStd = False):
		self.startAxis = 1 if len(data.shape) > 1 else 0

		self.meanFrame = np.ndarray(data.shape[self.startAxis:])
		self.stdFrame = np.ndarray(self.meanFrame.shape)

		self.localStd = localStd

		axes = []

		for axis in data.shape[self.startAxis:]:
			axes.append(np.arange(axis))

		for point in product(*axes):
			#add a slice to our point if needed. Equivalent of ':' in index
			idx = (slice(None),) + point if self.startAxis is not 0 else point
			self.meanFrame[point] = np.mean(data[idx])
			self.stdFrame[point] = np.std(data[idx])
		self.stdVal = np.std(data)

	def transform(self, data):
		arr = data.copy()
		if self.startAxis > 0:
			for i in range(arr.shape[0]):
				arr[i] = arr[i] - self.meanFrame
		else:
			arr = arr - self.meanFrame

		if self.localStd:
			arr = np.divide(arr, self.stdFrame, where=self.stdFrame!=0)
		else:
			arr = arr / self.stdVal
		
		return arr

	def inverse_transform(self, data):
		arr = data.copy()
		
		if self.localStd:
			arr = arr * self.stdFrame
		else:
			arr = arr * self.stdVal

		if self.startAxis > 0:
			for i in range(arr.shape[0]):
				arr[i] = arr[i] + self.meanFrame
		else:
			arr = arr + self.meanFrame

		return arr
