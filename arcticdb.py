from arctic import Arctic
from arctic import TICK_STORE
from arctic import CHUNK_STORE
from arctic.date import DateRange

import pandas as pd
from datetime import timezone, datetime as dt
import time

import pickle
import json

tickSymbol = 'test2'

store = Arctic('localhost')

chunkStore = store['chunkstore']
#store.initialize_library('name', lib_type=TICK_STORE)

def loadRawData():

    start = time.time()
    with open('data/poloniex_price_data.json') as json_data:
        print(json_data)
        loadedData = json.load(json_data)
        print("Loading the data took "+str(time.time() - start)+" seconds")
        return loadedData

    return [
        {"date":1439014500,"high":333,"low":1.61,"open":1.65,"close":1.75,"volume":75.15,"quoteVolume":45,"weightedAverage":1.67},
        {"date":1439014800,"high":1.85,"low":1.85,"open":1.85,"close":1.85,"volume":14.5786546,"quoteVolume":7.88035384,"weightedAverage":1.85},
        {"date":1439015100,"high":1.85,"low":1.85,"open":1.85,"close":1.85,"volume":0.296,"quoteVolume":0.16,"weightedAverage":1.85},
        {"date":1439015400,"high":1.85,"low":1.85,"open":1.85,"close":1.85,"volume":0.16611858,"quoteVolume":0.08979383,"weightedAverage":1.85},
        {"date":1439015700,"high":1.85,"low":1.85,"open":1.85,"close":1.85,"volume":0,"quoteVolume":0,"weightedAverage":1.85},
        {"date":1439016000,"high":1.85,"low":1.85,"open":1.85,"close":1.85,"volume":0,"quoteVolume":0,"weightedAverage":1.85},
        {"date":1439016300,"high":420,"low":1.85,"open":1.85,"close":1.85,"volume":0,"quoteVolume":0,"weightedAverage":1.85},
        {"date":1439016600,"high":1.71,"low":1.71,"open":1.71,"close":1.71,"volume":20.52,"quoteVolume":12,"weightedAverage":1.71},
        {"date":1439016900,"high":1.71,"low":1.71,"open":1.71,"close":1.71,"volume":0,"quoteVolume":0,"weightedAverage":1.71},
        {"date":1439017200,"high":1.71,"low":1.71,"open":1.71,"close":1.71,"volume":0,"quoteVolume":0,"weightedAverage":1.71},
        {"date":1439017500,"high":1.71,"low":1.71,"open":1.71,"close":1.71,"volume":0,"quoteVolume":0,"weightedAverage":1.71},
        {"date":1439017800,"high":1.75,"low":1.75,"open":1.75,"close":1.75,"volume":0.32584727,"quoteVolume":0.18619844,"weightedAverage":1.75}
    ]

def processRawData(data):

    start = time.time()
    for x in data:
        x['date'] = dt.fromtimestamp(x['date'])
        #x['transactions'] = str(pickle.dumps( [ {'from': 0x1, 'to': 0x2, 'value': 3} for x in range(3) ] ) )
    print("Processing the data took "+str(time.time() - start)+" seconds")

def getDataFrame(data):
    return pd.DataFrame(data)

def saveData(data):
    start = time.time()

    if chunkStore.has_symbol(tickSymbol):
        trimIndex = 0
        records = chunkStore.read(tickSymbol, chunk_range = DateRange(data[trimIndex]['date'])).values
        if len(records) != 0:
            newestDate = records[len(records)-1][1]
            print("newest date is ")
            print(newestDate)

            while trimIndex < len(data) and newestDate >= data[trimIndex]['date'] :
                trimIndex+=1

        if(len(data) == trimIndex): print("Data already written!")
        else: chunkStore.append(tickSymbol, getDataFrame(data[trimIndex:]))
    else:
        df = getDataFrame(data)
        chunkStore.write(tickSymbol, df, chunk_size='M')
    print("Saving the data took "+str(time.time() - start)+" seconds")

def readData():
    df = chunkStore.read(tickSymbol)

    print("Reading the fifth row")

    values = df.values

    print(values[4])

def printData(key, n = 5 ):
    start = time.time()
    df = chunkStore.read(key)
    print(df.head(n))
    print('...')
    print(df.tail(n))
    print(len(df.values))
    print("Displaying the data took "+str(time.time() - start)+" seconds")

#if chunkStore.has_symbol(tickSymbol) : chunkStore.delete(tickSymbol) #used for debugging

data = loadRawData() #get it

print("Loaded data with length "+str(len(data))+" ticks")

processRawData(data) #process a bit to make it suitable for storage

saveData(data[:100])
saveData(data[100:])

printData(tickSymbol)

readData()