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

if __name__ == "__main__": #if this is the main file, parse the command args
	np.set_printoptions(precision=3, linewidth=180)

	parser = argparse.ArgumentParser(description="Tool that can read historical data from the db or from a file and visualize it as a graph.")
	parser.add_argument('data1', type=str, help='A pickled file #1, output from training.')
	parser.add_argument('--data2', type=str, default=None, help='A pickled file #1, output from training.')
	parser.add_argument('--data3', type=str, default=None, help='A pickled file #1, output from training.')
	parser.add_argument('--key', type=str, default="R2", help='The name of the score to plot.')
	args, _ = parser.parse_known_args()

	files = [args.data1]
	if args.data2 is not None:
		files.append(args.data2)
	if args.data3 is not None:
		files.append(args.data3)

	print(files)

	data = []

	for f in files:
		with open(f, 'rb') as fi:
			data.append(pickle.load(fi))

	print(len(data))
	
	for i, dat in enumerate(data):
		print(files[i])
		plt.plot(dat[args.key], label=files[i])

	print(data[0].keys())

	plt.title('Comparison of training progress')
	plt.legend(loc='upper left')
	plt.show()