import sys
import os
import importlib
from datetime import timezone, timedelta, datetime as dt
import time
import dateutil.parser
import argparse
import traceback
import inspect

from tables.exceptions import NodeError

import pandas as pd
import numpy as np

from processors import propertyObjects
from processors import postprocessorObjects
from processors import state
from database import instance as db

debug = False


def generateProperties(processorObjects, start=None, end=None, force=False):
	values = {} #a dict that holds an array of the returned values for each property

	reqList = []

	usingState = False
	historicalData = False
	
	#if all processors are flexible
	flexibleRequires = sum(x.flexibleRequires for x in processorObjects) == len(processorObjects)

	prev_t = 0
	next_t = 0

	for prop in processorObjects:

		if prop.provides is None:
			values[prop.name] = []
		else:
			for name in prop.provides:
				values[name] = []

		print(prop.requires, prop.name)

		reqList += prop.requires
		if prop.requiresState and not usingState:
			usingState = True
			reqList += state.requires

		if prop.requiresHistoricalData:
			historicalData = True
		prev_t = max(prev_t, prop.previousTicks)
		next_t = max(next_t, prop.nextTicks)

	if usingState:
		historicalData = True

	window_length = prev_t + 1 + next_t

	if historicalData and start is not None and not force:
		raise ValueError("The selected properties require all historical data, yet a start was given as an argument.")

	#remove dublicate entries
	reqList = list(set(reqList))

	print("Working with properties:", processorObjects, "" if not usingState else "and using state.")

	print("Requirements are:", reqList)

	def tickHandler(data, dates):

		date = dates[prev_t]

		if usingState:
			iterateOver = [state, *processorObjects]
		else:
			iterateOver = processorObjects

		for prop in iterateOver:
			s_i = prev_t - prop.previousTicks
			e_i = prev_t + 1 + prop.nextTicks
			subset = data[s_i : e_i]

			pr_data = {}

			for key in subset[0].keys():
				for dct in subset:
					pr_data.setdefault(key, [])
					pr_data[key].append(dct[key])
				pr_data[key] = pd.concat(pr_data[key])

			#TODO: subset according to the property's requirements?

			val = prop.processTick(pr_data)

			if prop.returnsData:
				if debug: print("Got value", val, "for property", prop.name)

				if prop.provides is not None:
					if len(prop.provides) != len(val):
						raise ValueError('The length of the returned child properties does not match the list of child ones by property %s !' % prop.name)
					for i, provided in enumerate(prop.provides):
						values[provided].append({'date': date, provided: val[i]})
				else:
					values[prop.name].append({'date': date, prop.name: val})

	try:
		forEachTick(tickHandler, 'tick', reqList, start=start, end=end, window=window_length, flexible=flexibleRequires)
		print("Finished generating property values.")
	except KeyboardInterrupt:
		print("Got interrupted, saving the current progress...")



	#save the raw property values
	for prop in values.keys():
		try:
			if values[prop]: #sma / ema and other modifiers may not be available
				#if we've generated values for too fewer ticks
				saveProperty(prop, values[prop])
		except ValueError as e:
			print("Failed saving property!", e, traceback.format_exc())

def saveProperty(name, val, quiet = False):
	val2 = []

	for v in val:
		v2 = v.copy() #avoid changing the actual values

		val2.append(v2)

	df = pd.DataFrame(val2)
	
	print(df.head())
	print(df.tail())
	
	df.set_index('date', inplace=True)

	if not quiet:
		print("Saving prop " + name)#+ " with values ", df.head(5), df.tail(5))
		print("With byte size:", sys.getsizeof(df))

	db.save(name, df)

	meta = db.getMetadata(name)
	meta['type'] = 'property'
	db.setMetadata(name, meta)

def forEachTick(callback, mainKey, dataKeys, start = None, end = None, window=1, flexible=False):
	#get the time interval where we have all needed data
	start, end = db.getMasterInterval([mainKey, *dataKeys], start, end) #TODO REMOVE DEBUG

	print("Starting generating properties from", start, "to", end)

	lastEnd = None

	mainData = db.get(mainKey, start=start, end=end)

	if debug: print("Loaded mainData:", mainData)

	iterators = {}

	for key in dataKeys:
		if not db.has_key(key):
			if flexible:
				continue
			else:
				raise ValueError("Required key %s is not available for processors." % key)
		
		iterators[key] = db.get(key, start=start, end=end, iterator=True)
		print("Working with requested data", key)

	data = {}#[next(iterators[i]) for i in range(len(iterators))]

	for key in iterators: # load the first chunks for all data
		data[key] = next(iterators[key])

	startTime = time.time()

	windowCache = []
	dateCache = []

	for mainRow in mainData.iterrows():
		rowData = mainRow[1]

		rowDate = rowData.name

		if rowDate < start or rowDate > end: continue #we don't want to be doing anything outside of our main interval

		if lastEnd is None: lastEnd = rowDate #if this is the first row we read
		else:
			#our interval is > lastEnd and <= rowDate
			currentStart = lastEnd
			currentEnd = rowDate
			lastEnd = currentEnd

			#load the needed data

			tickData = {}

			for key in data:
				tickData[key] = subsetByDate(data[key], currentStart, currentEnd)

				while not containsFullInterval(data[key], tickData[key], currentEnd):
					print("Loading new chunk for key" , key, tickData[key].head(2), tickData[key].tail(2), data[key].head(2), data[key].tail(2), currentStart, currentEnd)
					print("Processing of the chunk took "+str(time.time() - startTime)+"s.")
					startTime = time.time()

					try:
						data[key] = next(iterators[key]) #load another data chunk and append it
					except:
						#in case our connection to our database is dropped for a random reason
						#simulate that a user has cancelled the operation so that we'll save the progress up until now
						raise KeyboardInterrupt()

					newPart = subsetByDate(data[key], currentStart, currentEnd)
					tickData[key] = pd.concat([tickData[key], newPart])
				if debug:
					print(tickData[key].head(2))
					print(tickData[key].tail(2))

			skipTick=False

			for cache, data_to_store in [(windowCache, tickData), (dateCache, currentEnd)]:
				cache.append(data_to_store)

				if len(cache) < window:
					skipTick=True
					break
				
				if len(cache) > window:
					cache.pop(0)

			if skipTick:
				continue

			callback(windowCache, dateCache)

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
					val = min(subset)
				else:
					val = np.array(subset).min(0)
			else:
				if not isinstance(subset[0], np.ndarray):
					val = max(subset)
				else:
					val = np.array(subset).max(0)
			newValues.append(val)
	return newValues

