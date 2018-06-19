from http.server import *
from urllib.parse import urlparse
from time import sleep
import json
import abc
import dateutil.parser
from datetime import datetime as dt
import pickle
import traceback

import numpy as np

import database_tools as db
from property_generator import subsetByDate, isProperty
from tools import decodeDataframe

class Provider(abc.ABC):
	def __init__(self):
		self.name = None

	@abc.abstractmethod
	def list_ids(self):
		pass

	@abc.abstractmethod
	def has_id(self, id):
		pass

	@abc.abstractmethod
	def read_metadata(self, id):
		pass

	@abc.abstractmethod
	def read_id(self, id, start=None, end=None, form=None):
		"""Method that returns all data about a given ID in STRING form."""

class DummyProvider(Provider):
	def __init__(self):
		super().__init__()
		self.ids = ["accountBalanceDistribution_log1_2", "accountBalanceDistribution_log1_2_10max", "accountBalanceDistribution_log1_2_10min", "accountBalanceDistribution_log1_2_ema", "accountBalanceDistribution_log1_2_sma", "activeAccounts", "activeAccountsShare", "avgBalOfLocal", "avgBalOfRecent", "avgGasByTopX", "avgGasUsed", "avgVal", "avgValFromRecent", "avgValFromTopX", "avgValToNew", "avgValToTopX", "balanceLastSeenDistribution_log1_2", "balanceLastSeenDistribution_log1_2_sma", "block", "blockDifficulty", "blockSize", "closePrice", "contractBalanceLastSeenDistribution_log1_2_v2", "contractVolumeInERC20Distribution_log1_2_v2_stateless", "gasLimit", "gasPrice", "gasUsed", "gasUsedByNew", "highPrice", "log", "lowPrice", "networkHashrate", "openPrice", "recentAccounts", "shareTracesFromRecent", "stickPrice", "tick", "topXCount", "trace", "traceBl", "traceTx", "tracesFromRecent", "transactionCount", "tx", "uniqueAccounts", "volumeEnteringTopX", "volumeFrom", "volumeLeavingTopX", "volumeTo"]
		self.name = 'dummy'
	
	def list_ids(self):
		return self.ids

	def has_id(self, id):
		return id in self.ids

	def read_metadata(self, id):
		if not self.has_id(id):
			raise ValueError("Id %s doesn't exist!" % id)
		return {'shape': (3,), 'frequency': '60', 'from': '2017-2-1', 'to': '2017-3-16'}

	def read_id(self, id, start=None, end=None, form=None):
		if not self.has_id(id):
			raise ValueError("Id %s doesn't exist!" % id)
		return "DIMITRY WHAT'S UP MY FRIEND"

class BlockchainProvider(Provider):
	def __init__(self):
		super().__init__()
		self.name = 'blockchain'
		self.store = db.getChunkstore()
		self.id_cache = None
	
	def list_ids(self):
		if self.id_cache is None:
			self.id_cache =  [x for x in self.store.list_symbols() if isProperty(x)]
		return self.id_cache

	def has_id(self, id):
		return id in self.list_ids()

	def read_metadata(self, id):
		if not self.has_id(id):
			raise ValueError("Id %s doesn't exist!" % id)
		meta = db.loadMetadata(self.store, id)

		for key in meta:
			if isinstance(meta[key], dt):
				meta[key] = str(meta[key]) #convert datetime objects to string for JSON serialization
		
		#add frequency data
		meta['frequency'] = 60*60 #TODO: Fix this hardcoded variable. this is seconds inbetween signals.

		#add shape data
		latestRow = db.getLatestRow(self.store, id) #get last record of time series
		val = latestRow[id].values[0] #its value
		if isinstance(val, str): #some values are pickled; database limitations
			val = db.decodeObject(val)
		if isinstance(val, float) or isinstance(val, int):
			shape = (1,)
			print("number!")
		elif isinstance(val, np.ndarray):
			shape = val.shape
		else:
			raise ValueError("Unsupported type of value: %s (value: %s)" % (str(type(val)), str(val)))
		meta['shape'] = shape

		return meta

	def read_id(self, id, start=None, end=None, form=None):
		if form is None:
			form = 'csv'
		
		if not self.has_id(id):
			raise ValueError("Id %s doesn't exist!" % id)

		meta = db.loadMetadata(self.store, id)
		if start < meta['start'] or end > meta['end']:
			raise ValueError("Given interval (%s, %s) does not fit in the property's interval (%s, %s)." % \
			(str(start), str(end), str(meta['start']), str(meta['end'])))

		data = db.loadData(self.store, id, start, end, filter = True)

		#due to database limitations, the values of the dataframe MAY be pickled (if it's a distribution). Let's unpickle them
		data = decodeDataframe(data)

		#debug & info
		print(data.head(3))
		print(data.tail(3))

		if form == 'csv':
			out = data.to_csv()
		elif form == 'json':
			out = data.to_json()
		elif form == 'pickle':
			out = pickle.dumps(data, pickle.HIGHEST_PROTOCOL)
		else:
			raise ValueError("Given format %s is unsupported!" % form)

		return out

