import pandas as pd
import numpy as np

from dataset_model import DatasetModel


class MatrixModel(DatasetModel):
	def __init__(self):
		self.name="matrix"
		self.requires=[]

	def generate(self, properties, args = {'window': 100, 'regularization': True}):
		if not properties: return

		data = properties[0] #first property
		for i in range(1, len(properties)):
			data = pd.merge(data, properties[i]) #merge all properties in one dataframe

		allDates = data['date']

		data.drop('date', axis=1, inplace=True)

		print(data.head(5))
		print()
		print(data.tail(5))

		window_size = 100

		if 'window' in args: #if given length of moving window
			window_size = args['window']

		vals = data.values

		frames = np.ndarray([len(vals)-window_size+1, window_size, len(properties)], dtype=np.float32)

		dates = []
		
		#sliding window over the values. Step is 1.
		for i in range(len(vals)):
			#if we've reached the end
			if i + window_size > len(vals): break
			
			#create a frame using sliding window
			frames[i] = vals[i:i+window_size]

			dates.append(allDates.iloc[i+window_size-1])

		print(frames[:3], frames.shape)

		if not 'normalize' in args or args['normalize']: #if no arg given, default to normalize.
			print("Normalizing...")
			for x in range(len(properties)):
				frames[:, :, x] = self.basic_normalization(frames[:, :, x])

		print(frames[len(frames)-3:], frames.shape)

		dates = np.array(dates) #convert to numpy array

		return (frames, dates)