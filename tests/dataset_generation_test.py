import pytest

from time import sleep
import pickle
import sys, os
sys.path.insert(0, os.path.realpath('./'))

import dataset_generator as ds
import database_tools as db

def test_labels():
	lib = db.getChunkstore()

	#get the whole history of the course
	course = db.loadData(lib, db.dbKeys['tick'], None, None, False)

	filename = "data/dataset_test.pickle"

	start = None
	end = None

	#generate a sample dataset
	ds.run("matrix", "openPrice,closePrice,gasPrice", start, end, filename, "boolean", False)

	sleep(1) #delay between saving and reading

	with open(filename, 'rb') as f:
		res = pickle.load(f) #load the result
	i=0

	indices = course.index.values

	for j, date in enumerate(res['dates']):
		#
		i = course.index[course['date'] == date]
		#while course.get_value(indices[i], 'date') != date:
		#	i+=1
		
		currPrice = course.get_value(i[0], 'close')
		nextPrice = course.get_value(i[0]+1, 'close')

		#print("Checking prices %s %s with value of label %s" % (currPrice, nextPrice, res['labels'][j]))

		if res['labels'][j] != (nextPrice > currPrice):
			print("Debug info: Date %s at course index %s (len=%s). Curr / next prices are %s and %s." % (date, i, len(course), currPrice, nextPrice))
			assert False

	assert True