import sys
import os
from datetime import timezone, timedelta, datetime as dt
import time
import dateutil.parser
import argparse
import pickle
import io
import codecs
import math

import pandas as pd
from arctic.date import CLOSED_OPEN
import numpy as np

sys.path.insert(0, os.path.realpath('dataset_models'))
from dataset_model import DatasetModel

from matrix_model import MatrixModel
from stacked_model import StackedModel
import database_tools as db



chunkStore = db.getChunkstore()

models = [MatrixModel(), StackedModel()]

save = True
debug = False

labelKey = 'closePrice'

def generateDataset(modelName, propertyNames, labelsType, start=None, end=None, args = {}, preprocess = {}):
	print("Generating dataset for properties ", propertyNames, "and using model", modelName, "for range", start, end)

	while '' in propertyNames:
		propertyNames.remove('')

	model = None

	#get the model instance
	for mod in models:
		if mod.name == modelName:
			model = mod

	if model is None:
		print("Error: Couldn't find model ", modelName)
		return

	properties = []

	#make sure we don't go off bounds for any property
	start, end = db.getMasterInterval(chunkStore, propertyNames, start, end)

	#load the needed properties
	for prop in propertyNames:
		data = db.loadData(chunkStore, prop, start, end, True, CLOSED_OPEN)

		if type(data.iloc[0][prop]) == str: #if the property values have been encoded, decode them
			print("Running numpy array Arctic workaround for prop %s..." % prop)
			data[prop] = data[prop].apply(lambda x: db.decodeObject(x))

		if prop in preprocess:
			settings = preprocess[prop]
			if 'scale' in settings:
				if settings['scale'] == 'log2':
					scaleF = np.log2
				elif settings['scale'] == 'log10':
					scaleF = np.log10
				else:
					raise ValueError("Unsupported scale type %s for preprocessing of property %s!" % (settings['scale'], prop))

				def scale(val):
					global globalMin

					if globalMin < 0: #if we have relative values
						val -= globalMin #turn all negatives to positives

					val = scaleF(val)
					val[val<0] = 0 #log if 0 is -inf

					return val
			else:
				scale = lambda x: x #no scaling

			xAxis = ':'
			yAxis = ':'
			
			if 'slices' in settings:
				xAxis, yAxis = settings['slices']

			strToSlice = lambda string: slice(*map(lambda x: int(x.strip()) if x.strip() else None, string.split(':')))

			xAxis = strToSlice(xAxis)
			yAxis = strToSlice(yAxis)

			print("Slicing data by %s and %s." % (str(xAxis), str(yAxis)))

			data[prop] = data[prop].apply(lambda x: x[yAxis, xAxis]) # trim

			global globalMin #we need the minimum single value, to see if the property is realtive or not
			globalMin = 0

			def findMin(x):
				global globalMin
				globalMin = min(globalMin, np.min(x))
				return x

			data[prop].apply(findMin)

			data[prop] = data[prop].apply(lambda x: scale(x)) # scale

		properties.append(data)

	for prop in properties:
		if len(properties[0]) != len(prop):
			raise ValueError("Error: Length mismatch in the data properties.")

	#feed the model the properties and let it generate
	dataset, dates, nextPrices, targetNorms =  model.generate(properties, args)

	labels, dates = generateLabels(dates, nextPrices, db.loadData(chunkStore, labelKey, start, None, True), labelsType)

	if len(dataset) != len(labels): #if we have a length mismatch, probably due to insufficient data for the last label
		print("Mismatch in lengths of dataset and labels, removing excessive entries")
		dataset = dataset[:len(labels)] #remove dataframes for which we have no labels

	package = {
		'dataset': dataset,
		'dates': dates,
		'labels': nextPrices,
		'normalization': targetNorms
	}

	return package

