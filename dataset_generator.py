import sys
from datetime import timezone, timedelta, datetime as dt
import time
import dateutil.parser
import argparse

import pandas as pd
from arctic.date import DateRange

#import database_tools as db



#chunkStore = db.getChunkstore()

def generateDataset(model, properties, strat=None, end=None):
	print("Generating dataset for properties ", properties, "and using model", model)

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Generates a dataset by compiling generated data properties using a certain dataset model")
	parser.add_argument('--model', type=str, default='matrix', help='The name of the dataset model to use. Defaults to matrix.')
	parser.add_argument('--properties', type=str, default='openPrice,gasPrice', help='A list of the names of the properties to use, separated by a comma.')
	parser.add_argument('--start', type=str, default=None, help='The start date. YYYY-MM-DD-HH')
	parser.add_argument('--end', type=str, default=None, help='The end date. YYYY-MM-DD-HH')
	
	args, _ = parser.parse_known_args()
	print(args)

	generateDataset(args.model, args.properties.split(','), args.start, args.end)