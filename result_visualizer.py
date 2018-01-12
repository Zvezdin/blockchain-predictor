import pickle
import argparse
import dateutil.parser
import os
import os.path
import time
import functools

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

def drawAccuracyGraph(histories, filename=None, maxCols=3):
	fig = plt.figure(figsize=(16*2, 9*2))

	cols = len(histories.keys())
	rows = 1

	if cols > maxCols:
		rows = cols // maxCols
		if cols % maxCols > 0:
			rows += 1
		cols = maxCols

	gs = GridSpec(rows, cols)

	currCol = 0
	currRow = 0

	for measure in list(histories.keys()):
		plt.subplot(gs[currRow, currCol])

		currCol += 1
		if currCol > maxCols-1:
			currCol = 0
			currRow += 1

		for run in histories[measure]:
			plt.plot(run['data'], label=(run['file']))
		plt.title(measure)
		plt.legend()
	plt.tight_layout()

	if filename is None:
		plt.show()
	else:
		plt.savefig(filename)
		print("Saved graph at %s." % filename)

#format of results is a list of dicts with key 'file' and 'score', being a list of scores
def sortResults(results, ascending=True, index=-1, func=None):
	def compare(x, y):
		if func is None:
			res = x['data'][index] - y['data'][index]
		else:
			res = func(x['data']) - func(y['data'])
		if not ascending:
			res = -res
		return res

	return sorted(results, key=functools.cmp_to_key(compare)) #convert to python's current format


def init():
	np.set_printoptions(precision=3, linewidth=180)

	parser = argparse.ArgumentParser(description="Tool that can read historical data from the db or from a file and visualize it as a graph.")
	parser.add_argument('data', type=str, nargs='*', help='A pickled file or file list, output from training.')
	parser.add_argument('--key', type=str, default=None, help='Display a specific score.')
	parser.add_argument('--best', type=int, default=None, help='Only display the best N results.')
	args, _ = parser.parse_known_args()

	files = args.data

	print(files)

	histories = []

	data = {}

	titles = files.copy()

	for f in files:
		with open(f, 'rb') as fi:
			hist = pickle.load(fi)['history']
			histories.append(hist)

	for i, hist in enumerate(histories):
		if args.key is not None:
			hist = {args.key: hist[args.key]}
		
		for key in hist:
			if key not in data:
				data[key] = []
			data[key].append({'file': files[i], 'data': hist[key]})

	for key in data:
		if key == 'val_loss' or key == 'loss' or key == 'rmse' or key == 'custom':
			data[key] = sortResults(data[key], ascending=True)
		elif key == 'R2' or key == 'sign':
			data[key] = sortResults(data[key], ascending=False)
		else:
			raise ValueError("Unexpected and unknown metric '%s'." % key)
		print("Best for %s: are as follows" % (key))
		for i in range(5):
			print("#%d %s is %f at %s" % (i+1, key, data[key][i]['data'][-1], data[key][i]['file']))

		if args.best is not None:
			data[key] = data[key][:args.best]


	drawAccuracyGraph(data)

	#plt.title('Comparison of training progress')
	#plt.legend(loc='upper left')
	#plt.show()

if __name__ == "__main__": #if this is the main file, parse the command args
	init()