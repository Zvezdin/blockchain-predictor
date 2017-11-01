from neural_network import NeuralNetwork

import numpy as np
import math
from keras.models import Sequential
from keras.layers import Dense, Activation, Dropout
from keras.layers import LSTM
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error

class BasicLSTMNetwork(NeuralNetwork):
	def __init__(self):
		self.name="LSTM"

	def train(self, givenDataset, givenLabels, args = {}):
		dataset = {}
		labels = {}

		if 'epoch' not in args:
			args['epoch'] = 5
		if 'LSTM' not in args:
			args['LSTM'] = [10, 10]
		elif type(args['LSTM']) != list:
			args['LSTM'] = [args['LSTM']]
		if 'batch' not in args:
			args['batch'] = 16

		features = givenDataset['train'].shape[2]
		time_steps = givenDataset['train'].shape[1]
		num_labels = 1


		for kind in ['train', 'valid', 'test']:
			#reformat only the labels first
			_, labels[kind] = self.reformat(givenDataset[kind], givenLabels[kind], features, time_steps, num_labels)
			#reformat the dataset for LSTM format of [samples, time steps, features]
			dataset[kind] = np.reshape(givenDataset[kind], (-1, givenDataset[kind].shape[1], givenDataset[kind].shape[2]))
			print('%s dataset with initial shape %s and resulting shape %s with labels %s' % (kind, givenDataset[kind].shape, dataset[kind].shape, labels[kind].shape))

		model = Sequential()

		model.add(LSTM(50,
			input_shape=(time_steps, features),
			return_sequences=True))
		model.add(Dropout(0.2))

		model.add(LSTM(100, return_sequences=False))
		model.add(Dropout(0.2))

		model.add(Dense(1))

		model.add(Activation('sigmoid'))
		model.compile(loss='mean_squared_error', optimizer='rmsprop')
		model.fit(dataset['train'], labels['train'], epochs=args['epoch'], batch_size=args['batch'], verbose=2)

		# make predictions
		self.prediction = {}
		score = {}
		sign = {}
		custom = {}

		for kind in ['train', 'valid', 'test']:
			self.prediction[kind] = model.predict(dataset[kind])

			# calculate root mean squared error
			score[kind] = self.RMSE(labels[kind], self.prediction[kind][:,0])
			sign[kind] = self.sign_accuracy(labels[kind], self.prediction[kind][:,0])
			custom[kind] = self.custom_accuracy(labels[kind], self.prediction[kind][:,0])
			print("Scores for %s." % kind)
			print('%f RMSE\t%f sign\t%f custom' % (score[kind], sign[kind], custom[kind]))
			

	def predict(self, dataset):
		return self.prediction['test']