from neural_network import NeuralNetwork

import numpy as np
import math
from keras.models import Sequential
from keras.layers import *
from keras.optimizers import *
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error

class BasicConvNetwork(NeuralNetwork):
	def __init__(self):
		self.name="CONV"

	def train(self, givenDataset, givenLabels, args = {}):
		dataset = {}
		labels = {}

		sizeModifier = 1

		if 'epoch' not in args:
			args['epoch'] = 5
		if 'CONV' not in args:
			args['CONV'] = [10]
		elif type(args['CONV']) != list:
			args['CONV'] = [args['CONV']]
		if 'dense' not in args:
			args['dense'] = []
		elif type(args['dense']) != list:
			args['dense'] = [args['dense']]
		if 'batch' not in args:
			args['batch'] = 16
		if 'lr' not in args:
			args['lr'] = 0.0001

		#remove any zero-size LSTM/dense layers
		for arr in [args['CONV'], args['dense']]:
			while 0 in arr: arr.remove(0)

		features = givenDataset['train'].shape[2]
		time_steps = givenDataset['train'].shape[1]


		for kind in ['warm', 'train', 'test']:
			#reformat only the labels first
			labels[kind] = givenLabels[kind].astype(np.float32) #shape of labels is (samples, targets)

			self.num_targets = labels[kind].shape[1]
			dataset[kind] = np.reshape(givenDataset[kind], (-1, givenDataset[kind].shape[1], givenDataset[kind].shape[2], 1))
			print('%s dataset with initial shape %s and resulting shape %s with labels %s' % (kind, givenDataset[kind].shape, dataset[kind].shape, labels[kind].shape))

		model = Sequential()
		model.add(Conv2D(32 // sizeModifier, (3, 3), padding='same', input_shape=(time_steps, features, 1)))
		model.add(Activation('relu'))
		model.add(Conv2D(32 // sizeModifier, (3, 3)))
		model.add(Activation('relu'))
		#model.add(MaxPooling2D(pool_size=(2, 2)))
		model.add(Dropout(0.25))

		model.add(Conv2D(64 // sizeModifier, (3, 3), padding='same'))
		model.add(Activation('relu'))
		model.add(Conv2D(64 // sizeModifier, (3, 3)))
		model.add(Activation('relu'))
		#model.add(MaxPooling2D(pool_size=(2, 2)))
		model.add(Dropout(0.25))

		model.add(Flatten())
		model.add(Dense(512 // sizeModifier))
		model.add(Activation('relu'))
		model.add(Dropout(0.5))
		model.add(Dense(self.num_targets, activation='linear'))

		#opt = Adam(args['lr'])

		opt = rmsprop(lr=0.0001, decay=1e-6)

		model.compile(loss='mean_squared_error', optimizer=opt)

		model.fit(dataset['train'], labels['train'], validation_data=(dataset['test'], labels['test']), epochs=args['epoch'], batch_size=args['batch'], verbose=1, shuffle=False)

		# make predictions
		self.prediction = {}

		self.prediction['train'] = model.predict(dataset['train'], batch_size=args['batch'])
		self.prediction['test'] = model.predict(dataset['test'], batch_size=args['batch'])

		print(self.prediction['test'].shape)

		self.scorePrediction(self.prediction, labels, 'train', self.num_targets)
		self.scorePrediction(self.prediction, labels, 'test', self.num_targets)

			

	def predict(self, setType):
		return self.prediction[setType]
