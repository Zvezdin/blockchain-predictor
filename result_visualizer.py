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

def basename(f):
	return os.path.split(f)[-1]

def getCompareFuncBasedOnKey(key):
	if key == 'val_loss' or key == 'loss' or key == 'rmse' or key == 'custom':
		return min
	elif key == 'R2' or key == 'sign':
		return max

def init():
	np.set_printoptions(precision=3, linewidth=180)

	parser = argparse.ArgumentParser(description="Tool that can read historical data from the db or from a file and visualize it as a graph.")
	parser.add_argument('data', type=str, nargs='*', help='A pickled file or file list, output from training.')
	parser.add_argument('--keys', type=str, default=None, help='Filter out only one or multiple keys, separated by a comma.')
	parser.add_argument('--best', type=int, default=None, help='Only display the best N results.')
	parser.add_argument('--detail', dest='detail', action='store_true', help='Display the scores in detail.')
	parser.set_defaults(detail=False)
	parser.add_argument('--no-display', dest='display', action='store_false', help='Do not plot any graphs.')
	parser.set_defaults(display=True)
	args, _ = parser.parse_known_args()

	files = args.data

	for i in range(len(files)):
		if '\n' in files[i]:
			s = files[i].split('\n')
			subfiles = [f for f in s if f != '' and not f.isspace()]
			files[i] = None
			files.extend(subfiles)
	files = [f for f in files if f is not None]
	
	#print(files)
	
	histories = []

	data = {}

	titles = files.copy()

	keys = args.keys.split(',') if args.keys is not None else None

	for f in files:
		with open(f, 'rb') as fi:
			element = pickle.load(fi)
			hist = element['history']
			histories.append(hist)

	for i, hist in enumerate(histories):
		if keys is not None:
			hist2 = {}
			for key in keys:
				hist2[key] = hist[key]
			hist = hist2

		for key in hist:
			if key not in data:
				data[key] = []
			filename = basename(files[i]) #extract filename from path
			data[key].append({'file': filename, 'data': hist[key]})

	for key in data:
		if key == 'val_loss' or key == 'loss' or key == 'rmse' or key == 'custom':
			func = min
			data[key] = sortResults(data[key], ascending=True, func=func)
		elif key == 'R2' or key == 'sign':
			func = max
			data[key] = sortResults(data[key], ascending=False, func=func)
		else:
			raise ValueError("Unexpected and unknown metric '%s'." % key)
		print("Best for %s: are as follows" % (key))
		for i in range(min(5, len(data[key]))):
			val = data[key][i]['data'][-1] if func is None else func(data[key][i]['data'])
			print("#%d %s is %f at %s" % (i+1, key, val, data[key][i]['file']))

		if args.best is not None:
			data[key] = data[key][:args.best]

	if args.detail:
		resLines = ""
		joiner = ' & '
		for i, hist in enumerate(histories):
			print("Detailed results for %s." % (basename(files[i])))
			best = []
			headers = []

			for key in (hist if keys is None else keys):
				best.append(getCompareFuncBasedOnKey(key)(hist[key]))
				headers.append(key)
			
			print(headers)
			print(best)

			commLine = '%' + basename(files[i]) + '\n'

			resLine = str.join(joiner, ("%f" % val for val in best)) + '\\\\\n'

			resLines += commLine
			resLines += resLine

			print(str.join(joiner, headers))
			print(resLine)
		print("All result lines for conveninece:")
		print(resLines)

	if args.display:
		drawAccuracyGraph(data)

	#plt.title('Comparison of training progress')
	#plt.legend(loc='upper left')
	#plt.show()

if __name__ == "__main__": #if this is the main file, parse the command args
	init()