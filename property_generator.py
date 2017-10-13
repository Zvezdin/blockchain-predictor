import sys
from datetime import timezone, timedelta, datetime as dt
import time
import dateutil.parser

import pandas as pd
from arctic.date import DateRange

import database_tools as db
from propertyGasPrice import PropertyGasPrice
from propertyOpenPrice import PropertyOpenPrice
from propertyClosePrice import PropertyClosePrice

chunkStore = db.getChunkstore()


globalProperties = [PropertyGasPrice(), PropertyOpenPrice(), PropertyClosePrice()]
propChunkSize = 'M'

debug = False


def generateProperties(selectedProperties = None, start = None, end = None):
	values = {} #a dict that holds an array of the returned values for each property

	dub = {}

	requirements = []

	properties = []

	if selectedProperties and len(selectedProperties) > 0:
		for prop in globalProperties: #for every property that we have
			if prop.name in selectedProperties: #if it is selected
				properties.append(prop) #add it for generation
	else: properties = globalProperties

	print("Working with properties:", properties)

	for prop in properties:
		values[prop.name]= []
		for req in prop.requires:
			if not req in dub:
				dub[req] = True
				requirements.append(req)
	print("Requirements are:", requirements)

	def tickHandler(data, date):
		for prop in properties:
			val = prop.processTick(data)
			if debug: print("Got value", val, "for property", prop.name)
			values[prop.name].append({'date': date, prop.name: val})

	forEachTick(tickHandler, db.dbKeys['tick'], requirements, start=start, end=end)

	for prop in properties:
		df = db.getDataFrame(values[prop.name])
		print("Saving prop " + prop.name+ " with values ", df)
		print("With byte size:", sys.getsizeof(df))

		try:
			db.saveData(chunkStore, prop.name, values[prop.name], propChunkSize)
		except:
			print("Failed saving property!", sys.exc_info()[0])



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
		data[key] = next(iterators[key])

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

			print("Loading data for dates", currentStart, currentEnd)

			#load the needed data

			tickData = {}
			for key in data:
				tickData[key] = subsetByDate(data[key], currentStart, currentEnd)

				while not containsFullInterval(data[key], tickData[key], currentEnd):
					print("Loading new chunk for key" , key, tickData[key].head(2), tickData[key].tail(2), data[key].head(2), data[key].tail(2), currentStart, currentEnd)
					print("Processing of the chunk took "+str(time.time() - startTime)+"s.")
					startTime = time.time()
					data[key] = next(iterators[key]) #load another data chunk and append it
					newPart = subsetByDate(data[key], currentStart, currentEnd)
					tickData[key] = pd.concat([tickData[key], newPart])
				if debug:
					print(tickData[key].head(2))
					print(tickData[key].tail(2))

			callback(tickData, currentEnd)

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
	def printHelp():
		print("Script that uses downloaded blockchain and course data to generate and save data properties.")
		print("Arguments:")
		print("generate: generates all available properties for all available data.")
		print("---Arguments---")
		print("")
		print("remove : removes the database entries of generated properties.")

	i = 0
	while i < len(sys.argv):
		arg = sys.argv[i]

		if arg.find('help') >= 0 or len(sys.argv) == 1: printHelp()
		elif arg == 'remove':
			for prop in globalProperties:
				db.removeDB(chunkStore, prop.name)
		elif arg == 'generate':
			try:
				generateProperties(sys.argv[i+1].split(','), dateutil.parser.parse(sys.argv[i+2]), dateutil.parser.parse(sys.argv[i+3]))
				i+=3
			except:
				try:
					generateProperties(sys.argv[i+1].split(','))
					i+=1
				except:
					generateProperties()

		i+=1