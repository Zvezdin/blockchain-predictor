import sys
import os
import importlib
from datetime import timezone, timedelta, datetime as dt
import time
import dateutil.parser
import argparse
import traceback

import pandas as pd
from arctic.date import DateRange
import numpy as np

import database_tools as db

#include the properties from their respectible folder
sys.path.insert(0, os.path.realpath('properties'))

from property import Property
from propertyAccountBalanceDistribution import PropertyAccountBalanceDistribution
from propertyAccountNumberDistribution import PropertyAccountNumberDistribution
from propertyBalanceLastSeenDistribution import PropertyBalanceLastSeenDistribution
from propertyBlockDifficulty import PropertyBlockDifficulty
from propertyBlockSize import PropertyBlockSize
from propertyClosePrice import PropertyClosePrice
from propertyContractBalanceLastSeenDistribution import PropertyContractBalanceLastSeenDistribution
from propertyContractVolumeInERC20Distribution import PropertyContractVolumeInERC20Distribution
from propertyGasLimit import PropertyGasLimit
from propertyGasPrice import PropertyGasPrice
from propertyGasUsed import PropertyGasUsed
from propertyHighPrice import PropertyHighPrice
from propertyLowPrice import PropertyLowPrice
from propertyNetworkHashrate import PropertyNetworkHashrate
from propertyOpenPrice import PropertyOpenPrice
#from propertyQuoteVolume import PropertyQuoteVolume
from propertyStickPrice import PropertyStickPrice
from propertyTransactionCount import PropertyTransactionCount
from propertyUniqueAccounts import PropertyUniqueAccounts
#from propertyVolume import PropertyVolume
from propertyVolumeFrom import PropertyVolumeFrom
from propertyVolumeTo import PropertyVolumeTo
#from propertyWeightedAverage import PropertyWeightedAverage

chunkStore = db.getChunkstore()


globalProperties = [PropertyAccountBalanceDistribution(), PropertyBalanceLastSeenDistribution(), PropertyBlockDifficulty(), PropertyBlockSize(), PropertyClosePrice(),
PropertyContractBalanceLastSeenDistribution(), PropertyContractVolumeInERC20Distribution(), PropertyGasLimit(), PropertyGasPrice(),
PropertyGasUsed(), PropertyHighPrice(), PropertyLowPrice(), PropertyNetworkHashrate(), PropertyOpenPrice(),
PropertyStickPrice(), PropertyTransactionCount(), PropertyUniqueAccounts(), PropertyVolumeFrom(), PropertyVolumeTo()]

propChunkSize = 'M'

debug = False


def generateProperties(selectedProperties = None, start = None, end = None, relative = False):
	values = {} #a dict that holds an array of the returned values for each property

	dub = {} #temp dict to make sure, that we won't have dubbed requirements

	requirements = []

	properties = []

	if selectedProperties and len(selectedProperties) > 0:
		for prop in globalProperties: #for every property that we have
			if prop.name in selectedProperties: #if it is selected
				properties.append(prop) #add it for generation
		
		if len(properties) != len(selectedProperties):
			print("ERROR! One or more of the given properties do not exist!")
			return
	else: properties = globalProperties

	print("Working with properties:", properties)

	for prop in properties:

		if prop.provides is None:
			values[prop.name]= []
		else:
			for name in prop.provides:
				values[name] = []
		for req in prop.requires:
			if not req in dub:
				dub[req] = True
				requirements.append(req)
	print("Requirements are:", requirements)

	def tickHandler(data, date):
		for prop in properties:
			val = prop.processTick(data)
			if debug: print("Got value", val, "for property", prop.name)

			if prop.provides is not None:
				if len(prop.provides) != len(val):
					raise ValueError('The length of the returned child properties does not match the list of child ones by property %s !' % prop.name)
				for i, provided in enumerate(prop.provides):
					values[provided].append({'date': date, provided: val[i]})
			else:
				values[prop.name].append({'date': date, prop.name: val})

	try:
		forEachTick(tickHandler, db.dbKeys['tick'], requirements, start=start, end=end)
		print("Finished generating property values.")
	except KeyboardInterrupt:
		print("Got interrupted, saving the current progress...")

	#hold the property names that don't provide children in a list
	propNames = [prop.name for prop in properties if prop.provides is None]

	#take the children those who provide them
	for prop in properties:
		if prop.provides is not None:
			propNames.extend(prop.provides)


	for prop in list(values.keys()):
		modifiedProperty(values, prop, prop+"_sma", smaValues)
		modifiedProperty(values, prop, prop+"_ema", emaValues)
		modifiedProperty(values, prop, prop+"_10max", futureMaxValues)
		modifiedProperty(values, prop, prop+"_10min", futureMinValues)

	if relative: #turn everything relative
		for prop in list(values.keys()):
			modifiedProperty(values, prop, prop+"_rel", relativeValues)

	#save the raw property values
	for prop in values.keys():
		try:
			saveProperty(prop, values[prop])
		except ValueError as e:
			print("Failed saving property!", e, traceback.format_exc())

