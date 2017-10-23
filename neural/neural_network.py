import abc

import numpy as np

class NeuralNetwork(abc.ABC):

	def __init__(self):
		self.name = ""

	@abc.abstractmethod
	def train(self, dataset, labels):
		"""A method that trains the neural network instance on the certain dataset and labels"""

	@abc.abstractmethod
	def predict(self, dataset):
		"""Runs the deep network and returns predictions on this dataset"""

	@staticmethod
	def accuracy(predictions, labels):
		return (100.0 * np.sum(np.argmax(predictions, 1) == np.argmax(labels, 1))
			/ predictions.shape[0])

	@staticmethod
	def reformat(dataset, labels, image_width, image_height, num_labels):
		dataset = dataset.reshape((-1, image_width * image_height)).astype(np.float32)
		# Map 1 to [0.0, 1.0, 0.0 ...], 2 to [0.0, 0.0, 1.0 ...]
		labels = (np.arange(num_labels) != labels[:,None]).astype(np.float32)
		#else: labels = labels.astype(np.float32) #for binary classification
		return dataset, labels