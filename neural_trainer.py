import sys
import os
from datetime import timezone, timedelta, datetime as dt
import time
import dateutil.parser
import argparse
import pickle

import pandas as pd
from arctic.date import CLOSED_OPEN
import numpy as np

sys.path.insert(0, os.path.realpath('neural'))
from neural_network import NeuralNetwork
from custom_deep_network import CustomDeepNetwork

import database_tools as db

globalModels = [CustomDeepNetwork()]

def loadDataset(filename):
	with open(filename, 'rb') as f:
		return pickle.load(f)

def run(dataset, models=None):

	#load the datasets
	rawDataset = loadDataset(dataset)

	dataset = {}
	labels = {}

	for i, kind in enumerate(['train', 'valid', 'test']):
		dataset[kind] = rawDataset[i]['dataset']

		labels[kind] = rawDataset[i]['labels']

	selectedModels = []

	if models != None:
		for model in globalModels:
			if model.name in models:
				selectedModels.append(model)
	else: selectedModels = globalModels

	print("Starting to train and evaluate the following networks: ", [net.name for net in selectedModels])

	for model in selectedModels:
		model.train(dataset, labels)

if __name__ == "__main__": #if this is the main file, parse the command args
	parser = argparse.ArgumentParser(description="Module that loads given datasets and trains and evaluates one or more neural network models on that.")
	parser.add_argument('dataset', type=str, help="The filepath to the dataset/s.")
	parser.add_argument('--models', type=str, help="A list of the models that are going to be trained and evaluated. Default is all available.")



	args, _ = parser.parse_known_args()

	givenModels = args.models.split(',') if args.models else None

	run(args.dataset, givenModels)