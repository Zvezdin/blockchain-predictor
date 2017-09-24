import pandas as pd
from datetime import timezone, timedelta, datetime as dt
import time

import sys
import os
from Naked.toolshed.shell import execute_js, muterun_js

from database_tools import *

from propertyGasPrice import *
from propertyOpenPrice import *
from property import *

chunkStore = getChunkstore()


properties = [PropertyGasPrice(), PropertyOpenPrice()]
propChunkSize = 'M'


def generateProperties():
	values = {} #a dict that holds an array of the returned values for each property

	for prop in properties:
		values[prop.name]= []

	def tickHandler(data, date):
		for prop in properties:
			val = prop.processTick(data)
			print("Got value", val, "for property", prop.name)
			values[prop.name].append({'date': date, prop.name: val})

	print("working with keys", dbKeys)

	forEachTick(tickHandler, dbKeys['tick'])

	for prop in properties:
		df = getDataFrame(values[prop.name])
		print("Saving prop " + prop.name+ " with values ", df)
		#saveData(chunkStore, prop.name, values[prop.name], propChunkSize)



def forEachTick(callback, mainKey, t=1):
	#get the time interval where we have all needed data
	start = max([loadMetadata(chunkStore, key)['start'] for key in dbKeys.values()])

	end = min([loadMetadata(chunkStore, key)['end'] for key in dbKeys.values()])

	print("Starting generating properties from", start, "to", end)

	lastEnd = None

	mainData = chunkStore.read(mainKey, chunk_range=DateRange(start, end))

	print("Loaded mainData:", mainData)

	iterators = {}

	for key in dbKeys: #for each key (not value) that we store in the dbKeys
		#if key == mainKey: continue
		iterators[key] = chunkStore.iterator(dbKeys[key], chunk_range=DateRange(start, end))

	data = {}#[next(iterators[i]) for i in range(len(iterators))]

	for key in iterators: # load the first chunks for all data
		data[key] = next(iterators[key])

	for mainRow in mainData.iterrows():
		rowData = mainRow[1]

		if rowData.date < start or rowData.date > end: continue #we don't want to be doing anything outside of our main interval

		if lastEnd is None: lastEnd = rowData.date #if this is the first row we read
		else:
			#our interval is > lastEnd and <= rowData.date
			currentStart = lastEnd
			currentEnd = rowData.date
			lastEnd = currentEnd

			print("Loading data for dates", currentStart, currentEnd)

			#load the needed data

			tickData = {}
			for key in data:
				tickData[key] = subsetByDate(data[key], currentStart, currentEnd)

				#print(data[key], tickData[key])

				while not containsFullInterval(data[key], tickData[key]):
					data[key] = next(iterators[key]) #load another data chunk and append it
					newPart = subsetByDate(data[key], currentStart, currentEnd)
					tickData[key] = pd.concat([tickData[key], newPart])
				print(tickData[key].head(2))
				print(tickData[key].tail(2))

			callback(tickData, currentEnd)

def loadDataForTick(lib, start, end):
	return [loadData(lib, key, start, end, True) for key in dbKeys]

def subsetByDate(data, start, end):
	"""Function that takes in a DataFrame and start and end dates, returning the subset of the frame with these dates"""
	return data[(data.date > start) & (data.date <= end)]

def containsFullInterval(data, subset):
	if len(subset) == 0: return False
	return (data.iloc[0].date <= subset.iloc[0].date) and (data.iloc[len(data)-1].date >= subset.iloc[len(subset)-1].date)

def printHelp():
	print("Script that uses downloaded blockchain and course data to generate and save data properties.")
	print("Arguments:")
	print("remove : removes the database entries of generated properties.")


for i, arg in enumerate(sys.argv):
	if arg.find('help') >= 0 or len(sys.argv) == 1: printHelp()
	elif arg == 'remove':
		for prop in properties:
			removeDB(prop.name, storeKey)
	elif arg == 'generate':
		generateProperties()