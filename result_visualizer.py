import pickle
import argparse
import dateutil.parser
import os
import os.path
import time

import matplotlib as mpl
#mpl.use('Agg')
import matplotlib.animation as animation
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
from matplotlib.gridspec import GridSpec

def plot(values, dates, title=''):
		plt.plot(dates, values)
		plt.xlabel = 'Timeline'
		plt.title(title)
		plt.show()

def plotImage(val, filename=None):
	if filename is not None and os.path.isfile(filename):
		return #no need to re-render if it already exists
	plt.clf()
	plt.imshow(val, interpolation="nearest")
	plt.colorbar()
	if filename is None:
		plt.show()
	else:
		print("Saving file %s." % filename)
		plt.savefig(filename)

def drawAccuracyGraph(histories, titles=None, filename=None, maxCols=3):
	fig = plt.figure(figsize=(16*2, 9*2))

	if type(histories) != list:
		histories = [histories]

	cols = len(histories[0].keys())
	rows = 1

	if cols > maxCols:
		rows = cols // maxCols
		if cols % maxCols > 0:
			rows += 1
		cols = maxCols

	gs = GridSpec(rows, cols)

	currCol = 0
	currRow = 0

	for i, measure in enumerate(list(histories[0].keys())):
		plt.subplot(gs[currRow, currCol])

		currCol += 1
		if currCol > maxCols-1:
			currCol = 0
			currRow += 1

		for i, history in enumerate(histories):
			plt.plot(history[measure], label=(titles[i] if titles is not None else None))
			plt.title(measure)
		plt.legend()
	plt.tight_layout()

	if filename is None:
		plt.show()
	else:
		plt.savefig(filename)
		print("Saved graph at %s." % filename)

if __name__ == "__main__": #if this is the main file, parse the command args
	np.set_printoptions(precision=3, linewidth=180)

	parser = argparse.ArgumentParser(description="Tool that can read historical data from the db or from a file and visualize it as a graph.")
	parser.add_argument('data', type=str, nargs='*', help='A pickled file or file list, output from training.')
	parser.add_argument('--key', type=str, default=None, help='Display a specific score')
	args, _ = parser.parse_known_args()

	files = args.data

	print(files)

	data = []

	for f in files:
		with open(f, 'rb') as fi:
			data.append(pickle.load(fi)['history'])

	print(len(data))
	
	drawAccuracyGraph(data, titles=files)
	
	print(data[0].keys())

	#plt.title('Comparison of training progress')
	#plt.legend(loc='upper left')
	#plt.show()