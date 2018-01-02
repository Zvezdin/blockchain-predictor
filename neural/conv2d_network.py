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

	def reformat(self, dataset, labels):
		newLabels = labels.astype(np.float32) #shape of labels is (samples, targets)
		if self.invertLabels:
			newLabels = 1-newLabels

		if len(dataset.shape) == 3:
			#reshape from N,time_steps,features to N,time_steps,features,1
			newDataset = np.reshape(dataset, (-1, dataset.shape[1], dataset.shape[2], 1))

		elif len(dataset.shape) == 4:
			#reshape from N,time_steps,height,width to N,height,width,time_steps
			newDataset = np.reshape(dataset, (-1, dataset.shape[2], dataset.shape[3], dataset.shape[1]))

		return (newDataset, newLabels)

	def load(self, filepath):
		self.model = self.loadModelKeras(loadModel)

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

		#remove any zero-size LSTM/dense layers
		for arr in [args['CONV'], args['dense']]:
			while 0 in arr: arr.remove(0)

		height = inputShape[1]
		width = inputShape[2]
		try:
			channels = inputShape[3]
		except IndexError:
			channels = 1

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
		self.model.add(Dense(numTargets, name='1'))
		self.model.add(Activation('linear', name='Linear'))

		#opt = Adam(args['lr'])

		opt = rmsprop(lr=args['lr'], decay=1e-6)

		self.model.compile(loss='mean_squared_error', optimizer=opt)

		self.plotModel(self.model)

	def train(self, givenDataset, givenLabels, args = {}):
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

		if args['activationMap'] is not None:
			activationMap(args['activationMap'])

		# make predictions
		self.prediction = {}

		self.prediction['train'] = self.model.predict(dataset['train'], batch_size=args['batch'])
		self.prediction['test'] = self.model.predict(dataset['test'], batch_size=args['batch'])

		print(self.prediction['test'].shape)

		self.scorePrediction(self.prediction, labels, 'train', self.num_targets)
		self.scorePrediction(self.prediction, labels, 'test', self.num_targets)

		return history
			

	def predict(self, dataset):
		if self.invertLabels:
			return 1-self.model.predict(dataset)
		return self.model.predict(dataset)

	def evaluate(self, dataset):
		return self.scorePrediction(self.predict(dataset))

	def activationMap(layer_name):
		print("Creating an activation map for layer %s." % layer_name)
		intermediate_layer_model = Model(inputs=self.model.input, outputs=self.model.get_layer(layer_name).output)
		units = intermediate_layer_model.predict(dataset['test'])

		print(units.shape)

		filters = units.shape[3]
		plt.figure(1, figsize=(20,20))
		n_columns = 6
		n_rows = math.ceil(filters / n_columns) + 1
		for i in range(filters):
			plt.subplot(n_rows, n_columns, i+1)
			plt.title('Filter ' + str(i))
			plt.imshow(units[0,:,:,i], interpolation="nearest", cmap="gray")
		plt.show()