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

def generateDataset(modelName, propertyNames, start=None, end=None):
	print("Generating dataset for properties ", propertyNames, "and using model", modelName, "for range", start, end)

	model = None

	#get the model instance
	for mod in models:
		if mod.name is modelName:
			mod = model

	if model is None:
		print("Error: Couldn't find model ", modelName)
		return

	properties = []

	#load the needed properties
	for prop in propertyNames:
		properties.append(db.loadData(chunkStore, prop, start, end, True))

	#feed the model the properties and let it generate
	dataset = model.generate(properties)

	#save the dataset to a file
	pickle.dump(dataset, open('dataset'), protocol=pickle.HIGHEST_PROTOCOL)


if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Generates a dataset by compiling generated data properties using a certain dataset model")
	parser.add_argument('--model', type=str, default='matrix', help='The name of the dataset model to use. Defaults to matrix.')
	parser.add_argument('--properties', type=str, default='openPrice,gasPrice', help='A list of the names of the properties to use, separated by a comma.')
	parser.add_argument('--start', type=str, default=None, help='The start date. YYYY-MM-DD-HH')
	parser.add_argument('--end', type=str, default=None, help='The end date. YYYY-MM-DD-HH')
	
	args, _ = parser.parse_known_args()
	print(args)

	generateDataset(args.model, args.properties.split(','), dateutil.parser.parse(args.start), dateutil.parser.parse(args.end))