class MasterProvider():
	def __init__(self):
		self.providers = [DummyProvider(), BlockchainProvider()]

	def handle_request(self, args):
		self.key_exists(args, 'method')
		method = args['method']

		if method == 'list_providers':
			return json.dumps([x.name for x in self.providers])

		self.key_exists(args, 'provider')
		
		provider = [x for x in self.providers if x.name == args['provider']]
		if len(provider) != 1:
			raise ValueError("Incorrect given provider %s." % args['provider'])
		provider = provider[0]
			
		if method == 'list':
			items = provider.list_ids()

			return json.dumps(items)
		elif method == 'metadata':
			self.key_exists(args, 'id')

			metadata = provider.read_metadata(args['id'])
			print(metadata)
			return json.dumps(metadata)
		elif method == 'read':
			self.key_exists(args, 'id')
			start = args.get('start', None)
			if start is not None:
				start = dateutil.parser.parse(start)
			end = args.get('end', None)
			if end is not None:
				end = dateutil.parser.parse(end)
			form = args.get('form', None)
			return provider.read_id(args['id'], start=start, end=end, form=form)

	def key_exists(self, obj, key):
		if key not in obj:
			raise ValueError("No %s key in data!" % key)

master = MasterProvider()

class RequestHandler(BaseHTTPRequestHandler):
	def _set_headers(self, typ, len_data):
		self.send_response(200)
		self.send_header('Content-type', typ)
		self.send_header('Content-Length', len_data)
		#the next line seems problematic. We'll do without this header for now.
		#self.send_header('Transfer-Encoding', 'chunked')
		self.end_headers()
	
	def _send_error(self, num):
		self.send_response(num)
		self.end_headers()

	def do_GET(self):
		print(self.client_address, self.command, self.path)
		parsed = urlparse(self.path)
		query_text = parsed.query

		try:
			query = dict(qc.split("=") for qc in parsed.query.split("&"))
			for key in query:
				query[key] = query[key].replace('%20', ' ')
		except ValueError:
			self._send_error(400)
			return

		print("query:", query)

		try:
			res = master.handle_request(query)
		except ValueError as e:
			print(traceback.print_exc())
			self._send_error(400)
			return

		if res is not None:
			self._set_headers('text/json', len(res))
			if isinstance(res, str):
				res = res.encode('utf-8')
			self.send_data_chunked(res, self.wfile)

	def send_data_chunked(self, data, stream, max_length=3):
		i = 0
		while True:
			chunk = data[i:i+max_length]
			if len(chunk) > 0:
				self.send_data(chunk, stream)
				i += max_length
			else:
				break

	def send_data(self, data, stream):
		stream.write(data)

def run(server_class=HTTPServer, handler_class=RequestHandler):
	server_address = ('', 8000)
	httpd = server_class(server_address, handler_class)
	httpd.serve_forever()

run()

#REQUEST DOCUMENTATION:

#Possible GET arguments: method, provider, id, start, end, form

#method=list_providers (JSON)
## Lists all available providers. All other methods requred a given provider as a parameter

#method=list (JSON)
## Lists all available IDs from the given provider

#method=metadata (JSON)
## Returns the metadata about a given ID as a parameter

#method=read (STRING, Chunked)
## Reads all data about the given ID. By default, it returns the string representation of the values in csv format.
## To change the format, use the 'form' parameter. Accepted formats are: json, csv, pickle
## You can request a given interval by using the 'start' and 'end' arguments. The format is 'YYYY-MM-DD HH:MM' or just 'YYYY-MM-DD'. Time in GMT.

#EXAMPLES:
#?method=list_providers
#?method=list&provider=blockchain
#?method=read&provider=blockchain&id=avgValToTopX&form=pickle
#?method=read&provider=blockchain&id=avgValToTopX&form=csv&start=2016-01-01%2000:00:00&end=2016-03-01%2003:21:30
