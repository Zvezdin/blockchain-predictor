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
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.realpath('neural'))
from neural_network import NeuralNetwork
from custom_deep_network import CustomDeepNetwork

import database_tools as db

globalModels = [CustomDeepNetwork()]

def loadDataset(filename):
	with open(filename, 'rb') as f:
		return pickle.load(f)

def randomizeDataset(dataset, labels):
	permutation = np.random.permutation(labels.shape[0])
	shuffled_dataset = dataset[permutation,:,:]
	shuffled_labels = labels[permutation]
	return shuffled_dataset, shuffled_labels

def run(dataset, models=None):

	#load the datasets
	rawDataset = loadDataset(dataset)

	dataset = {}
	labels = {}
	dates = {}

	for i, kind in enumerate(['train', 'valid', 'test']):
		dataset[kind] = rawDataset[i]['dataset']

		labels[kind] = rawDataset[i]['labels']

		dates[kind] = rawDataset[i]['dates']

	selectedModels = []

	dataset['train'], labels['train'] = randomizeDataset(dataset['train'], labels['train'])

	if models != None:
		for model in globalModels:
			if model.name in models:
				selectedModels.append(model)
	else: selectedModels = globalModels

	print("Starting to train and evaluate the following networks: ", [net.name for net in selectedModels])

	for model in selectedModels:
		model.train(dataset, labels)

	print("Trained the networks.")

	print("Running prediction on test dataset.")

	predictions = []


	for model in selectedModels:
		#TODO don't rely on the model's memory of the dataset.
		res = model.predict(None)

		p = dates['test'].argsort()

		predictions.append({'model': model.name, 'prediction': res[p], 'actual': labels['test'][p], 'dates': dates['test'][p]})

	print("Starting simulated trading to evaluate results")

	for pred in predictions:
		res, trades = simulateTrading(pred['prediction'], pred['actual'], 100.0)
		print("Got return %4f$ when starting with 100$ (%d trades) for predictions by model %s" % (res, trades, pred['model']))

	for pred in predictions:
		drawAccuracyGraph(pred['model'], pred['dates'], pred['prediction'], pred['actual'])

def simulateTrading(prediction, actual, startBalance):
	balance = startBalance #start with 100 of the stable currency

	crypto = False #what currency are we holding? crypto (predicted) or the stable one.

	lastPriceBoughtCrypto = 1

	timesTraded = 0

	for i, curr in enumerate(actual):
		if i >= len(prediction) - 1: break

		pred = prediction[i+1]

		if not crypto and pred > curr: #if the crypto price will raise and we're not on crypto
			crypto = True
			balance /= curr
			lastPriceBoughtCrypto = curr
			timesTraded += 1
		elif crypto and curr < pred: #if the crypto price will fall and we are holding crypto
			crypto = False
			balance *= curr
			timesTraded += 1

	if crypto:
		balance *= lastPriceBoughtCrypto #if we have finished with balance on crypto, revert last time we bought it.
		crypto = False

	return (balance, timesTraded)

def drawAccuracyGraph(name, dates, prediction, actual):
	plt.plot(dates, actual, label='Price', color='blue')
	plt.plot(dates, prediction, label='Predicted', color='red')
	plt.x = dates
	plt.title('Price vs Predicted on %s' % name)
	plt.legend(loc='upper left')
	plt.show()

if __name__ == "__main__": #if this is the main file, parse the command args
	parser = argparse.ArgumentParser(description="Module that loads given datasets and trains and evaluates one or more neural network models on that.")
	parser.add_argument('dataset', type=str, help="The filepath to the dataset/s.")
	parser.add_argument('--models', type=str, help="A list of the models that are going to be trained and evaluated. Default is all available.")



	args, _ = parser.parse_known_args()

	givenModels = args.models.split(',') if args.models else None

	run(args.dataset, givenModels)