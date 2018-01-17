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
		self.name = "LSTM"
		self.model = None
		self.cut_timesteps = False
		self.batch_size = None

	def reformat(self, dataset, labels, cut_timesteps=False):
		newLabels = None

		if labels is not None:
			newLabels = labels.astype(np.float32) #shape of labels is (samples, targets)

		if len(dataset.shape) == 3:
			#shape is N,time_steps,features
			newDataset = np.reshape(dataset, (-1, dataset.shape[1], dataset.shape[2]))

		elif len(dataset.shape) >= 4:
			raise ValueError("Unable to handle 4+D input shape %s!" % str(dataset.shape))

		if cut_timesteps:
			print("Warning! Cutting all previous timesteps")
			newDataset = np.reshape(newDataset[:, -1, :], (-1, 1, newDataset.shape[2])) #cut except the latest time step

		return (newDataset, newLabels)

	def load(self, filepath):
		self.model = self.loadModelKeras(filepath)

	def save(self, filepath):
		self.saveModelKeras(self.model, filepath)

	def build(self, inputShape, numTargets, args = {}):
		if 'LSTM' not in args:
			args['LSTM'] = [128, 256]
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
		if 'cut_timesteps' not in args:
			args['cut_timesteps'] = False
		
		self.cut_timesteps = args['cut_timesteps']
		self.batch_size = args['batch']

		features = inputShape[2]
		time_steps = inputShape[1]

		if self.cut_timesteps:
			time_steps = 1

		#remove any zero-size LSTM/dense layers
		for arr in [args['LSTM'], args['dense']]:
			while 0 in arr: arr.remove(0)

		self.model = Sequential()

		for i, layer in enumerate(args['LSTM']):
			ret_seq=(i< (len(args['LSTM'])-1))
			name = str(layer)+ '_' + str(i+1) + ('_ret_seq' if ret_seq else '')
			if i==0:
				self.model.add(LSTM(layer, return_sequences=ret_seq, stateful=args['stateful'], batch_input_shape=(args['batch'], time_steps, features), name=name ) )
				self.model.add(Dropout(0.1, name='0.1'))
			else:
				self.model.add(LSTM(layer, return_sequences=ret_seq, stateful=args['stateful'], name=name) )
			#model.add(Activation('relu'))
			print("Adding LSTM Layer of size %d." % layer)

		for dense in args['dense']:
			self.model.add(Dense(dense))
			#model.add(Activation('relu'))

		self.model.add(Dense(numTargets, name=str(numTargets)))
		self.model.add(Activation('linear', name='linear'))

		#model.add(PReLU(alpha_initializer='zeros', alpha_regularizer=None, alpha_constraint=None, shared_axes=None))

		opt = Adam(args['lr'])

		self.model.compile(loss='mean_squared_error', optimizer=opt)

		self.plotModel(self.model)

	def train(self, givenDataset, givenLabels, args = {}, targetNormalization = None):
		dataset = {}
		labels = {}

		if 'epoch' not in args:
			args['epoch'] = 5
		if 'batch' not in args:
			args['batch'] = 16
		args.setdefault('randomData', False)


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
			if args['stateful']:
				self.model.predict(dataset['warm'], batch_size=args['batch']) #predict so that fitting starts with a state
			epochHist = self.model.fit(dataset['train'], labels['train'], epochs=1, batch_size=args['batch'], validation_data=(dataset['test'], labels['test']), verbose=1, shuffle=False)
			if args['stateful']:
				self.model.reset_states()
			
			prediction = self.model.predict(dataset['test'], batch_size=args['batch'])
			currLabels = labels['test']
			if targetNormalization is not None:
				prediction = self.reverse_target_normalization(prediction, targetNormalization)
				currLabels = self.reverse_target_normalization(currLabels, targetNormalization)
			evalHist = self.scorePrediction(prediction, currLabels)[0]

			self.mergeHistories(history, epochHist.history)
			self.mergeHistories(history, evalHist)

		return history

	def predict(self, dataset):
		dataset, _ = self.reformat(dataset, None, cut_timesteps=self.cut_timesteps)

		return self.model.predict(dataset, batch_size=self.batch_size)

	def evaluate(self, dataset, labels):
		_, labels = self.reformat(dataset, labels, cut_timesteps=self.cut_timesteps) #don't reformat the dataset, predict() will reformat it
		return self.scorePrediction(self.predict(dataset), labels)