def subsetByDate(data, start, end):
	"""Function that takes in a DataFrame and start and end dates, returning the subset of the frame with these dates"""
	return data[(data.index > start) & (data.index <= end)]

def isProperty(key):
	"""Checks whether the given database key belongs to a property or not."""
	for prop in propertyObjects:
		if key == prop.name:
			return True #TODO: What about property modifiers, like _rel, _sma, _10max?
		if prop.provides is not None:
			if key in prop.provides:
				return True
	return False

def containsFullInterval(data, subset, end):
	#if, for some reason, the subsetted data is empty, check only the intervals
	if len(subset) == 0:
		return (data.iloc[len(data)-1].name >= end)
	#check the real data
	else:
		res = (data.iloc[len(data)-1].name >= subset.iloc[len(subset)-1].name)
		return res

def getObjectsFromNameList(names, objects, empty_list_is_all=True):
	if len(names) > 0:
		res = []
		for obj in objects: #for every property that we have
			if obj.name in names: #if it is selected
				res.append(obj) #add it for generation
		
		if len(res) != len(names):
			raise ValueError("One or more of the given processors (%s) do not exist!" % str.join(',', names))
		return res
	elif empty_list_is_all:
		return objects.copy()
	else:
		raise ValueError("Empty name list given")

def generatePostprocessors(postprocessors):
	for proc in postprocessors:
		proc_name = proc.name

		available_props = [x.name for x in propertyObjects if db.has_key(x.name)] if proc.requires == [] else proc.requires

		for prop_name in available_props:
			print(proc_name, prop_name)

			proc.requires = [prop_name]

			generateProperties([proc])

			new_name = proc_name % prop_name 
			#try: # Problem: renaming the key doesn't change the name of the df columns
			#	db.rename(proc_name, proc_name % prop_name)
			#except NodeError:
			print("Renaming %s to %s" % (proc_name, new_name))

			data = db.get(proc_name)
			meta = db.getMetadata(proc_name)

			data.rename(index=str, columns={prop_name: new_name})
			meta['type'] = 'postprocessor'

			db.save(new_name, data)
			db.setMetadata(new_name, meta)

			db.remove(proc_name)

def run(action, processor_type, processors, start=None, end=None, list=False, force=False):
	db.open()

	processorObjects = propertyObjects if processor_type == "property" else postprocessorObjects

	if action == 'generate':
		objects = getObjectsFromNameList(processors, processorObjects)
		if processor_type == 'property':
			generateProperties(objects, start=start, end=end, force=force)
		else:
			generatePostprocessors(objects)
	elif action == 'remove':
		for key in db.list_keys():
			meta = db.getMetadata(key)

			if 'type' in meta:
				if key in processors or meta['type'] == processor_type:
					db.remove(key)
					print("Successfully removed key %s" % key)
	elif args.action == None or args.list:
		print("Available properties:", str.join(',', [prop.name for prop in propertyObjects]))

	db.close()

if __name__ == "__main__": #if this is the main file, parse the command args
	parser = argparse.ArgumentParser(description="Script that uses downloaded blockchain and course data to generate and save data properties")
	parser.add_argument('action', type=str, choices=['generate', 'remove'], help='Whether to generate processors or to remove some/all previously generated ones.')
	parser.add_argument('processor_type', type=str, choices=['property', 'postprocessor'], help='Whether to generate properties or postprocessors.')
	parser.add_argument('--processors', type=str, default=None, help='A list of the names of the processors to generate, separated by a comma.')
	parser.add_argument('--start', type=str, default=None, help='The start date. YYYY-MM-DD-HH')
	parser.add_argument('--end', type=str, default=None, help='The end date. YYYY-MM-DD-HH')
	parser.add_argument('--list', dest='list', action="store_true", help="List the available processors that can be generated.")
	parser.set_defaults(list=False)
	parser.add_argument('--force', dest='force', action="store_true", help="Shut up and 'sudo do_the_job'.")
	parser.set_defaults(force=False)

	args, _ = parser.parse_known_args()

	run(args.action, args.processor_type, processors=args.processors.split(',') if args.processors is not None else [], \
		start=dateutil.parser.parse(args.start) if args.start is not None else None, \
		end=dateutil.parser.parse(args.end) if args.end is not None else None, list=args.list, force=args.force)

