import pickle
import argparse
import dateutil.parser
import os, sys
import os.path
import time

import matplotlib as mpl
#mpl.use('Agg')
import matplotlib.animation as animation
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.realpath('dataset_models')) #needed to load recent datasets
from imageNormalizer import ImageNormalizer
from basicNormalizer import BasicNormalizer
from aroundZeroNormalizer import AroundZeroNormalizer

import database_tools as db


def plot(values, dates, title=''):
		plt.plot(dates, values)
		plt.xlabel = 'Timeline'
		plt.title(title)
		plt.show()

def plotImage(val, filename=None, hbar=False):
	if filename is not None and os.path.isfile(filename):
		return #no need to re-render if it already exists
	plt.clf()

	plt.imshow(val, interpolation="nearest")
	plt.colorbar(orientation='horizontal' if hbar else 'vertical')

	if filename is None:
		plt.show()
	else:
		print("Saving file %s." % filename)
		plt.savefig(filename)

def createAnimation(frames, dates):
	fig = plt.figure()
	ax = fig.add_subplot(111)

	ims = []

	#for i, frame in enumerate(frames):
	#	im = plt.imshow(frame, animated=True)
	#	tit = plt.annotate(str(dates[i]), (-1,-1), animated=True)
	#	#cb = plt.colorbar()
	#	ims.append([im, tit])
	cv0 = frames[0]
	im = ax.imshow(cv0, origin='lower') # Here make an AxesImage rather than contour
	cb = fig.colorbar(im)
	tx = ax.set_title(str(dates[0]))

	def animate(i):
		arr = frames[i]
		vmax     = np.max(arr)
		vmin     = np.min(arr)
		im.set_data(arr)
		im.set_clim(vmin, vmax)
		tx.set_text(str(dates[i]))

	ani = animation.FuncAnimation(fig, animate, frames=len(frames), interval=1)

	global args

	ani.save(args.renderTimelapse)

if __name__ == "__main__": #if this is the main file, parse the command args
	np.set_printoptions(precision=3, linewidth=180)

	parser = argparse.ArgumentParser(description="Tool that can read historical data from the db or from a file and visualize it as a graph.")
	parser.add_argument('data', type=str, help='The data to visualize. Can be a filepath to a pickled (single!) dataset or a key in the db.')
	parser.add_argument('--type', type=str, default='file', choices=['key', 'file'], help='What type of data to load and visualize- key from the database or a file.')
	parser.add_argument('--index', type=int, default=0, help='If loading a file, provide the index of the property in the data matrix to be visualized.')
	parser.add_argument('--target', dest='target', action="store_true", help='If visualizing a file, whether or not to visualize the prediction target.')
	parser.add_argument('--start', type=str, default=None, help='The start date. YYYY-MM-DD-HH')
	parser.add_argument('--end', type=str, default=None, help='The end date. YYYY-MM-DD-HH')
	parser.add_argument('--frame', dest='frame', action='store_true', help='Display single frame values')
	parser.add_argument('--trim', dest='trim', action='store_true', help='A frame can be trimmed from values on Y=0 and X=end.')
	parser.add_argument('--log2', dest='log2', action='store_true', help='Scale all account counts by a log2.')
	parser.add_argument('--hbar', dest='hbar', action='store_true', help='Position the colorbar horisontally.')
	parser.add_argument('--renderTimelapse', type=str, default=None, help='Render all frames of a key and save them as a video in the specified path.')
	parser.set_defaults(frame=False)
	parser.set_defaults(trim=False)
	parser.set_defaults(log2=False)
	parser.set_defaults(hbar=False)
	parser.set_defaults(target=False)

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
					frame = dataset['dataset'][-1, -1, :, :] #shape is samples, layers, width, height
					print(frame)
					
					print(dataset['dataset'].shape)

					print(dataset['dates'][-1])

					plotImage(frame)
					if args.target:
						plot(dataset['labels'], dataset['dates'], 'Correct labels')
	elif args.type=='key':
		prop = args.data

		data = db.loadData(db.getChunkstore(), prop, start, end, True)

		if type(data.iloc[0][prop]) == str: #if the property values have been encoded, decode them
			print("Running numpy array Arctic workaround for prop %s..." % prop)
			data[prop] = data[prop].apply(lambda x: db.decodeObject(x))
		
		values = data[prop].values
		dates = data['date'].values

		if type(values[0]) != np.ndarray:
			plot(values, dates, 'Value of '+prop)
		else: #if we are dealing with complex property, visualize it
			if args.renderTimelapse is not None:
				rangeGen = range(len(values))
				frames = []
			else:
				rangeGen = range(len(values)-1, len(values))
			for i in rangeGen:
				val = values[i]
				print(val.shape)

				if args.trim:
					val = val[1:, :-1]

				if args.log2:
					if np.min(val) < 0: #if we have relative values
						val -= np.min(val) #turn all negatives to positives

					val = np.log2(val)
					val[val<0] = 0 #log if 0 is -inf

				print(val.shape)
				date = dates[i]

				if len(val.shape) != 2:
					print("ERROR: Unsupported property value format with shape %s. Supported shapes are 2D." % str(val.shape))
				elif args.renderTimelapse is None:
					print(val)
					print(val.shape)
					print(date)
					plotImage(val, hbar = args.hbar)
				else:
					frames.append(val)
			if args.renderTimelapse is not None:
				createAnimation(frames, dates)