def saveProperty(name, val, quiet = False):
	val2 = []

	for v in val:
		v2 = v.copy() #avoid changing the actual values

		if type(v2[name]) == np.ndarray:
			v2[name] = db.encodeObject(v2[name]) #encode due to DB limitations
		val2.append(v2)

	if not quiet:
		df = db.getDataFrame(val2)
		print("Saving prop " + name+ " with values ", df.head(5), df.tail(5))
		print("With byte size:", sys.getsizeof(df))

	db.saveData(chunkStore, name, val2, propChunkSize)

def forEachTick(callback, mainKey, dataKeys, start = None, end = None, t=1):
	#get the time interval where we have all needed data
	start, end = db.getMasterInterval(chunkStore, db.dbKeys.values(), start, end)

	print("Starting generating properties from", start, "to", end)

	lastEnd = None

	mainData = chunkStore.read(mainKey, chunk_range=DateRange(start, end))

	if debug: print("Loaded mainData:", mainData)

	iterators = {}

	for key in db.dbKeys: #for each key (not value) that we store in the dbKeys
		if dataKeys and key not in dataKeys: continue
		iterators[key] = chunkStore.iterator(db.dbKeys[key], chunk_range=DateRange(start, end))
		print("Working with requested data", key)

	data = {}#[next(iterators[i]) for i in range(len(iterators))]

	for key in iterators: # load the first chunks for all data
		data[key] = decodeRawData(next(iterators[key]))

	startTime = time.time()

	for mainRow in mainData.iterrows():
		rowData = mainRow[1]

		if rowData.date < start or rowData.date > end: continue #we don't want to be doing anything outside of our main interval

		if lastEnd is None: lastEnd = rowData.date #if this is the first row we read
		else:
			#our interval is > lastEnd and <= rowData.date
			currentStart = lastEnd
			currentEnd = rowData.date
			lastEnd = currentEnd

			#print("Loading data for dates", currentStart, currentEnd)

			#load the needed data

			tickData = {}
			for key in data:
				tickData[key] = subsetByDate(data[key], currentStart, currentEnd)

				while not containsFullInterval(data[key], tickData[key], currentEnd):
					print("Loading new chunk for key" , key, tickData[key].head(2), tickData[key].tail(2), data[key].head(2), data[key].tail(2), currentStart, currentEnd)
					print("Processing of the chunk took "+str(time.time() - startTime)+"s.")
					startTime = time.time()
					data[key] = decodeRawData(next(iterators[key])) #load another data chunk and append it
					newPart = subsetByDate(data[key], currentStart, currentEnd)
					tickData[key] = pd.concat([tickData[key], newPart])
				if debug:
					print(tickData[key].head(2))
					print(tickData[key].tail(2))

			callback(tickData, currentEnd)

def modifiedProperty(valuesDict, name, newName, transformFunction):
	propVals = []

	valuesDict[newName] = []

	for i, val in enumerate(valuesDict[name]):
		propVals.append(val[name])

	propVals = transformFunction(propVals)

	for i, val in enumerate(propVals):
		if val is not None: #we can see none values in the start of the series as they cannot be converted to what needed.
			valuesDict[newName].append({'date': valuesDict[name][i]['date'], newName: val})

def relativeValues(values):
	newValues = []
	for i in range(len(values)-1, -1, -1):
		if i > 0:
			newValues.append(values[i] - values[i-1])
		else:
			newValues.append(None)
	newValues.reverse()

	return newValues

def smaValues(values, periods=10):
	newValues = []

	for i, val in enumerate(values):
		if i < periods -1:
			newValues.append(None)
		else:
			newValues.append(sum(values[i-(periods-1): i+1]) / float(periods)) #the avg of last 'periods' periods

	return newValues

