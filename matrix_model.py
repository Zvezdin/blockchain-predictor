import pandas as pd
import numpy as np

from dataset_model import DatasetModel


class MatrixModel(DatasetModel):
	def __init__(self):
		self.name="matrix"
		self.requires=[]

	def generate(self, properties):
		if not len(properties): return

		data = properties[0]
		for i in range(1, len(properties)):
			data = pd.merge(data, properties[i])

		print(data)

		allDates = data['date']

		data.drop('date', axis=1, inplace=True)

		print(properties, data)
		print()
		print(data.values)

		window_size = 3

		vals = data.values

		frames = np.ndarray([len(vals)-window_size, window_size, len(properties)])

		dates = []
		
		#sliding window over the values. Step is 1.
		for i in range(len(vals)):
			#if we've reached the end
			if i + window_size >= len(vals): break
			
			#create a frame using sliding window
			frames[i] = vals[i:i+window_size]

			dates.append(allDates.iloc[i+window_size])

		print(frames, frames.shape)

		for x in range(len(properties)):
			frames[:, :, x] = self.basic_normalization(frames[:, :, x])

		#frames[:, :, 0] = (frames[:, :, 0] - np.mean(frames[:, :, 0])) / np.std(frames[:, :, 0])

		print(frames, frames.shape)

		print(dates)

		return (frames, dates)