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
			args['window'] = 24
		if 'normalize' not in args:
			args['normalize'] = True
		if 'target' not in args:
			args['target'] = ['highPrice_rel']
		if 'localNormalize' not in args:
			args['localNormalize'] = [None]#['stickPrice']
		if 'defaultNormalization' not in args:
			args['defaultNormalization'] = 'around_zero'
		if 'normalization' not in args:
			args['normalization'] = {'labels': args['defaultNormalization']}
		if 'binary' not in args:
			args['binary'] = False
		if 'blacklistTarget' not in args:
			args['blacklistTarget'] = False
		if 'invert' not in args:
			args['invert'] = False

		#for target in args['target']:
		targetData = data[args['target']] #get the target columns

		print(targetData)

		if args['blacklistTarget']: #drop the target from the dataset
			data.drop(args['target'], axis=1, inplace=True)
		
		#this method can backfire, so it is disabled temporairly
			#remove any zero price deltas - we can't predict based on that
		#data.drop(data[data[data.columns[args['price']]] == 0].index, inplace=True)

		print("Head:")
		print(data.head(5))
		print("Tail:")
		print(data.tail(5))

		window_size = args['window']

		vals = data.values

		frames = np.ndarray([len(vals)-window_size, window_size, data.shape[1]], dtype=np.float64)

		nextPrices = np.ndarray((frames.shape[0], targetData.shape[1])) #len of samples with targets, num of targets

		dates = []
		
		#sliding window over the values. Step is 1.
		for i in range(len(vals)):
			#if we've reached the end
			if i + window_size >= len(vals): break
			
			#create a frame using sliding window 
			frame = vals[i:i+window_size]

			frames[i] = frame

			for colI, col in enumerate(targetData):
				nextPrices[i, colI] = targetData[col].iloc[i+window_size] #get the price that should be predicted for this frame

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
				normalization.append(args['defaultNormalization'])

		if args['normalize']:
			print("Normalizing...")
			for x in range(data.shape[1]):
				if x not in localNormalize: #local normalization happens via another way
					print("Globally normalizing property %d with method %s." % (x, normalization[x]))
					frames[:, :, x] = self.normalize(frames[:, :, x], normalization[x])

			#if we want the whole set to be globally normalized at once
			#frames = self.normalize(frames, 'basic')

			#normalize the property and the predicted price locally
			for x in localNormalize:
				print("Locally normalizing property %d with method %s." % (x, normalization[x]))
				for i, frame in enumerate(frames):
					#due to recent changes, local normalization of target is not supported

					#if x == priceIndex: #normalize the price if it walls with this local property
					#	nextPrices[i] = min(max(self.normalize(nextPrices[i], normalization[x], frame[:, x]), 0), 1)

					if np.min(frame[:, x]) == 0 and np.max(frame[:, x]) == 0:
						print("Empty dataset at index %i." % i)

					frame[:, x] = self.normalize(frame[:, x], normalization[x])

			#normalize the targets
			for i in range(nextPrices.shape[1]):
				nextPrices[:, i] = self.normalize(nextPrices[:, i], args['normalization']['labels'])

		if args['binary']:
			print("Converting data to binary! May cause issues.")
			for x in range(data.shape[1]):
				frames[:, :, x] = self.conver_to_binary(frames[:, :, x])
			nextPrices = self.conver_to_binary(nextPrices)

		print("Tail frames:")
		print(frames[len(frames)-3:], frames.shape)

		print("Labels:")
		print(nextPrices[-15:], nextPrices.shape)

		dates = np.array(dates) #convert to numpy array

		if args['invert']:
			frames = 1-frames

		return (frames, dates, nextPrices)

	def normalize(self, arr, method, base = None):
		if method == 'basic':
			return self.basic_normalization(arr, base)
		elif method == 'around_zero':
			return self.around_zero_normalization(arr, base)
