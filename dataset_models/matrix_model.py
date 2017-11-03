import pandas as pd
import numpy as np

from dataset_model import DatasetModel


class MatrixModel(DatasetModel):
	def __init__(self):
		self.name="matrix"
		self.requires=[]

	def generate(self, properties, args = {}):
		if not properties: return

		data = properties[0] #first property

		for i in range(1, len(properties)):
			data = pd.merge(data, properties[i]) #merge all properties in one dataframe

		allDates = data['date']

		data.drop('date', axis=1, inplace=True)

		column_incides = {}

		for i, col in enumerate(data.columns):
			column_incides[col] = i

		#argument defaults
		if 'window' not in args:
			args['window'] = 100
		if 'normalize' not in args:
			args['normalize'] = True
		if 'price' not in args:
			try:
				args['price'] = column_incides['stickPrice']
			except KeyError:
				try:
					args['price'] = column_incides['closePrice']
				except KeyError:
					raise #we have no idea which is the price index
		if 'localNormalize' not in args:
			args['localNormalize'] = [None]#['stickPrice']
		if 'normalization' not in args:
			args['normalization'] = {'stickPrice': 'around_zero', 'closePrice': 'around_zero', 'labels': 'around_zero'}
		if 'binary' not in args:
			args['binary'] = False

		#this method can backfire, so it is disabled temporairly
			#remove any zero price deltas - we can't predict based on that
		#data.drop(data[data[data.columns[args['price']]] == 0].index, inplace=True)

		#blacklist = []

		#for prop in properties:
		#	if prop.columns.contains('stickPrice'):
		#		blacklist.extend('openPrice', 'closePrice') #if we have stick price, we want to avoid open and close prices in the end dataset.

		print("Head:")
		print(data.head(5))
		print("Tail:")
		print(data.tail(5))


		priceIndex = args['price']
		#stickAlgorithm = args['stick']

		window_size = args['window']

		vals = data.values

		frames = np.ndarray([len(vals)-window_size, window_size, len(properties)], dtype=np.float64)

		nextPrices = np.ndarray(frames.shape[0])

		dates = []
		
		#sliding window over the values. Step is 1.
		for i in range(len(vals)):
			#if we've reached the end
			if i + window_size >= len(vals): break
			
			#create a frame using sliding window 
			frame = vals[i:i+window_size]

			frames[i] = frame

			nextPrices[i] = vals[i+window_size][priceIndex] #get the price that should be predicted for this frame

			dates.append(allDates.iloc[i+window_size-1])

		print("Head frames:")
		print(frames[:3], frames.shape)

		localNormalize = []

		try:
			localNormalize = [column_incides[x] for x in args['localNormalize']]
		except KeyError:
			pass

		normalization = []

		for col in data.columns:
			if col in args['normalization']:
				normalization.append(args['normalization'][col]) #append the type of normalization for that column index
			else:
				normalization.append('around_zero')

		if args['normalize']:
			print("Normalizing...")
			for x in range(len(properties)):
				if x not in localNormalize: #local normalization happens via another way
					print("Globally normalizing property %d with method %s." % (x, normalization[x]))
					frames[:, :, x] = self.normalize(frames[:, :, x], normalization[x])

			#normalize the property and the predicted price locally
			for x in localNormalize:
				print("Locally normalizing property %d with method %s." % (x, normalization[x]))
				for i, frame in enumerate(frames):
					#find the delta - distance between min and max price to normalize on.

					if x == priceIndex: #normalize the price if it walls with this local property
						nextPrices[i] = min(max(self.normalize(nextPrices[i], normalization[x], frame[:, x]), 0), 1)

					if np.min(frame[:, x]) == 0 and np.max(frame[:, x]) == 0:
						print("Empty dataset at index %i." % i)

					frame[:, x] = self.normalize(frame[:, x], normalization[x])

			if priceIndex not in localNormalize: #if we haven't normalized the labels yet
				nextPrices = self.normalize(nextPrices, args['normalization']['labels'])

		if args['binary']:
			print("Converting data to binary! May cause issues.")
			for x in range(len(properties)):
				frames[:, :, x] = self.conver_to_binary(frames[:, :, x])
				nextPrices = self.conver_to_binary(nextPrices)

		print("Tail frames:")
		print(frames[len(frames)-3:], frames.shape)

		dates = np.array(dates) #convert to numpy array

		return (frames, dates, nextPrices)

	def normalize(self, arr, method, base = None):
		if method == 'basic':
			return self.basic_normalization(arr, base)
		elif method == 'around_zero':
			return self.around_zero_normalization(arr, base)