from neural_network import NeuralNetwork

import numpy as np
import math
from keras.models import Sequential
from keras.layers import *
from keras.optimizers import RMSprop
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
		if 'dense' not in args:
			args['dense'] = []
		elif type(args['dense']) != list:
			args['dense'] = [args['dense']]
		if 'batch' not in args:
			args['batch'] = 16
		if 'lr' not in args:
			args['lr'] = 0.0001

		#remove any zero-size LSTM/dense layers
		for arr in [args['LSTM'], args['dense']]:
			while 0 in arr: arr.remove(0)

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

		for i, layer in enumerate(args['LSTM']):
			ret_seq=(i< (len(args['LSTM'])-1))
			if i==0:
				model.add(LSTM(layer, input_shape=(time_steps, features), return_sequences=ret_seq ) )
			else:
				model.add(LSTM(layer, return_sequences=ret_seq ) )
			model.add(Dropout(0.2))
			print("Adding LSTM Layer of size %d." % layer)

		for dense in args['dense']:
			model.add(Dense(dense))
			#model.add(Activation('relu'))

		model.add(Dense(1))

		model.add(Activation('linear'))

		opt = RMSprop(args['lr'])

		model.compile(loss='mean_squared_error', optimizer=opt)
		model.fit(dataset['train'], labels['train'], epochs=args['epoch'], batch_size=args['batch'], verbose=2)

		# make predictions
		self.prediction = {}
		score = {}
		sign = {}
		custom = {}
		R2 = {}

		for kind in ['train', 'valid', 'test']:
			self.prediction[kind] = model.predict(dataset[kind])

			# calculate root mean squared error
			score[kind] = self.RMSE(labels[kind], self.prediction[kind][:,0])
			sign[kind] = self.sign_accuracy(labels[kind], self.prediction[kind][:,0])
			custom[kind] = self.custom_accuracy(labels[kind], self.prediction[kind][:,0])
			R2[kind] = self.R2(labels[kind], self.prediction[kind][:,0])

			print("Scores for %s." % kind)
			print('%f RMSE\t%f sign\t%f custom\t%f R2' % (score[kind], sign[kind], custom[kind], R2[kind]))
			

	def predict(self, setType):
		return self.prediction[setType]