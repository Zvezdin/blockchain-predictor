import abc

import numpy as np
import math
from sklearn.metrics import mean_squared_error
from keras.utils import plot_model
from keras import backend as K
from keras.models import load_model

class NeuralNetwork(abc.ABC):

	def __init__(self):
		self.name = ""

	@abc.abstractmethod
	def train(self, dataset, labels, args = {}, loadModel = None):
		"""A method that trains the neural network instance on the certain dataset and labels"""

	@abc.abstractmethod
	def predict(self, dataset):
		"""Runs the deep network and returns predictions on this dataset"""

	@abc.abstractmethod
	def evaluate(self, dataset, labels):
		"""Evaluates the performance on a certain dataset based on multiple factors."""

	@abc.abstractmethod
	def save(self, filepath):
		"""Saves the model arch, weights and optimizer state"""

	@abc.abstractmethod
	def load(self, filepath):
		"""Loads the model arch, weights and optimizer state"""

	@abc.abstractmethod
	def build(self, args = {}):
		"""Builds the model"""

	@abc.abstractmethod
	def reformat(self, dataset, labels):
		"""Reformats the dataset and labels based on network specification"""

	@staticmethod
	def accuracy(predictions, labels):
		return (100.0 * np.sum(np.argmax(predictions, 1) == np.argmax(labels, 1))
			/ predictions.shape[0])

	@staticmethod
	def labelsReformat(dataset, labels, image_width, image_height, num_labels):
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
		#Note: using this as a Keras metric doesn't work
		#Keras uses tensors and restricts operations to only what given
		relative_zero = 0.0 #constant, depends on the dataset type and cannot be easily retrieved

		correct_signs = 0.0
		absolutePrices = True

		if len(labels[labels<0]) > len(labels) * 0.07: #if the negative values are more than 7% of all values
			absolutePrices = False #they are relative

		print("Working with %s values." % ('absolute' if absolutePrices else 'relative'))

		for i in range(len(labels)):
			if not absolutePrices:
				if (labels[i] >= relative_zero and prediction[i] >= relative_zero) or (labels[i] < relative_zero and prediction[i] < relative_zero):
					correct_signs += 1
			else:
				if i == 0:
					continue
				else:
					if (labels[i] - labels[i-1]) * (prediction[i] - prediction[i-1]) > 0: #if the sign of the change is the same
						correct_signs += 1
		
		correct_signs /= len(labels)

		return correct_signs

	@staticmethod
	def custom_accuracy(labels, prediction):
		total = 0.0

		for i in range(len(labels)):
			minDel = min(prediction[i], labels[i])

			if minDel != 0:
				total += abs(labels[i] - prediction[i]) / minDel

		total /= len(labels)

		return total

	@staticmethod
	def R2(labels, prediction):
		sumOfErrors = 0.0
		nullModel = 0.0
		for i in range(len(labels)):
			sumOfErrors += pow(labels[i] - prediction[i], 2)
			nullModel += pow(0.5 - labels[i], 2)

		return 1 - sumOfErrors / nullModel

	@staticmethod
	def scorePrediction(prediction, labels):
		results = []
		for target in range(labels.shape[1]):
			# calculate root mean squared error
			rmse = NeuralNetwork.RMSE(labels[:, target], prediction[:,target])
			sign = NeuralNetwork.sign_accuracy(labels[:, target], prediction[:,target])
			custom = NeuralNetwork.custom_accuracy(labels[:, target], prediction[:,target])
			R2 = NeuralNetwork.R2(labels[:, target], prediction[:,target])

			results.append({'rmse': rmse, 'sign': sign, 'custom': custom, 'R2': R2})

		return results

	@staticmethod
	def mergeHistories(history, newPart):
		for key in newPart:
			if key not in history:
				history[key] = []
			if type(newPart[key]) == list:
				history[key].extend(newPart[key])
			else:
				history[key].append(newPart[key])

	@staticmethod
	def activationMap(model, layer_name, dataset, n_columns=6):
		print("Creating an activation map for layer %s." % layer_name)
		intermediate_layer_model = Model(inputs=model.input, outputs=model.get_layer(layer_name).output)
		units = intermediate_layer_model.predict(dataset)

		print(units.shape)

		filters = units.shape[3]
		plt.figure(1, figsize=(20,20))
		n_rows = math.ceil(filters / n_columns) + 1
		for i in range(filters):
			plt.subplot(n_rows, n_columns, i+1)
			plt.title('Filter ' + str(i))
			plt.imshow(units[0,:,:,i], interpolation="nearest")
		plt.show()

	@staticmethod
	def plotModel(model):
		plot_model(model, to_file='model.png')

	@staticmethod
	def saveModelKeras(model, filepath):
		model.save(filepath)
	
	@staticmethod
	def loadModelKeras(filepath):
		return load_model(filepath)
