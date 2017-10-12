import sys
from datetime import timezone, timedelta, datetime as dt
import time
import dateutil.parser
import argparse
import pickle

import pandas as pd
from arctic.date import DateRange

from dataset_model import DatasetModel

from matrix_model import MatrixModel
import database_tools as db



chunkStore = db.getChunkstore()

models = [MatrixModel()]

save = False

def generateDataset(modelName, propertyNames, filename, start=None, end=None):
	print("Generating dataset for properties ", propertyNames, "and using model", modelName, "for range", start, end)

	model = None

	#get the model instance
	for mod in models:
		if mod.name is modelName:
			model = mod

	if model is None:
		print("Error: Couldn't find model ", modelName)
		return

	properties = []

	#make sure we don't go off bounds for any property
	start, end = db.getMasterInterval(chunkStore, propertyNames, start, end)

	#load the needed properties
	for prop in propertyNames:
		properties.append(db.loadData(chunkStore, prop, start, end, True))

	#feed the model the properties and let it generate
	return model.generate(properties)

def generateLabels(ticks, labelsType):
	#todo
	return

def saveDataset(filename, dataset, labels):
	if save:
		#save the dataset to a file
		data = {
			'dataset': dataset,
			'labels': labels
		}
		try:
			with open(filename, 'wb') as f:
				pickle.dump(data, f, pickle.HIGHEST_PROTOCOL)
		except Exception as e:
			print('Unable to save data to', filename, ':', e)

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Generates a dataset by compiling generated data properties using a certain dataset model")
	parser.add_argument('--model', type=str, default='matrix', help='The name of the dataset model to use. Defaults to matrix.')
	parser.add_argument('--properties', type=str, default='openPrice,gasPrice', help='A list of the names of the properties to use, separated by a comma.')
	parser.add_argument('--start', type=str, default=None, help='The start date. YYYY-MM-DD-HH')
	parser.add_argument('--end', type=str, default=None, help='The end date. YYYY-MM-DD-HH')
	parser.add_argument('--filename', type=str, default="data/dataset.pickle", help='The target filename / dir to save the pickled dataset to. Defaults to "data/dataset.pickle"')
	parser.add_argument('--labels', type=str, default='boolean', choices=['boolean', 'full'], help='What kind of labels should be generated for each dataframe. "boolean" contains only the sign of the course, "full" consists of all other target predictions.')

	args, _ = parser.parse_known_args()
	print(args)

	start = dateutil.parser.parse(args.start) if args.start is not None else None
	end = dateutil.parser.parse(args.end) if args.end is not None else None

	dataset = generateDataset(args.model, args.properties.split(','), args.filename, start, end)
	labels = generateLabels(None, args.labels)

	if save: saveDataset(dataset, labels)
