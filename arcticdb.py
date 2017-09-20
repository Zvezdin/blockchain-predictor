from arctic import Arctic
from arctic import TICK_STORE
from arctic import CHUNK_STORE
from arctic.date import DateRange

import pandas as pd
from datetime import timezone, datetime as dt
import time

import pickle
import json

import sys
import os
from Naked.toolshed.shell import execute_js, muterun_js

tickKey = 'test2'
txKey = 'tx'
blKey =  'block'
blockChunkSize = 'W'
txChunkSize = 'D'
courseChunkSize = 'M'

blockSeries = 10000
attemptsThreshold = 10

store = Arctic('localhost')

chunkStore = 0
try:
	chunkStore = store['chunkstore']
except:
	store.initialize_library('chunkstore', lib_type=CHUNK_STORE)
	chunkStore = store['chunkstore']

def loadRawData(filepath):

	start = time.time()

	try:
		with open(filepath) as json_data:
			loadedData = json.load(json_data)
			print("Loading the data took "+str(time.time() - start)+" seconds")
			return loadedData
	except:
		return None
def processRawData(data):

	start = time.time()
	for x in data:
		x['date'] = dt.fromtimestamp(x['date'])
		#x['transactions'] = str(pickle.dumps( [ {'from': 0x1, 'to': 0x2, 'value': 3} for x in range(3) ] ) )
	print("Processing the data took "+str(time.time() - start)+" seconds")

def getDataFrame(data):
	return pd.DataFrame(data)

def saveData(key, data, chunkSize = courseChunkSize):
	start = time.time()

	if chunkStore.has_symbol(key):
		trimIndex = 0

		try:
			newestDate = chunkStore.read_metadata(key)['end']
		except:
			newestDate = 0
		print("newest date is ")
		print(newestDate)

		while trimIndex < len(data) and newestDate >= data[trimIndex]['date'] :
			trimIndex+=1

		if(len(data) == trimIndex): print("Data already written!")
		else:
			metadata = chunkStore.read_metadata(key)
			print("Got metadata", metadata)
			chunkStore.append(key, getDataFrame(data[trimIndex:]))

			metadata['end'] = data[len(data)-1]['date']
			chunkStore.write_metadata(key, metadata)
	else:
		df = getDataFrame(data)
		chunkStore.write(key, df, chunk_size=chunkSize)
		chunkStore.write_metadata(key, {'start': data[0]['date'], 'end': data[len(data)-1]['date'] })
	print("Saving the data took "+str(time.time() - start)+" seconds")

def readData(key):
	try:
		df = chunkStore.read(key)
	except:
		print("Error:", sys.exc_info()[0])
		return	
	print("Reading the fifth row")

	values = df.values

	print(values[4])

def printData(key, n = 5 ):
	start = time.time()

	try:
		df = chunkStore.read(key)
	except:
		print("Error:", sys.exc_info()[0])
		return
	print(df.head(n))
	print('...')
	print(df.tail(n))
	print(len(df.values))
	print("Displaying the data took "+str(time.time() - start)+" seconds")

def saveCourse(key, processor):
	callDataDownloaderCourse()
	filepath = 'data/poloniex_price_data.json'
	data = loadRawData(filepath) #get it

	print("Loaded data with length "+str(len(data))+" ticks") #debug

	processor(data) #process a bit to make it suitable for storage

	saveData(key, data, courseChunkSize) #save to db

def removeDB(key):
	if chunkStore.has_symbol(key):
		chunkStore.delete(key) #used for debugging
		print("Removed database")

def peekDB(key):
	printData(key)

def readDB(key):
	readData(key)

def getLatestRow(key):
	latestDate = chunkStore.read_metadata(key)['end']
	return chunkStore.read(key, chunk_range = DateRange(latestDate, None))

def callDataDownloaderCourse():
	success = execute_js('data-downloader.js', 'course')
	if not success: print("Failed to execute js")

def callDataDownloaderBlockchain(start, count):
	success = execute_js('data-downloader.js', 'blockchain '+str(start)+' '+str(count))
	if not success: print("Failed to execute js")

def downloadBlockchain(start = 0, targetBlock = None):
	currentBlock = getLatestBlock()

	if(currentBlock == 0): currentBlock = start

	print("Starting to download blocks after", currentBlock, " and with target ", targetBlock)

	series = blockSeries

	attempts = 0

	while currentBlock < (targetBlock if targetBlock != None else 4146000):
		print('Calling js to download '+str(series)+' blocks from '+str(currentBlock))
		callDataDownloaderBlockchain(currentBlock, series)
		filename = 'data/blocks '+str(currentBlock)+'-'+str(currentBlock+series-1)+'.json'
		data = loadRawData(filename) #get it

		if data == None:
			print("Failed reading", filename, ", redownloading...")
			attempts += 1

			if(attempts > attemptsThreshold):
				print("Too many failed attempts, aborting operation.")
				return
			continue

		attempts = 0
		os.remove(filename)

		blocks, transactions = processRawBlockchainData(data)

		saveData(blKey, blocks, blockChunkSize) #save block data
		if len(transactions) > 0 :
			saveData(txKey, transactions, txChunkSize) #save tx,t oo

		currentBlock += series

def processRawBlockchainData(data):
	transactions = []
	for block in data:
		block['date'] = dt.fromtimestamp(block['date']) #transfer date string to date object, used to filter and manage the dt
		for tx in block['transactions']:
			tx['date'] = block['date']
			transactions.append(tx)
		block.pop('transactions', None) #remove the transactions from blockcdata - we work with them separately
	return data, transactions

def getLatestBlock():
	try:
		tmp = getLatestRow(blKey) #get a dataframe with only the latest row
		return tmp.values[0, tmp.columns.searchsorted('number')] + 1 #extract the block number from it, add 1 for the next one
	except:
		return 0

def printHelp():
	print("Arguments:")
	print("remove - removes the db")
	print("course - downloads and saves / upgrades historical course in the db")
	print("blockchain - downloads and saves / upgrades blockchain data in the db. Enter a start and an end block to download all blocks within that range.")
	print("peek - shows the first and last rows of the db")
	print("read - loads the db in memory")
	print("upgrade - updates both blockchain and course db entries")

for i, arg in enumerate(sys.argv):
	if arg.find('help') >= 0 or len(sys.argv) == 1: printHelp()
	elif arg == 'remove':
		removeDB(tickKey)
		removeDB(blKey)
		removeDB(txKey)
	elif arg == 'course': saveCourse(tickKey, processRawData)
	elif arg == 'peek':
		peekDB(blKey)
		peekDB(txKey)
	elif arg == 'read': readDB(tickKey)
	elif arg == 'upgrade': upgradeDB(tickKey)
	elif arg == 'blockchain':
		try:
			downloadBlockchain(int(sys.argv[i+1]), int(sys.argv[i+2])) #Try to see if the user gave an argument
		except:
			downloadBlockchain() #if not, pass none