import pickle
import argparse
import dateutil.parser

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

import database_tools as db


def plot(values, datesm, title=''):
		plt.plot(dates, values)
		plt.xlabel = 'Timeline'
		plt.title(title)
		plt.show()

if __name__ == "__main__": #if this is the main file, parse the command args
	parser = argparse.ArgumentParser(description="Tool that can read historical data from the db or from a file and visualize it as a graph.")
	parser.add_argument('data', type=str, help='The data to visualize. Can be a filepath to a pickled (single!) dataset or a key in the db.')
	parser.add_argument('--type', type=str, default='file', choices=['key', 'file'], help='What type of data to load and visualize- key from the database or a file.')
	parser.add_argument('--index', type=int, default=0, help='If loading a file, provide the index of the property in the data matrix to be visualized.')
	parser.add_argument('--start', type=str, default=None, help='The start date. YYYY-MM-DD-HH')
	parser.add_argument('--end', type=str, default=None, help='The end date. YYYY-MM-DD-HH')
	parser.add_argument('--frame', dest='frame', action='store_true', help='Display single frame values')
	parser.set_defaults(frame=False)

	args, _ = parser.parse_known_args()

	start = dateutil.parser.parse(args.start) if args.start is not None else None
	end = dateutil.parser.parse(args.end) if args.end is not None else None

	if args.type=='file':
		with open(args.data, 'rb') as f:
			data = pickle.load(f)
			if type(data) != list:
				data = [data] #turn to single element list
					
			if not args.frame:
				for dataset in data:
					values = dataset['dataset'][:, -1, args.index]
					dates = dataset['dates']

					print(values, dates)

					plot(values, dates, 'Value of '+args.data)
					plot(dataset['labels'], dataset['dates'], 'Correct labels')
			else:
				for dataset in data:
					np.set_printoptions(precision=3)
					frame = dataset['dataset'][-1, -1, :, :] #shape is samples, layers, width, height
					print(frame)
					
					print(dataset['dataset'].shape)
					
					#frame = frame.reshape(frame.shape[0], frame.shape[1], 1) #reshape to width,height, single channel

					plt.imshow(frame, interpolation="nearest")
					plt.colorbar()
					plt.show()
					plt.hist(frame.ravel(), bins=256, range=(0.0, 1.0), fc='k', ec='k')
					plt.show()
	elif args.type=='key':
		data = db.loadData(db.getChunkstore(), args.data, start, end, True)
		values = data[args.data].values
		dates = data['date'].values

		plot(values, dates, 'Value of '+args.data)
	