def generateLabels(dates, nextPrices, ticks, labelsType):
	"""Generates dataset labels for each passed date, getting data from ticks. dates MUST BE CHRONOLOGICALLY ORDERED. """
	if labelsType == "boolean":
		labels = []
		i=0
		
		indices = ticks.index.values

		for date in dates:
			while ticks.get_value(indices[i], 'date') != date:
				i+=1

			try:
				currPrice = ticks.get_value(indices[i], 'closePrice')
				nextPrice = ticks.get_value(indices[i+1], 'closePrice')
			except (ValueError, IndexError, KeyError):
				print("Failed to load the date after", date, ". Probably end of data. Will remove one dataset entry.")
				dates = dates[:len(labels)] #keep only the labeled dates
				break
			if debug:
				print(ticks.loc[indices[i] : indices[i+1]])

			label = nextPrice > currPrice
			
			if debug:
				print("Label for dataframe at %s is %s for prices curr/next : %s and %s" % (date, label, currPrice, nextPrice) )
			labels.append([label])

		#make numpy array
		labels = np.array(labels)
		
		return (labels, dates)

	elif labelsType == 'full': #nothing to do, the prices are already given and are normalized
		return (nextPrices, dates)

def randomizeDataset(dataset):
	main = dataset['dataset']
	permutation = np.random.permutation(main)

	for key in dataset:
		if type(dataset[key]) != np.ndarray or len(dataset[key]) != len(main):
			print("Unable to shuffle key %s. Leaving it as is." % key)
			continue
		dataset[key] = dataset[key][permutation]
	return dataset

def saveDataset(filename, data):
	if save:
		#save the dataset to a file
		try:
			with open(filename, 'wb') as f:
				pickle.dump(data, f, pickle.HIGHEST_PROTOCOL)
		except Exception as e:
			print('Unable to save data to', filename, ':', e)

def run(model, properties, start, end, filename, labels, ratio, shuffle, args, preprocess = {}):
	start = dateutil.parser.parse(start) if start is not None else None
	end = dateutil.parser.parse(end) if end is not None else None

	try:
		ratio = [int(x) for x in ratio.split(':')]
	except ValueError:
		print("Error while reading the given ratio. Did you format it in the correct way?")
		return

	#generate the dataset
	dataset = generateDataset(model, properties.split(','), labels, start, end, args, preprocess)

	if shuffle:
		#randomize it
		dataset = randomizeDataset(dataset)
		print("Randomized dataset and labels.")

	if len(ratio) == 1:
		data = dataset
	else:
		data = []

		split = [] #the lenghts of the dataset pieces

		mainLen = len(dataset['dataset'])
		for rat in ratio:
			split.append( int((rat * mainLen) / np.sum(ratio)) ) #calculate the length by keeping the given ratio

		print(split, ratio)

		index = 0

		for i, spl in enumerate(split):
			end = (spl + index) if i != len(split) -1 else None #because of integer division, add anything left on the last iteration

			newDataset = {}

			for key in dataset:
				if type(dataset[key]) != np.ndarray or len(dataset[key]) != mainLen:
					newDataset[key] = dataset[key]
					print("Unable to split key %s. Leaving it as is." % key)
				else:
					newDataset[key] = dataset[key][index:end]
			data.append(newDataset)

			index += spl

	#save it
	if save:
		saveDataset(filename, data)
		print("saved dataset and labels as %a." % filename)

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Generates a dataset by compiling generated data properties using a certain dataset model")
	parser.add_argument('--model', type=str, default='matrix', help='The name of the dataset model to use. Defaults to matrix.')
	parser.add_argument('properties', type=str, default='openPrice,closePrice,gasPrice', help='A list of the names of the properties to use, separated by a comma.')
	parser.add_argument('--start', type=str, default=None, help='The start date. YYYY-MM-DD-HH')
	parser.add_argument('--end', type=str, default=None, help='The end date. YYYY-MM-DD-HH')
	parser.add_argument('--filename', type=str, default=None, help='The target filename / dir to save the pickled dataset to. Defaults to "data/dataset.pickle"')
	parser.add_argument('--labels', type=str, default='full', choices=['boolean', 'full'], help='What kind of labels should be generated for each dataframe. "boolean" contains only the sign of the course, "full" consists of all other target predictions.')
	parser.add_argument('--ratio', type=str, default='1', help='On how many fragments to split the main dataset. For example, "1:2:3" will create three datasets with sizes proportional to what given.')
	parser.add_argument('--shuffle', dest='shuffle', action="store_true", help="Shuffle the generated dataset and labels.")
	parser.set_defaults(shuffle=False)

	args, _ = parser.parse_known_args()

	if args.filename == None:
		filename = "data/dataset_" + str(args.start) + "-" + str(args.end) + ".pickle"
	else: filename = args.filename

	run(args.model, args.properties, args.start, args.end, filename, args.labels, args.ratio, args.shuffle, {})
