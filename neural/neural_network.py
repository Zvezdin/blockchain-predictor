import abc

import numpy as np
import math
from sklearn.metrics import mean_squared_error

class NeuralNetwork(abc.ABC):

	def __init__(self):
		self.name = ""

	@abc.abstractmethod
	def train(self, dataset, labels, args = {}):
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

		#for value generation
		labels = labels.astype(np.float32)

		labels.reshape((labels.shape[0], 1))

		labels = labels[:, None]

		#for binary classification
		#labels = (np.arange(num_labels) != labels[:,None]).astype(np.float32)
		return dataset, labels

	@staticmethod
	def RMSE(labels, prediction):
		return math.sqrt(mean_squared_error(labels, prediction))
	
	@staticmethod
	def sign_accuracy(labels, prediction):
		correct_signs = 0.0
		for i in range(len(labels)):
			if (labels[i] >= 0.5 and prediction[i] >= 0.5) or (labels[i] < 0.5 and prediction[i] < 0.5):
				correct_signs += 1
		
		correct_signs /= len(labels)

		return correct_signs

	@staticmethod
	def custom_accuracy(labels, prediction):
		total = 0.0

		for i in range(len(labels)):
			total += abs(labels[i] - prediction[i]) / min(prediction[i], labels[i])

		total /= len(labels)

		return total

	@staticmethod
	def R2(labels, prediction):
		sumOfErrors = 0.0
		nullModel = 0.0
		for i in range(len(labels)):
			sumOfErrors += pow(labels[i] - prediction[i], 2)
			nullModel += pow(0.5 - prediction[i], 2)

		return 1 - sumOfErrors / nullModel