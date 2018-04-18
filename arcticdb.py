""""Interface between the JS Download script and the Database storage"""

import os
from datetime import datetime as dt
import time
import json
import argparse

from Naked.toolshed.shell import execute_js, muterun_js

import database_tools as db

blockSeries = 2000
attemptsThreshold = 10

logsSeparate = False
parseToInt = False

tempFilename = 'data/temp.json'

dataDownloaderScript = '--max-old-space-size=32768 data-downloader.js'

chunkStore = db.getChunkstore()

def loadRawData(filepath):

	start = time.time()

	try:
		with open(filepath) as json_data:
			loadedData = json.load(json_data)
			print("Loading the data took "+str(time.time() - start)+" seconds")
			return loadedData
	except FileNotFoundError:
		return None

def convertTimestamp(x):
	if 'date' in x:
		key = 'date'
	elif 'time' in x:
		key = 'time'
	else:
		raise ValueError('Unsupported timestamp format in given data %s.' % x.keys())
	x['date'] = dt.utcfromtimestamp(x.pop(key, None)) #remove the old key, convert to date and replace it with 'date'

def parseInt(data):
	if type(data) == dict:
		for key in data: #parse to int
				if type(data[key]) == str:
					try:
						base = 10
						if data[key].startswith('0x'):
							base = 16

						data[key] = int(data[key], base=base)
					except ValueError:
						pass
	elif type(data) == list:
		for i, val in enumerate(data):
			if type(val) == str:
				try:
					base = 10
					if val.startswith('0x'):
						base = 16

					data[i] = int(val, base=base)
				except ValueError:
					pass

def processRawCourseData(data):
	start = time.time()
	for x in data:
		convertTimestamp(x)


def downloadCourse():
	callDataDownloaderCourse(tempFilename)

	data = loadRawData(tempFilename) #get it
	os.remove(tempFilename)

	print("Downloaded data with length "+str(len(data))+" ticks") #debug

	processRawCourseData(data) #process a bit to make it suitable for storage

	db.saveData(chunkStore, db.dbKeys['tick'], data, db.chunkSizes['tick']) #save to db


def callDataDownloaderCourse(filename):
	success = execute_js(dataDownloaderScript, '--course --filename '+filename)
	if not success:
		print("Failed to execute js")

def callDataDownloaderBlockchain(start, count, filename):
	success = execute_js(dataDownloaderScript, '--blockchain '+str(start)+' '+str(count)+' --filename '+filename)
	if not success:
		print("Failed to execute js")

def downloadBlockchain(start=0, targetBlock=None):
	"""Calls the JS script to download a certain block range and saves the result in the DB"""

	currentBlock = getLatestBlock()

	if currentBlock < 0:
		currentBlock = start

	series = blockSeries

	if targetBlock is None:
		targetBlock = 5300000 #TODO: Have automatic detection of latest block
	if series > targetBlock - currentBlock:
		series = targetBlock - currentBlock
	print("Starting to download blocks after", currentBlock, " and with target ", targetBlock)

	attempts = 0

	while currentBlock < targetBlock:
		nextTargetBlock = currentBlock + series-1
		print('Calling js to download '+str(series)+' blocks from '+str(currentBlock))
		callDataDownloaderBlockchain(currentBlock, nextTargetBlock, tempFilename)

		data = loadRawData(tempFilename) #get it

		if data is None:
			print("Failed reading", tempFilename, ", redownloading...")
			attempts += 1

			if attempts > attemptsThreshold:
				print("Too many failed attempts, aborting operation.")
				return

			time.sleep(30 * attempts) #delay before retrying. Most issues are solved that way.
			continue

		attempts = 0
		os.remove(tempFilename)

		data = processRawBlockchainData(data)

		for key in data:
			if data[key]:
				db.saveData(chunkStore, db.dbKeys[key], data[key], db.chunkSizes[key]) #save in DB

		currentBlock += series

def getBlockchainFile(arg1, arg2): #the resulting file from the download script should match the requested arguments
	return 'data/blocks '+str(arg1)+'-'+str(arg2)+'.json'

def processRawBlockchainData(data):
	for key in data: #for each time series
		for el in data[key]: #each element in the time series
			convertTimestamp(el) #transfer UNIX timestamp to date object, used to filter and manage the DB
			if parseToInt:
				parseInt(el)

	return data

def getLatestBlock():
	try:
		tmp = db.getLatestRow(chunkStore, db.dbKeys['block']) #get a dataframe with only the latest row
		num =  tmp.values[0, tmp.columns.searchsorted('number')] + 1 #extract the block number from it, add 1 for the next one
		
		return num
	except:
		return -1

if __name__ == "__main__": #if this is the main file, parse the command args
	parser = argparse.ArgumentParser(description="Module that downloads and stores blockchain and course data.")
	parser.add_argument('--course', dest='course', action="store_true", help="Downloads and saves or upgrades historical course data.")
	parser.add_argument('--blockchain', dest='blockchain', action="store_true", help="Downloads and saves or upgrades blockchain data.")
	parser.add_argument('--start', type=int, default=0, help='From which block to start downloading.')
	parser.add_argument('--end', type=int, default=None, help='Until which block to download.')
	parser.set_defaults(course=False)
	parser.set_defaults(blockchain=False)

	args, _ = parser.parse_known_args()

	if args.course: downloadCourse()
	if args.blockchain:
		downloadBlockchain(args.start, args.end)