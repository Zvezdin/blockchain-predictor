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

from dataset_models import modelObjects as models

from database import instance as db

save = True
debug = False

labelKey = 'closePrice'

def generateDataset(modelName, propertyNames, targetNames, labelsType='full', start=None, end=None, args = {}):
	print("Generating dataset for properties %s, targets %s, model %s and range from %s to %s." % (str(propertyNames), str(targetNames), modelName, str(start), str(end)))

	for arr in [propertyNames, targetNames]:
		while '' in arr:
			arr.remove('')

	model = None

	#get the model instance
	for mod in models:
		if mod.name == modelName:
			model = mod

	if model is None:
		print("Error: Couldn't find model ", modelName)
		return

	properties = []
	targets = []

	#make sure we don't go off bounds for any property
	start, end = db.getMasterInterval(propertyNames+targetNames, start, end)

	#load the needed properties
	for dataType, inputData in [('property', propertyNames), ('target', targetNames)]:
		for prop in inputData:
			data = db.get(prop, start=start, end=end)

			print(data.columns)
			#if type(data.iloc[0][prop]) == str: #if the property values have been encoded, decode them
			#	assert(False) #this shouldn't happen
				#print("Running numpy array Arctic workaround for prop %s..." % prop)
				#data[prop] = data[prop].apply(lambda x: db.decodeObject(x))

			if dataType == 'property':
				properties.append(data)
			if dataType == 'target':
				targets.append(data)

	for prop in properties:
		if len(properties[0]) != len(prop):
			raise ValueError("Error: Length mismatch in the data properties.")

	#feed the model the properties and let it generate
	dataset, dates, nextPrices, targetNorms =  model.generate(properties, targets, args)

	labels = nextPrices
	
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
		#try:
		with open(filename, 'wb') as f:
			pickle.dump(data, f, pickle.HIGHEST_PROTOCOL)
		#except Exception as e:
		#	print('Unable to save data to', filename, ':', e)

def run(model, properties, targets, filename, start=None, end=None, ratio=[1], shuffle=False, overwrite=False, args={}):
	if os.path.isfile(filename) and not overwrite:
		print("Filename %s already exists and the overwrite flag is not set!" % filename)
		return

	db.open()

	if type(properties) != list:
		properties = [properties]
	if type(targets) != list:
		targets = [targets]
	

	#generate the dataset
	dataset = generateDataset(model, properties, targets, start=start, end=end, args=args)

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

	db.close()

def init():
	parser = argparse.ArgumentParser(description="Generates a dataset by compiling generated data properties using a certain dataset model")
	parser.add_argument('--model', type=str, default='matrix', help='The name of the dataset model to use. Defaults to matrix.')
	parser.add_argument('properties', type=str, default='openPrice,closePrice,gasPrice', help='A list of the names of the properties to use, separated by a comma.')
	parser.add_argument('targets', type=str, default='highPrice', help='A list of target property names, separated by a comma.')
	parser.add_argument('--start', type=str, default=None, help='The start date. YYYY-MM-DD-HH')
	parser.add_argument('--end', type=str, default=None, help='The end date. YYYY-MM-DD-HH')
	parser.add_argument('--filename', type=str, default=None, help='The target filename / dir to save the pickled dataset to. Defaults to "data/dataset.pickle"')
	parser.add_argument('--overwrite', dest='overwrite', action='store_true', help="If the filename already exists, overwrite it.")
	parser.add_argument('--ratio', type=str, default='1', help='On how many fragments to split the main dataset. For example, "1:2:3" will create three datasets with sizes proportional to what given.')
	parser.add_argument('--shuffle', dest='shuffle', action="store_true", help="Shuffle the generated dataset and labels.")
	parser.set_defaults(shuffle=False)
	parser.set_defaults(overwrite=False)

	args, _ = parser.parse_known_args()

	if len(_) != 0:
		raise ValueError("Provided flags %s cannot be understood." % str(_))

	if args.filename == None:
		filename = "data/dataset_" + str(args.start) + "-" + str(args.end) + ".pickle"
	else: filename = args.filename

	start = args.start
	end = args.end

	start = dateutil.parser.parse(start) if start is not None else None
	end = dateutil.parser.parse(end) if end is not None else None

	try:
		ratio = [int(x) for x in args.ratio.split(':')]
	except ValueError:
		print("Error while reading the given ratio. Did you format it in the correct way?")
		return

	run(args.model, args.properties.split(','), args.targets.split(','), filename, start=start, end=end, ratio=ratio, shuffle=args.shuffle, overwrite=args.overwrite)

if __name__ == "__main__":
	init()
