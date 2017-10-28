import pandas as pd
import numpy as np

from dataset_model import DatasetModel


class MatrixModel(DatasetModel):
	def __init__(self):
		self.name="matrix"
		self.requires=[]

	def generate(self, properties, args = {'window': 100, 'normalize': True}):
		if not properties: return

		#blacklist = []

		#for prop in properties:
		#	if prop.columns.contains('stickPrice'):
		#		blacklist.extend('openPrice', 'closePrice') #if we have stick price, we want to avoid open and close prices in the end dataset.

		data = properties[0] #first property

		for i in range(1, len(properties)):
			data = pd.merge(data, properties[i]) #merge all properties in one dataframe

		allDates = data['date']

		data.drop('date', axis=1, inplace=True)

		print("Head:")
		print(data.head(5))
		print("Tail:")
		print(data.tail(5))

		stickAlgorithm = False
		try:
			priceIndex = data.columns.get_loc('stickPrice')
			stickAlgorithm = True
		except KeyError:
			priceIndex = data.columns.get_loc('closePrice')


		window_size = 10

		if 'window' in args: #if given length of moving window
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

		if not 'normalize' in args or args['normalize']: #if no arg given, default to normalize.
			print("Normalizing...")
			for x in range(len(properties)):
				if stickAlgorithm and x != priceIndex: #price is normalized via another algorithm
					frames[:, :, x] = self.basic_normalization(frames[:, :, x])

		#normalize the price using a candle stick algorithm
		if stickAlgorithm and priceIndex >= 0:
			for i, frame in enumerate(frames):
				#find the delta - distance between min and max price to normalize on.
				size = frame[:, priceIndex].max() - frame[:, priceIndex].min()

				if size != 0:
					frame[:, priceIndex] = (frame[:, priceIndex] + size) / (size*2) #normalize to interval [0,1]
					nextPrices[i] = min((nextPrices[i] + size) / (size*2), 1.0) #normalize the predicted price as well. It may go off bounds, so squash it.
		else: #normalize the pries the standart way
			nextPrices = self.basic_normalization(nextPrices)
		print("Tail frames:")
		print(frames[len(frames)-3:], frames.shape)

		dates = np.array(dates) #convert to numpy array

		return (frames, dates, nextPrices)