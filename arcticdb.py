import sys
import os
from datetime import timezone, datetime as dt
import time
import pickle
import json
from time import sleep
import argparse

import pandas as pd
from Naked.toolshed.shell import execute_js, muterun_js
from arctic import Arctic
from arctic import TICK_STORE
from arctic import CHUNK_STORE
from arctic.date import DateRange

import database_tools as db

blockSeries = 10000
attemptsThreshold = 10


priceDataFile = 'data/cryptocompare_price_data.json'
dataDownloaderScript = '--max-old-space-size=4076 data-downloader.js'

chunkStore = db.getChunkstore()

def loadRawData(filepath):

	start = time.time()

	try:
		with open(filepath) as json_data:
			loadedData = json.load(json_data)
			print("Loading the data took "+str(time.time() - start)+" seconds")
			return loadedData
	except:
		return None

def convertTimestamp(x):
	if 'date' in x:
		key = 'date'
	elif 'time' in x:
		key = 'time'
	else:
		raise ValueError('Unsupported timestamp format in given data %s.' % x.keys())
	x['date'] = dt.utcfromtimestamp(x.pop(key, None)) #remove the old key, convert to date and replace it with 'date'

def processRawCourseData(data):

	start = time.time()
	for x in data:

		convertTimestamp(x)
		#x['transactions'] = str(pickle.dumps( [ {'from': 0x1, 'to': 0x2, 'value': 3} for x in range(3) ] ) )
	print("Processing the data took "+str(time.time() - start)+" seconds")





def downloadCourse(key):
	callDataDownloaderCourse()

	data = loadRawData(priceDataFile) #get it

	print("Downloaded data with length "+str(len(data))+" ticks") #debug

	processRawCourseData(data) #process a bit to make it suitable for storage

	db.saveData(chunkStore, key, data, db.courseChunkSize) #save to db


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

			sleep(30 * attempts) #delay before retrying. Most issues are solved that way.
			continue

		attempts = 0
		os.remove(filename)

		blocks, transactions = processRawBlockchainData(data)

		db.saveData(chunkStore, db.dbKeys['block'], blocks, db.blockChunkSize) #save block data
		if len(transactions) > 0 :
			db.saveData(chunkStore, db.dbKeys['tx'], transactions, db.txChunkSize) #save tx,t oo

		currentBlock += series

def getBlockchainFile(arg1, arg2): #the resulting file from the download script should match the requested arguments
	return 'data/blocks '+str(arg1)+'-'+str(arg2)+'.json'

def processRawBlockchainData(data):
	transactions = []
	for block in data:
		convertTimestamp(block) #transfer date string to date object, used to filter and manage the dt
		for tx in block['transactions']:
			tx['date'] = block['date']
			transactions.append(tx)
		block.pop('transactions', None) #remove the transactions from blockcdata - we work with them separately
	return data, transactions

def getLatestBlock():
	try:
		tmp = db.getLatestRow(chunkStore, db.dbKeys['block']) #get a dataframe with only the latest row
		return tmp.values[0, tmp.columns.searchsorted('number')] + 1 #extract the block number from it, add 1 for the next one
	except:
		return -1

if __name__ == "__main__": #if this is the main file, parse the command args
	parser = argparse.ArgumentParser(description="Module that downloads and stores blockchain and course data.")
	parser.add_argument('--course', dest='course', action="store_true", help="Downloads and saves or upgrades historical course data.")
	parser.add_argument('--blockchain', dest='blockchain', action="store_true", help="Downloads and saves or upgrades blockchain data.")
	parser.add_argument('--start', type=int, default=None, help='From which block to start downloading.')
	parser.add_argument('--end', type=int, default=None, help='Until which block to download.')
	parser.set_defaults(course=False)
	parser.set_defaults(blockchain=False)

	args, _ = parser.parse_known_args()

	if args.course: downloadCourse(db.dbKeys['tick'])
	if args.blockchain:
		downloadBlockchain(args.start, args.end)