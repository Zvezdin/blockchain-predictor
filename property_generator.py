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


globalProperties = [PropertyAccountBalanceDistribution(), PropertyBalanceLastSeenDistribution(), PropertyBlockDifficulty(), PropertyBlockSize(), PropertyClosePrice(), PropertyGasLimit(), PropertyGasPrice(),
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
	else: properties = globalProperties

	print("Working with properties:", properties)

	for prop in properties:

		if prop.provides == None:
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

			if prop.provides != None:
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

	#print("DEBUG:")
	#for prop in globalProperties:
	#	if prop.name == 'accountDistribution':
	#		for adr in ['0xb794f5ea0ba39494ce839613fffba74279579268', '0x35da6AbcB08F2b6164fE380BB6c47BD8F2304d55']:
	#			adr = adr.lower() #fix capital hex error
	#			print("Balance of %s is %d" % (adr, prop.accounts[adr]))
	#		print("Max balance is %d." % max(prop.accounts.values()))

	#hold the property names that don't provide children in a list
	propNames = [prop.name for prop in properties if prop.provides == None]

	#take the children those who provide them
	for prop in properties:
		if prop.provides != None:
			propNames.extend(prop.provides)


	#save the raw property values
	for prop in propNames:
		try:
			saveProperty(prop, values[prop])
		except ValueError as e:
			print("Failed saving property!", e, traceback.format_exc())

	for prop in properties:
		if relative and not prop.isRelative: #turn that property into relative values
			print("Turning property %s into relative values." % prop.name)

			names = [prop.name]

			if prop.provides != None:
				names = prop.provides

			for name in names:
				values[name+"_rel"] = values.pop(name) #rename the main property key
				for i in range(len(values[name+'_rel'])-1, -1, -1): #reverse index iteration
					if i > 0:
						values[name+'_rel'][i][name] = values[name+'_rel'][i][name] - values[name+'_rel'][i-1][name]

						values[name+'_rel'][i][name+'_rel'] = values[name+'_rel'][i].pop(name) # rename the value key

				values[name+'_rel'].pop(0) #remove the first value as we can't relative that

				try:
					saveProperty(name+'_rel', values[name+'_rel'])
				except:
					print("Failed saving property!", sys.exc_info()[0])

def saveProperty(name, val, quiet = False):
	if not quiet:
		df = db.getDataFrame(val)
		print("Saving prop " + name+ " with values ", df.head(5), df.tail(5))
		print("With byte size:", sys.getsizeof(df))

	db.saveData(chunkStore, name, val, propChunkSize)

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
				if prop.provides != None:
					properties.extend(prop.provides)

			relProps = properties.copy()

			for i, prop in enumerate(relProps):
				relProps[i] += '_rel'

			properties.extend(relProps)

		for prop in properties:
			db.removeDB(chunkStore, prop)
	elif args.action == None or args.list:
		print("Available properties:", [prop.name for prop in globalProperties])
