from neural_network import NeuralNetwork

import numpy as np
import math
from keras.models import Sequential
from keras.layers import *
from keras.optimizers import *
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error
from keras.models import Model
import matplotlib.pyplot as plt

class Conv3DNetwork(NeuralNetwork):
	def __init__(self):
		self.name="Conv3D"
		self.invertLabels = False
		self.model = None

	def reformat(self, dataset, labels):
		newLabels = None

		if labels is not None:
			newLabels = labels.astype(np.float32) #shape of labels is (samples, targets)
			if self.invertLabels:
				newLabels = 1-newLabels

		if len(dataset.shape) == 3:
			raise ValueError("Conv3d does not support input shaped %s!" % str(dataset.shape))
		elif len(dataset.shape) == 4:
			#reshape from N,time_steps,height,width to N,height,width,time_steps, 1
			newDataset = np.reshape(dataset, (-1, dataset.shape[2], dataset.shape[3], dataset.shape[1]))
			newDataset = np.reshape(newDataset, (*newDataset.shape, 1))

		return (newDataset, newLabels)

	def load(self, filepath):
		self.model = self.loadModelKeras(filepath)

	def save(self, filepath):
		self.saveModelKeras(self.model, filepath)

	def build(self, inputShape, numTargets, args = {}):
		sizeModifier = 1

		if 'CONV' not in args:
			args['CONV'] = [10]
		elif type(args['CONV']) != list:
			args['CONV'] = [args['CONV']]
		if 'dense' not in args:
			args['dense'] = []
		elif type(args['dense']) != list:
			args['dense'] = [args['dense']]
		if 'lr' not in args:
			args['lr'] = 0.0001
		if 'kernel' not in args:
			args['kernel'] = 3
		args.setdefault('pool', 2)

		#remove any zero-size LSTM/dense layers
		for arr in [args['CONV'], args['dense']]:
			while 0 in arr: arr.remove(0)

		pool = args['pool']

		height = inputShape[1]
		width = inputShape[2]
		time_steps = inputShape[3]
		try:
			channels = inputShape[4]
		except IndexError:
			channels = 1

		self.model = Sequential()
		self.model.add(Conv3D(32, (args['kernel'],)*3, padding='same', input_shape=(height, width, time_steps, channels), name='c32_1'))
		self.model.add(Activation('relu', name='ReLU_1'))
		self.model.add(Conv3D(32, (args['kernel'],)*3, name='c32_2'))
		self.model.add(Activation('relu', name='ReLU_2'))
		self.model.add(MaxPooling3D(pool_size=(pool,)*3))
		self.model.add(Dropout(0.25, name='0.25_1'))
		
		self.model.add(Conv3D(int(32 * sizeModifier), (args['kernel'],)*3, padding='same', name='c32_3', ))
		self.model.add(Activation('relu', name='ReLU_3'))
		self.model.add(Conv3D(int(64 * sizeModifier), (args['kernel'],)*3, name='c64'))
		self.model.add(Activation('relu', name='ReLU_4'))
		self.model.add(MaxPooling3D(pool_size=(pool,)*3))
		self.model.add(Dropout(0.25, name='0.25_2'))

		self.model.add(Flatten())
		self.model.add(Dense(512, name='512'))
		self.model.add(Activation('relu', name='ReLU_5'))
		self.model.add(Dropout(0.5, name='0.5'))
		self.model.add(Dense(numTargets, name='1'))
		self.model.add(Activation('linear', name='Linear'))

		#opt = Adam(args['lr'])

		opt = rmsprop(lr=args['lr'], decay=1e-6)

		self.model.compile(loss='mean_squared_error', optimizer=opt)

		self.plotModel(self.model)

	def train(self, givenDataset, givenLabels, args = {}, targetNormalization = None):
		if 'epoch' not in args:
			args['epoch'] = 5
		if 'batch' not in args:
			args['batch'] = 16
		args.setdefault('activationMap', None)
		args.setdefault('randomData', False)

		dataset = {}
		labels = {}

		for kind in givenDataset:
			dataset[kind], labels[kind] = self.reformat(givenDataset[kind], givenLabels[kind])

			if args['randomData']:
				dataset[kind] = np.random.rand(*dataset[kind].shape)

			print('%s dataset with initial shape %s and resulting shape %s with labels %s' % (kind, givenDataset[kind].shape, dataset[kind].shape, labels[kind].shape))

		if self.model == None: #if no model, build it
			print("Building model.")
			self.build(dataset['train'].shape, labels['train'].shape[1], args)

		history = {}

		for i in range(args['epoch']):
			epochHist = self.model.fit(dataset['train'], labels['train'], validation_data=(dataset['test'], labels['test']), epochs=1, batch_size=args['batch'], verbose=1, shuffle=False)

			prediction = self.model.predict(dataset['test'], batch_size=args['batch'])
			currLabels = labels['test']
			if targetNormalization is not None:
				prediction = self.reverse_target_normalization(prediction, targetNormalization)
				currLabels = self.reverse_target_normalization(currLabels, targetNormalization)
			evalHist = self.scorePrediction(prediction, currLabels)[0]

			self.mergeHistories(history, epochHist.history)
			self.mergeHistories(history, evalHist)

		if args['activationMap'] is not None:
			self.activationMap(self.model, args['activationMap'], dataset['test'])

		return history
			

	def predict(self, dataset):
		dataset, _ = self.reformat(dataset, None)
		if self.invertLabels:
			return 1-self.model.predict(dataset)
		return self.model.predict(dataset)

	def evaluate(self, dataset, labels):
		_, labels = self.reformat(dataset, labels) #don't reformat the dataset, predict() will reformat it
		return self.scorePrediction(self.predict(dataset), labels)
