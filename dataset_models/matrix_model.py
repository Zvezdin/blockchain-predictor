import pandas as pd
import numpy as np

from dataset_model import DatasetModel


class MatrixModel(DatasetModel):
	def __init__(self):
		self.name="matrix"
		self.requires=[]

	def generate(self, properties, args = {}):
		if not properties: return

		#argument defaults
		if 'window' not in args:
			args['window'] = 104
		if 'normalize' not in args:
			args['normalize'] = True
		if 'target' not in args:
			args['target'] = ['highPrice_rel']
		if 'localNormalize' not in args:
			args['localNormalize'] = [None]#['stickPrice']
		if 'defaultNormalization' not in args:
			args['defaultNormalization'] = 'basic'
		if 'normalization' not in args:
			args['normalization'] = {'highPrice_rel': 'around_zero'}
		if 'binary' not in args:
			args['binary'] = False
		if 'blacklistTarget' not in args:
			args['blacklistTarget'] = True
		if 'invert' not in args:
			args['invert'] = False
		args.setdefault('normalizationLevel', 'pixel') #or 'layer', 'pixel'
		args.setdefault('normalizationStd', 'local') #or 'global'

		propertyValues = None
		targetData = None

		for i in range(0, len(properties)):
			prop = properties[i].drop('date', axis=1)

			if len(prop.columns) != 1:
				raise ValueError("The received property contains more than one data column!")
			propName = prop.columns[0]

			print("Processing property %s." % propName)

			v = prop.values.swapaxes(0, 1)[0, :] #single list of the property values.

			print("Debug", v.shape)

			if type(v[0]) == np.ndarray: #matrix model doesn't support multi dim value arrays. Flatten them.
				print("Warning: Matrix model does not supoort property %s. It will be flattened." % propName)
				v = np.array([x.flatten(order='C') for x in v])

			if len(v.shape) == 1:
				v = np.reshape(v, (v.shape[0], 1))

			#we have the property values. Normalize or not.
			if args['normalize'] and args['normalizationLevel'] == 'property':
				normalization = args['normalization'].get(propName, args['defaultNormalization'])
				if propName not in args['localNormalize']: #local normalization happens via another way
					print("Globally normalizing property %s with method %s." % (propName, normalization))
					v = self.normalize(v, normalization)

			if args['binary']:
				print("Converting data to binary! May cause issues.")
				v = self.conver_to_binary(v)

			#add to our target
			if propName in args['target']:
				if targetData is None:
					targetData = v
				else:
					targetData = np.append(targetData, v, axis=1)

				if args['blacklistTarget']:
					continue #skip the property

			#add to our dataset
			if propertyValues is None:
				propertyValues = v
			else:
				propertyValues = np.append(propertyValues, v, axis=1)
			print(propertyValues.shape)

		allDates = properties[0]['date']


		if args['normalize'] and args['normalizationLevel'] == 'pixel':
			meanFrame = np.ndarray((propertyValues.shape[1]))
			stdFrame = np.ndarray(meanFrame.shape)

			for i in range(propertyValues.shape[1]):
				meanFrame[i] = np.mean(propertyValues[:, i])
				stdFrame[i] = np.std(propertyValues[:, i])
			for i in range(propertyValues.shape[0]):
				propertyValues[i, :] = propertyValues[i, :] - meanFrame

			if args['normalizationStd'] == 'local':
				propertyValues = np.divide(propertyValues, stdFrame, where=stdFrame!=0)
			elif args['normalizationStd'] == 'global':
				propertyValues = propertyValues / np.std(propertyValues)
			else:
				raise ValueError("Unknown setting for normalizationStd - %s" % (args['normalizationStd']))

			print("Generating target data with mean %d" % np.mean(targetData))

			targetData = targetData - np.mean(targetData)
			targetData = targetData / np.std(targetData)


		print(targetData)

		window_size = args['window']

		vals = propertyValues

		frames = np.ndarray([len(vals)-window_size, window_size, vals.shape[1]], dtype=np.float64) #shape is N, win_size, prop_count

		nextPrices = np.ndarray((frames.shape[0], targetData.shape[1])) #len of samples with targets, num of targets

		dates = []
		
		#sliding window over the values. Step is 1.
		for i in range(len(vals)):
			#if we've reached the end
			if i + window_size >= len(vals): break
			
			#create a frame using sliding window 
			frame = vals[i:i+window_size]

			frames[i] = frame

			for targetI in range(targetData.shape[1]):
				nextPrices[i, targetI] = targetData[i+window_size][targetI] #get the price that should be predicted for this frame

			dates.append(allDates.iloc[i+window_size-1])

		print("Head frames:")
		print(frames[:3], frames.shape)


		print("Tail frames:")
		print(frames[len(frames)-3:], frames.shape)

		print("Labels:")
		print(nextPrices[-15:], nextPrices.shape)

		dates = np.array(dates) #convert to numpy array

		if args['invert']:
			frames = 1-frames

		return (frames, dates, nextPrices)
