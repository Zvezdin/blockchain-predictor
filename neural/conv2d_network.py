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

class Conv2DNetwork(NeuralNetwork):
	def __init__(self):
		self.name="Conv2D"
		self.invertLabels = False
		self.model = None
		self.datasetCache = None

	def train(self, givenDataset, givenLabels, args = {}, loadModel = None):
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
		args.setdefault('activationMap', None)
		args.setdefault('randomData', False)

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
			
			if args['randomData']:
				dataset[kind] = np.random.rand(*dataset[kind].shape)

			print('%s dataset with initial shape %s and resulting shape %s with labels %s' % (kind, givenDataset[kind].shape, dataset[kind].shape, labels[kind].shape))

		self.datasetCache = dataset

		height = dataset['train'].shape[1]
		width = dataset['train'].shape[2]
		try:
			channels = dataset['train'].shape[3]
		except IndexError:
			channels = 1

		history = {}

		if loadModel is not None:
			self.model = self.loadModelKeras(loadModel)
		else:
			self.model = Sequential()
			self.model.add(Conv2D(32, (args['kernel'], args['kernel']), padding='same', input_shape=(height, width, channels), name='c32_1'))
			self.model.add(Activation('relu', name='ReLU_1'))
			self.model.add(Conv2D(32, (args['kernel'], args['kernel']), name='c32_2'))
			self.model.add(Activation('relu', name='ReLU_2'))
			self.model.add(MaxPooling2D(pool_size=(2, 2)))
			self.model.add(Dropout(0.25, name='0.25_1'))
			
			self.model.add(Conv2D(int(32 * sizeModifier), (args['kernel'], args['kernel']), padding='same', name='c32_3', ))#input_shape=(height, width, channels)))
			self.model.add(Activation('relu', name='ReLU_3'))
			self.model.add(Conv2D(int(64 * sizeModifier), (args['kernel'], args['kernel']), name='c64'))
			self.model.add(Activation('relu', name='ReLU_4'))
			self.model.add(MaxPooling2D(pool_size=(2, 2)))
			self.model.add(Dropout(0.25, name='0.25_2'))

			self.model.add(Flatten())
			self.model.add(Dense(512, name='512'))
			self.model.add(Activation('relu', name='ReLU_5'))
			self.model.add(Dropout(0.5, name='0.5'))
			self.model.add(Dense(self.num_targets, name='1'))
			self.model.add(Activation('linear', name='Linear'))

			#opt = Adam(args['lr'])

			opt = rmsprop(lr=args['lr'], decay=1e-6)

			self.model.compile(loss='mean_squared_error', optimizer=opt)

			self.plotModel(self.model)

			for i in range(args['epoch']):
				epochHist = self.model.fit(dataset['train'], labels['train'], validation_data=(dataset['test'], labels['test']), epochs=1, batch_size=args['batch'], verbose=1, shuffle=False)

				prediction = {}
				prediction['test'] = self.model.predict(dataset['test'], batch_size=args['batch'])

				evalHist = self.scorePrediction(prediction, labels, 'test', self.num_targets)[0]

				for key in evalHist: #temporary workaround
					evalHist[key] = evalHist[key]['test']

				print(evalHist)

				for scoresDict in [epochHist.history, evalHist]:
					for key in scoresDict:
						if key not in history:
							history[key] = []
						if type(scoresDict[key]) == list:
							history[key].extend(scoresDict[key])
						else:
							history[key].append(scoresDict[key])


		# make predictions
		self.prediction = {}

		self.prediction['train'] = self.model.predict(dataset['train'], batch_size=args['batch'])
		self.prediction['test'] = self.model.predict(dataset['test'], batch_size=args['batch'])

		print(self.prediction['test'].shape)

		self.scorePrediction(self.prediction, labels, 'train', self.num_targets)
		self.scorePrediction(self.prediction, labels, 'test', self.num_targets)

		return history
			

	def predict(self, setType):
		if self.invertLabels:
			return 1-self.model.predict(self.datasetCache[setType])
		return self.model.predict(self.datasetCache[setType])

	def evaluate(self, setType):
		return self.scorePrediction(self.predict(setType))

	def save(self, filepath):
		self.saveModelKeras(self.model, filepath)