import pandas as pd
from datetime import timezone, timedelta, datetime as dt
import time

import sys
import os
from Naked.toolshed.shell import execute_js, muterun_js

from database_tools import *

from propertyGasPrice import *
from property import *

chunkStore = getChunkstore()


properties = [PropertyGasPrice()]
propChunkSize = 'M'


def generateProperties():
	values = {} #a dict that holds an array of the returned values for each property

	for prop in properties:
		values[prop.name]= []

	def tickHandler(data, date):
		for prop in properties:
			block, tx, course = data
			val = prop.processTick(block, tx, course)
			print("Got value", val, "for property", prop.name)
			values[prop.name].append({'date': date, prop.name: val})

	forEachTick(tickHandler)

	for prop in properties:
		df = getDataFrame(values[prop.name])
		print("Saving prop " + prop.name+ " with values ", df)
		saveData(chunkStore, prop.name, values[prop.name], propChunkSize)



def forEachTick(callback, tSeconds = 5*60, cache = 10):
	t = timedelta(seconds = tSeconds)
	cacheT = timedelta(seconds = cache*tSeconds)

	#get the time interval where we have all needed data
	t1, t2, t3 = loadMetadata(chunkStore, blKey)['start'], loadMetadata(chunkStore, txKey)['start'], loadMetadata(chunkStore, tickKey)['start']

	start = max(t1, t2)
	start = max(start, t3)

	t1, t2, t3 = loadMetadata(chunkStore, blKey)['end'], loadMetadata(chunkStore, txKey)['end'], loadMetadata(chunkStore, tickKey)['end']

	end = min(t1, t2)
	end = min(end, t3)

	currentStart = start
	currentEnd = currentStart + t

	loadedStart = currentStart
	loadedEnd = min(loadedStart + cacheT, end)

	print("Starting generating properties from", start, "to", end)

	while True:
		print("Loading data for dates", loadedStart, loadedEnd)
		data = loadDataForTick(chunkStore, loadedStart, loadedEnd) #load a large portion of the data and cache it in the RAM.

		while currentEnd <= loadedEnd: #break that large portion of data in smaller intervals that are passed to the callback
			print("Processing data from", currentStart, "to", currentEnd)
			callback([subsetByDate(data[x], currentStart, currentEnd) for x in range(len(data))], currentEnd)
			currentStart += t #sliding window
			currentEnd = currentStart + t

		loadedStart += cacheT #sliding window over the timeline
		loadedEnd = min(loadedStart + cacheT, end)

		if currentEnd > end:
			break

def loadDataForTick(lib, start, end):
	return loadData(lib, blKey, start, end, True), loadData(lib, txKey, start, end, True), loadData(lib, tickKey, start, end, True)

def subsetByDate(data, start, end):
	"""Function that takes in a DataFrame and start and end dates, returning the subset of the frame with these dates"""
	a = data[data.date >= start]
	return a[a.date < end]

def printHelp():
	print("Script that uses downloaded blockchain and course data to generate and save data properties.")
	print("Arguments:")
	print("remove : removes the database entries of generated properties.")


for i, arg in enumerate(sys.argv):
	if arg.find('help') >= 0 or len(sys.argv) == 1: printHelp()
	elif arg == 'remove':
		removeDB(propKey, storeKey)
	elif arg == 'generate':
		generateProperties()