def emaValues(values, periods=10):
	newValues = []

	multiplier = 2 / float(periods + 1)

	smaVals = smaValues(values, periods=periods)

	initialSMA = False

	for i, sma in enumerate(smaVals):
		if sma is None:
			newValues.append(None)
			continue
		
		if(not initialSMA):
			ema = sma #the first value is the first available SMA
			initialSMA = True
		else:
			ema = (values[i] - newValues[i-1]) * multiplier + newValues[i-1]
		newValues.append(ema)

	return newValues

def macdValues(values, firstEmaPeriods = 12, secondEmaPeriods = 26):
	newValues = []

	firstEma = emaValues(values, firstEmaPeriods)
	secondEma = emaValues(values, secondEmaPeriods)

	for i, val in enumerate(values):
		if firstEma[i] is None or secondEma[i] is None:
			newValues.append(None)
		else:
			newValues.append(firstEma[i] - secondEma[i])

def futureMaxValues(values, periods=10):
	return futureMaxMinValues(values, periods=periods, minValues=False)

def futureMinValues(values, periods=10):
	return futureMaxMinValues(values, periods=periods, minValues=True)


def futureMaxMinValues(values, periods=10, minValues=False):
	newValues = []

	for i, val in enumerate(values):
		if(i+(periods-1) >= len(values)):
			newValues.append(None)
		else:
			subset = values[i:(i+periods)]
			assert(len(subset) > 0)

			if(minValues):
				if not isinstance(subset[0], np.ndarray):
					print(type(subset[0]))
					val = min(subset)
				else:
					val = np.array(subset).min(0)
			else:
				if not isinstance(subset[0], np.ndarray):
					print(type(subset[0]))
					val = max(subset)
				else:
					val = np.array(subset).max(0)
			newValues.append(val)
	return newValues

def decodeRawData(data):
	if 'logs' in data: #the logs in our raw data are encoded via pickle, because of Arctic limitations
		data['logs'] = data['logs'].apply(lambda x: db.decodeObject(x))
	return data

def loadDataForTick(lib, start, end):
	return [db.loadData(lib, key, start, end, True) for key in db.dbKeys]

def subsetByDate(data, start, end):
	"""Function that takes in a DataFrame and start and end dates, returning the subset of the frame with these dates"""
	return data[(data.date > start) & (data.date <= end)]

def containsFullInterval(data, subset, end):
	#if, for some reason, the subsetted data is empty, check only the intervals
	if len(subset) == 0: return (data.iloc[len(data)-1].date >= end)
	#check the real data
	else: return (data.iloc[len(data)-1].date >= subset.iloc[len(subset)-1].date)

if __name__ == "__main__": #if this is the main file, parse the command args
	parser = argparse.ArgumentParser(description="Script that uses downloaded blockchain and course data to generate and save data properties")
	parser.add_argument('--action', type=str, default=None, choices=['generate', 'remove'], help='Whether to generate properties or to remove some/all previously generated ones.')
	parser.add_argument('--properties', type=str, default=None, help='A list of the names of the properties to generate, separated by a comma.')
	parser.add_argument('--start', type=str, default=None, help='The start date. YYYY-MM-DD-HH')
	parser.add_argument('--end', type=str, default=None, help='The end date. YYYY-MM-DD-HH')
	parser.add_argument('--list', dest='list', action="store_true", help="List the available properties that can be generated.")
	parser.set_defaults(list=False)
	parser.add_argument('--relative', dest='relative', action="store_true", help="Generate the properties with relative values.")
	parser.set_defaults(relative=False)

	args, _ = parser.parse_known_args()

	start = dateutil.parser.parse(args.start) if args.start is not None else None
	end = dateutil.parser.parse(args.end) if args.end is not None else None

	properties = args.properties.split(',') if args.properties != None  else None

	if args.action == 'generate':
		generateProperties(properties, start, end, args.relative)
	elif args.action == 'remove':
		if properties == None:
			properties = [prop.name for prop in globalProperties if prop.provides == None]

			for prop in globalProperties:
				if prop.provides is not None:
					properties.extend(prop.provides)

			relProps = properties.copy()

			for i, prop in enumerate(relProps):
				relProps[i] += '_rel'

			properties.extend(relProps)

		for prop in properties:
			db.removeDB(chunkStore, prop)
	elif args.action == None or args.list:
		print("Available properties:", [prop.name for prop in globalProperties])
