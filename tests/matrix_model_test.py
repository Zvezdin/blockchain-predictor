import pytest
import pandas as pd
import numpy as np

from datetime import datetime as dt
import sys, os
sys.path.insert(0, os.path.realpath('./dataset_models'))
from dataset_model import DatasetModel

from matrix_model import MatrixModel

def test_frame():
	dates = np.array([dt(2017,1,1), dt(2017,1,2), dt(2017,1,3), dt(2017,1,4), dt(2019,3,1), dt(2019,3,7)])

	a = pd.DataFrame({'a': np.array([1,2,3,4,5,5]), 'date': dates}, index=[10,20,30,40,70,80])
	b = pd.DataFrame({'b': np.array([5,4,3,2,1,1]), 'date': dates})
	c = pd.DataFrame({'c': np.array([2300e+10, 4700e+10, 9800e+9, 4900e+10, 5690e+10, 5690e+10]), 'date': dates})
	d = pd.DataFrame({'d': np.array([1000e+11, 1, -10, 50e+5, 0.03, 0.03]), 'date': dates})
	e = pd.DataFrame({'e': np.array([-56, -6, -19, -145, 0, 0]), 'date': dates})

	properties = [a,b,c,d,e]

	model = MatrixModel()

	res, resDates, _ = model.generate(properties, {'normalize': False, 'window': 3, 'blacklistTarget': False, 'target': 'a'})

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

	expectedDates = dates[2:-1]

	print("We're expecting:")
	print(expectation, expectedDates)

	assert np.array_equal(res, expectation) and np.array_equal(expectedDates, resDates)

def test_regularization():
	model = MatrixModel()

	dates = np.array([dt(2017,1,1), dt(2017,1,2), dt(2017,1,3), dt(2017,1,4), dt(2019,3,1), dt(2019,3,7)])

	a = pd.DataFrame({'a': np.array([1,2,3,4,5,5]), 'date': dates}, index=[10,20,30,40,70,80])
	b = pd.DataFrame({'b': np.array([5e+20, 4e+20, 3e+20, 2e+20, 1e+20, 1e+20]), 'date': dates})

	properties = [a,b]

	res, resDates, _ = model.generate(properties, {'normalize': True, 'defaultNormalization': 'basic', 'window': 3, 'blacklistTarget': False, 'target': 'a'})

	expectation = np.ndarray((3, 3, 2))

	expectation[0] = np.array([[0., 1],
								[0.25, 0.75],
								[0.5, 0.5]])

	expectation[1] = np.array([[0.25, 0.75],
								[0.5, 0.5],
								[0.75, 0.25]])

	expectation[2] = np.array([[0.5, 0.5],
								[0.75, 0.25],
								[1, 0]])
							

	expectedDates = dates[2:-1]

	print("We're expecting:")
	print(expectation, expectedDates)

	print("But we got:")
	print(res, resDates, res==expectation)

	assert np.array_equal(res, expectation) and np.array_equal(expectedDates, resDates)