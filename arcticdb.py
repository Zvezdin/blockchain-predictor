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

from database_tools import *

blockSeries = 10000
attemptsThreshold = 10


priceDataFile = 'data/poloniex_price_data.json'
dataDownloaderScript = '--max-old-space-size=4076 data-downloader.js'

chunkStore = getChunkstore()

def loadRawData(filepath):

	start = time.time()

	try:
		with open(filepath) as json_data:
			loadedData = json.load(json_data)
			print("Loading the data took "+str(time.time() - start)+" seconds")
			return loadedData
	except:
		return None
def processRawCourseData(data):

	start = time.time()
	for x in data:
		x['date'] = dt.fromtimestamp(x['date'])
		#x['transactions'] = str(pickle.dumps( [ {'from': 0x1, 'to': 0x2, 'value': 3} for x in range(3) ] ) )
	print("Processing the data took "+str(time.time() - start)+" seconds")





def downloadCourse(key):
	callDataDownloaderCourse()

	data = loadRawData(priceDataFile) #get it

	print("Downloaded data with length "+str(len(data))+" ticks") #debug

	processRawCourseData(data) #process a bit to make it suitable for storage

	saveData(chunkStore, key, data, courseChunkSize) #save to db


def callDataDownloaderCourse():
	success = execute_js(dataDownloaderScript, 'course')
	if not success: print("Failed to execute js")

def callDataDownloaderBlockchain(start, count):
	success = execute_js(dataDownloaderScript, 'blockchain '+str(start)+' '+str(count))
	if not success: print("Failed to execute js")

def downloadBlockchain(start = 0, targetBlock = None):
	currentBlock = getLatestBlock()

	if(currentBlock < 0): currentBlock = start

	print("Starting to download blocks after", currentBlock, " and with target ", targetBlock)


	series = blockSeries

	if targetBlock != None and series > targetBlock - currentBlock: series = targetBlock - currentBlock

	attempts = 0

	while currentBlock < (targetBlock if targetBlock != None else 4146000): #todo determine the end of the blockchain automatically
		print('Calling js to download '+str(series)+' blocks from '+str(currentBlock))
		callDataDownloaderBlockchain(currentBlock, series)
		filename = getBlockchainFile(currentBlock, currentBlock+series-1)
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

		saveData(chunkStore, dbKeys.block, blocks, blockChunkSize) #save block data
		if len(transactions) > 0 :
			saveData(chunkStore, dbKeys.tx, transactions, txChunkSize) #save tx,t oo

		currentBlock += series

def getBlockchainFile(arg1, arg2): #the resulting file from the download script should match the requested arguments
	return 'data/blocks '+str(arg1)+'-'+str(arg2)+'.json'

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
		tmp = getLatestRow(chunkStore, dbKeys.block) #get a dataframe with only the latest row
		return tmp.values[0, tmp.columns.searchsorted('number')] + 1 #extract the block number from it, add 1 for the next one
	except:
		return -1

def printHelp():
	print("Arguments:")
	print("remove - removes the db")
	print("course - downloads and saves / upgrades historical course in the db")
	print("blockchain - downloads and saves / upgrades blockchain data in the db. Enter a start and an end block to download all blocks within that range.")
	print("peek - shows the first and last rows of the db")
	print("read - loads data in memory. Enter a db key to choose the data.")
	print("upgrade - updates both blockchain and course db entries")

i = 0
while i < len(sys.argv):
	arg = sys.argv[i]

	if arg.find('help') >= 0 or len(sys.argv) == 1: printHelp() #if there are no given arguments or the user has entered 'help'
	elif arg == 'remove':
		removeDB(dbKeys.tick, storeKey)
		removeDB(dbKeys.block, storeKey)
		removeDB(dbKeys.tx, storeKey)
	elif arg == 'course': downloadCourse(dbKeys.tick)
	elif arg == 'peek':
		peekData(chunkStore, dbKeys.block)
		peekData(chunkStore, dbKeys.tx)
		peekData(chunkStore, dbKeys.tick)
	elif arg == 'read':
		try:
			readAllData(chunkStore, sys.argv[i+1])
			i+=1
		except:
			print("There was an error while reading. Did you enter the correct key?")
			break
	elif arg == 'upgrade': upgradeDB(dbKeys.tick)
	elif arg == 'blockchain':
		try:
			downloadBlockchain(int(sys.argv[i+1]), int(sys.argv[i+2])) #Try to see if the user gave an argument
			i+=2
		except:
			downloadBlockchain() #if not, pass none
	i+=1