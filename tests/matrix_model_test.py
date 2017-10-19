import pytest
import pandas as pd
import numpy as np

from datetime import datetime as dt
import sys, os
sys.path.insert(0, os.path.realpath('./dataset_models'))
from dataset_model import DatasetModel

from matrix_model import MatrixModel

def test():
	dates = np.array([dt(2017,1,1), dt(2017,1,2), dt(2017,1,3), dt(2017,1,4), dt(2019,3,1)])

	a = pd.DataFrame({'a': np.array([1,2,3,4,5]), 'date': dates}, index=[10,20,30,40,70])
	b = pd.DataFrame({'b': np.array([5,4,3,2,1]), 'date': dates})
	c = pd.DataFrame({'c': np.array([2300e+10, 4700e+10, 9800e+9, 4900e+10, 5690e+10]), 'date': dates})
	d = pd.DataFrame({'d': np.array([1000e+11, 1, -10, 50e+5, 0.03]), 'date': dates})
	e = pd.DataFrame({'e': np.array([-56, -6, -19, -145, 0]), 'date': dates})

	properties = [a,b,c,d,e]

	model = MatrixModel()

	res, resDates = model.generate(properties, {'normalize': False, 'window': 3})

	print("Got result from model:")
	print(res, resDates)

	expectation = np.ndarray((3, 3, 5))

	expectation[0] = np.array([[1, 5, 2300e+10, 1000e+11, -56],
								[2, 4, 4700e+10, 1, -6],
								[3, 3, 9800e+9, -10, -19]])

	expectation[1] = np.array([[2, 4, 4700e+10, 1, -6],
								[3, 3, 9800e+9, -10, -19],
								[4, 2, 4900e+10, 50e+5, -145]])

	expectation[2] = np.array([[3, 3, 9800e+9, -10, -19],
								[4, 2, 4900e+10, 50e+5, -145],
								[5, 1, 5690e+10, 0.03, 0]])

	expectedDates = dates[2:]

	print("We're expecting:")
	print(expectation, expectedDates)

	print(expectedDates, resDates)

	assert np.array_equal(res, expectation) and np.array_equal(expectedDates, resDates)