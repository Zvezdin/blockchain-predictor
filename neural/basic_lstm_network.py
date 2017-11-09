from neural_network import NeuralNetwork

import numpy as np
import math
from keras.models import Sequential
from keras.layers import *
from keras.optimizers import *
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
		if 'stateful' not in args:
			args['stateful'] = False

		#remove any zero-size LSTM/dense layers
		for arr in [args['LSTM'], args['dense']]:
			while 0 in arr: arr.remove(0)

		features = givenDataset['train'].shape[2]
		time_steps = givenDataset['train'].shape[1]


		for kind in ['warm', 'train', 'test']:
			#reformat only the labels first
			labels[kind] = givenLabels[kind].astype(np.float32) #shape of labels is (samples, targets)

			self.num_targets = labels[kind].shape[1]
			#_, labels[kind] = self.reformat(givenDataset[kind], givenLabels[kind], features, time_steps, num_labels)
			#reformat the dataset for LSTM format of [samples, time steps, features]
			dataset[kind] = np.reshape(givenDataset[kind], (-1, givenDataset[kind].shape[1], givenDataset[kind].shape[2]))
			print('%s dataset with initial shape %s and resulting shape %s with labels %s' % (kind, givenDataset[kind].shape, dataset[kind].shape, labels[kind].shape))

		model = Sequential()

		for i, layer in enumerate(args['LSTM']):
			ret_seq=(i< (len(args['LSTM'])-1))
			if i==0:
				model.add(LSTM(layer, return_sequences=ret_seq, stateful=args['stateful'], batch_input_shape=(args['batch'], time_steps, features) ) )
				model.add(Dropout(0.1))
			else:
				model.add(LSTM(layer, return_sequences=ret_seq, stateful=args['stateful']) )
			#model.add(Activation('relu'))
			print("Adding LSTM Layer of size %d." % layer)

		for dense in args['dense']:
			model.add(Dense(dense))
			#model.add(Activation('relu'))

		model.add(Dense(self.num_targets, activation='linear'))

		#model.add(PReLU(alpha_initializer='zeros', alpha_regularizer=None, alpha_constraint=None, shared_axes=None))

		opt = Adam(args['lr'])

		model.compile(loss='mean_squared_error', optimizer=opt)

		if not args['stateful']:
			model.fit(dataset['train'], labels['train'], epochs=args['epoch'], batch_size=args['batch'], verbose=1, shuffle=False)
		else:
			for i in range(args['epoch']):
				model.predict(dataset['warm'], batch_size=args['batch']) #predict so that fitting starts with a state
				model.fit(dataset['train'], labels['train'], epochs=1, batch_size=args['batch'], verbose=0, shuffle=False)
				model.reset_states()

		# make predictions
		self.prediction = {}

		predictionBatch = args['batch']

		model.predict(dataset['warm'], batch_size=predictionBatch)
		self.prediction['train'] = model.predict(dataset['train'], batch_size=predictionBatch)
		self.prediction['test'] = model.predict(dataset['test'], batch_size=predictionBatch)
		model.reset_states()

		print(self.prediction['test'].shape)

		self.scorePrediction(self.prediction, labels, 'train', self.num_targets)
		self.scorePrediction(self.prediction, labels, 'test', self.num_targets)

			

	def predict(self, setType):
		return self.prediction[setType]