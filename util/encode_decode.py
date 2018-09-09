import codecs
import pickle

import numpy as np

marker = 'EnC0D3D'

def encodeObject(obj):
	return codecs.encode(pickle.dumps(obj, -1), "base64").decode()

def decodeObject(encoded):
	return pickle.loads(codecs.decode(encoded.encode(), "base64"))

def decodeDataframe(data):
	for col in data.columns:
		if isinstance(data.iloc[0][col], str):# and data.iloc[0][col].startswith(marker):
			data[col] = data[col].apply(lambda x: decodeObject(x.replace(marker, '')) if (isinstance(x, str) and marker in x) else x) #remove the marker and decode

	return data

def encodeDataFrame(data):
	for col in data.columns:
		if isinstance(data.iloc[0][col], np.ndarray):
			data[col] = data[col].apply(lambda x: marker+encodeObject(x)) #put a marker up front so we know when to decode

	return data