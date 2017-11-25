import pandas as pd
import numpy as np

from dataset_model import DatasetModel

debug = True

class StackedModel(DatasetModel):

	def __init__(self):
		self.name="stacked"
		self.requires=[]

	def generate(self, properties, args = {}):
		if not properties: return

		#argument defaults
		args.setdefault('window', 104)
		args.setdefault('normalize', True)
		args.setdefault('target', ['highPrice_rel'])
		args.setdefault('localNormalize', [None])
		args.setdefault('defaultNormalization', 'basic')
		args.setdefault('normalization', {'highPrice_rel': 'around_zero'})
		args.setdefault('binary', False)
		args.setdefault('blacklistTarget', True)
		args.setdefault('invert', False)

		args.setdefault('width', 10)
		args.setdefault('height', 1)
		args.setdefault('flexible', True) #if the height of the image can be expanded if the chosen properties don't fit

		propertyValues = np.ndarray((properties[0].shape[0], args['width'], args['height']))
		targetData = None

		currentRow = 0
		currentCol = 0
		usedSpace = np.zeros((args['width'], args['height']), dtype=bool)

		for i in range(0, len(properties)):
			prop = properties[i].drop('date', axis=1)

			if len(prop.columns) != 1:
				raise ValueError("The received property contains more than one data column!", prop.columns)
			propName = prop.columns[0]

			print("Processing property %s." % propName)

			v = prop.values.swapaxes(0, 1)[0, :] #single list of the property values.

			if debug: print("Debug", v.shape)

			if type(v[0]) == np.ndarray: #matrix model doesn't support multi dim value arrays. Flatten them.
				v = np.array([x for x in v]) #currently, v is a np array of np arrays. This is to force everything to one large ndarray
				v = v.swapaxes(1,2) # swap the prop value count with the width.

			if len(v.shape) == 1: #if it is a single value property. make it 3d
				v = np.reshape(v, (v.shape[0], 1, 1))

			if debug: print("Debug v2", v.shape)

			#we have the property values. Normalize or not.
			if args['normalize']:
				normalization = args['normalization'].get(propName, args['defaultNormalization'])
				if propName not in args['localNormalize']: #local normalization happens via another way
					print("Globally normalizing property %s with method %s." % (propName, normalization))
					v = self.normalize(v, normalization)

			if args['binary']:
				print("Converting data to binary! May cause issues.")
				v = self.conver_to_binary(v)

			#add to our target
			if propName in args['target']:
				flattened = v.flatten(order='C') #the outputs cannot be spatial
				flattened = flattened.reshape((flattened.shape[0], 1))
				if targetData is None:
					targetData = flattened
				else:
					targetData = np.append(flattened, v, axis=1)

				if args['blacklistTarget']:
					continue #skip the property

			placed = False

			while not placed:
				if v.shape[1] > propertyValues.shape[1]: #not possible to fit
					raise ValueError("Cannot fit property with width %d into space with width %d!" % (v.shape[1], propertyValues.shape[1]))

				if currentRow + v.shape[1] > propertyValues.shape[1]: #can't fit horizontally
					currentRow = 0
					currentCol += 1 #break on new line. Should fit now.
					
					if debug: print("Property couldn't fit horizontally, went on a new row")

				while currentCol + v.shape[2] > propertyValues.shape[2]: #it can't fit vertically, resize it
					if not args['flexible']:
						raise ValueError("Cannot fit property with at column #%d with height %d into space with height %d!" % (currentCol, v.shape[2], propertyValues.shape[2]))
					else:
						propertyValues = self.appendColumn3d(propertyValues)
						usedSpace = self.appendColumn2d(usedSpace)
						if debug: print("Property couldn't fit vertically, added a column")

				if not self.canPlacePropertyInSpace(propertyValues, v, usedSpace, currentRow, currentCol): #just can't fit
					currentRow += 1 #the space is used, move up a row
					if debug: print("Space for property is used, moved up a row")
				else:
					self.placePropertyInSpace(propertyValues, v, usedSpace, currentRow, currentCol)
					if debug:
						print("Placed property %s with shape %s at [%d,%d]" % (propName, str(v.shape), currentRow, currentCol))
						print(usedSpace)
					placed = True

		allDates = properties[0]['date']

		if debug: print("Shape of property values is %s." % str(propertyValues.shape))

		print(targetData, targetData.shape)

		window_size = args['window']

		vals = propertyValues

		frames = np.ndarray([vals.shape[0]-window_size, window_size, vals.shape[1], vals.shape[2]], dtype=np.float64) #shape is N, width, height, window_size

		nextPrices = np.ndarray((frames.shape[0], targetData.shape[1])) #len of samples with targets, num of targets

		dates = []
		
		#sliding window over the values. Step is 1.
		for i in range(len(vals)):
			#if we've reached the end
			if i + window_size >= vals.shape[0]: break
			
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

	def canPlacePropertyInSpace(self, space, prop, usedSpace, row, col):
		return usedSpace[row: row+prop.shape[1], col: col+prop.shape[2]].sum() == 0

	def placePropertyInSpace(self, space, prop, usedSpace, row, col):
		if self.canPlacePropertyInSpace(space, prop, usedSpace, row, col): #if the space is free
			try:
				space[:, row: row+prop.shape[1], col: col+prop.shape[2]] = prop
				usedSpace[row: row+prop.shape[1], col: col+prop.shape[2]] = True
			except ValueError:
				return False
			return True
		else:
			return False

	def appendColumn3d(self, arr):
		new = np.zeros((arr.shape[0], arr.shape[1], arr.shape[2]+1), dtype = arr.dtype)
		new[:, :, :-1] = arr

		return new

	def appendColumn2d(self, arr):
		new = np.zeros((arr.shape[0], arr.shape[1]+1), dtype = arr.dtype)
		new[:, :-1] = arr

		return new
