from neural_network import NeuralNetwork

import numpy as np
import math
from keras.models import Sequential
from keras.layers import *
from keras.optimizers import *
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error

class CustomDeepNetwork(NeuralNetwork):
	def __init__(self):
		self.name="CustomDeep"
		self.model = None

	def train(self, givenDataset, givenLabels, args = {}, loadModel = None):
		dataset = {}
		labels = {}

		if 'epoch' not in args:
			args['epoch'] = 5
		if 'hidden' not in args:
			args['hidden'] = [2048, 1024, 512, 50]
		elif type(args['hidden']) != list:
			args['hidden'] = [args['hidden']]
		if 'batch' not in args:
			args['batch'] = 16
		if 'lr' not in args:
			args['lr'] = 0.0001

		#remove any zero-size LSTM/dense layers
		for arr in [args['hidden']]:
			while 0 in arr: arr.remove(0)

		features = givenDataset['train'].shape[2]
		time_steps = givenDataset['train'].shape[1]


		for kind in ['warm', 'train', 'test']:
			#reformat only the labels first
			labels[kind] = givenLabels[kind].astype(np.float32) #shape of labels is (samples, targets)

			self.num_targets = labels[kind].shape[1]
			dataset[kind] = np.reshape(givenDataset[kind], (-1, givenDataset[kind].shape[1] * givenDataset[kind].shape[2]))
			print('%s dataset with initial shape %s and resulting shape %s with labels %s' % (kind, givenDataset[kind].shape, dataset[kind].shape, labels[kind].shape))

		history = {}

		if loadModel is not None:
			model = self.loadModelKeras(loadModel)
		else:
			model = Sequential()

			for i, layer in enumerate(args['hidden']):
				if i==0:
					model.add(Dense(layer, batch_input_shape=(args['batch'], time_steps * features), name=str(layer) ) )
					model.add(Dropout(0.1, name='0.1'))
				else:
					model.add(Dense(layer, name=str(layer)) )
				model.add(Activation('relu', name='relu_'+str(i+1)))
				print("Adding Dense Layer of size %d." % layer)

			model.add(Dense(self.num_targets, name='1'))
			model.add(Activation('linear', name='linear'))

			#model.add(PReLU(alpha_initializer='zeros', alpha_regularizer=None, alpha_constraint=None, shared_axes=None))

			opt = Adam(args['lr'])

			model.compile(loss='mean_squared_error', optimizer=opt)

			self.plotModel(model)

			for i in range(args['epoch']):
				epochHist = model.fit(dataset['train'], labels['train'], validation_data=(dataset['test'], labels['test']), epochs=1, batch_size=args['batch'], verbose=1, shuffle=False)

				prediction = {}
				prediction['test'] = model.predict(dataset['test'], batch_size=args['batch'])

				evalHist = self.scorePrediction(prediction, labels, 'test', self.num_targets)[0]

				for key in evalHist: #temporary workaround
					evalHist[key] = evalHist[key]['test']

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

		predictionBatch = args['batch']

		model.predict(dataset['warm'], batch_size=predictionBatch)
		self.prediction['train'] = model.predict(dataset['train'], batch_size=predictionBatch)
		self.prediction['test'] = model.predict(dataset['test'], batch_size=predictionBatch)
		model.reset_states()

		print(self.prediction['test'].shape)

		self.scorePrediction(self.prediction, labels, 'train', self.num_targets)
		self.scorePrediction(self.prediction, labels, 'test', self.num_targets)

		self.model = model

		return history

	def predict(self, setType):
		return self.prediction[setType]

	def evaluate(self, setType):
		pass #TODO implement

	def save(self, filepath):
		self.saveModelKeras(self.model, filepath)