from neural_network import NeuralNetwork

import numpy as np
import math
from keras.models import Sequential
from keras.layers import *
from keras.optimizers import *
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error

class Conv2DNetwork(NeuralNetwork):
	def __init__(self):
		self.name="Conv2D"
		self.invertLabels = True

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
		if 'kernel' not in args:
			args['kernel'] = 3

		#remove any zero-size LSTM/dense layers
		for arr in [args['CONV'], args['dense']]:
			while 0 in arr: arr.remove(0)

		for kind in ['warm', 'train', 'test']:
			#reformat only the labels first
			labels[kind] = givenLabels[kind].astype(np.float32) #shape of labels is (samples, targets)
			if self.invertLabels:
				labels[kind] = 1-labels[kind]

			self.num_targets = labels[kind].shape[1]

			if len(givenDataset[kind].shape) == 3:
				#reshape from N,time_steps,features to N,time_steps,features,1
				dataset[kind] = np.reshape(givenDataset[kind], (-1, givenDataset[kind].shape[1], givenDataset[kind].shape[2], 1))
			elif len(givenDataset[kind].shape) == 4:
				#reshape from N,time_steps,height,width to N,height,width,time_steps
				dataset[kind] = np.reshape(givenDataset[kind], (-1, givenDataset[kind].shape[2], givenDataset[kind].shape[3], givenDataset[kind].shape[1]))
			print('%s dataset with initial shape %s and resulting shape %s with labels %s' % (kind, givenDataset[kind].shape, dataset[kind].shape, labels[kind].shape))

		height = dataset['train'].shape[1]
		width = dataset['train'].shape[2]
		try:
			channels = dataset['train'].shape[3]
		except IndexError:
			channels = 1

		model = Sequential()
		#model.add(Conv2D(32 // sizeModifier, (args['kernel'], args['kernel']), padding='same', input_shape=(time_steps, features, 1), name='32_1'))
		#model.add(Activation('relu', name='ReLU_1'))
		#model.add(Conv2D(32 // sizeModifier, (args['kernel'], args['kernel']), name='32_2'))
		#model.add(Activation('relu', name='ReLU_2'))
		##model.add(MaxPooling2D(pool_size=(2, 2)))
		#model.add(Dropout(0.25, name='0.25_1'))

		model.add(Conv2D(32 // sizeModifier, (args['kernel'], args['kernel']), padding='same', name='32_3', input_shape=(height, width, channels)))
		model.add(Activation('relu', name='ReLU_3'))
		model.add(Conv2D(64 // sizeModifier, (args['kernel'], args['kernel']), name='64'))
		model.add(Activation('relu', name='ReLU_4'))
		#model.add(MaxPooling2D(pool_size=(2, 2)))
		model.add(Dropout(0.25, name='0.25_2'))

		model.add(Flatten())
		model.add(Dense(512 // sizeModifier, name='512'))
		model.add(Activation('relu', name='ReLU_5'))
		model.add(Dropout(0.5, name='0.5'))
		model.add(Dense(self.num_targets, name='1'))
		model.add(Activation('linear', name='Linear'))

		#opt = Adam(args['lr'])

		opt = rmsprop(lr=args['lr'], decay=1e-6)

		model.compile(loss='mean_squared_error', optimizer=opt)

		self.plotModel(model)

		model.fit(dataset['train'], labels['train'], validation_data=(dataset['test'], labels['test']), epochs=args['epoch'], batch_size=args['batch'], verbose=1, shuffle=False)

		# make predictions
		self.prediction = {}

		self.prediction['train'] = model.predict(dataset['train'], batch_size=args['batch'])
		self.prediction['test'] = model.predict(dataset['test'], batch_size=args['batch'])

		print(self.prediction['test'].shape)

		self.scorePrediction(self.prediction, labels, 'train', self.num_targets)
		self.scorePrediction(self.prediction, labels, 'test', self.num_targets)

			

	def predict(self, setType):
		if self.invertLabels:
			return 1-self.prediction[setType]
		return self.prediction[setType]