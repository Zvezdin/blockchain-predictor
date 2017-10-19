import pytest
import pandas as pd
import numpy as np

from datetime import datetime as dt
import sys, os
sys.path.insert(0, os.path.realpath('./dataset_models'))
from dataset_model import DatasetModel

def test_normalization():
	#normal input
	res = DatasetModel.basic_normalization(np.array([1,2,3,4,5]))

	assert np.array_equal(res, np.array([0, 0.25, 0.5, 0.75, 1]))

	#really large input
	res = DatasetModel.basic_normalization(np.array([1e+20, 2e+20, 3e+20, 4e+20, 5e+20]))

	assert np.array_equal(res, np.array([0, 0.25, 0.5, 0.75, 1]))

	#really small input
	res = DatasetModel.basic_normalization(np.array([1e-5, 2e-5, 4e-5, 5e-5]))

	assert np.array_equal(res, np.array([0, 0.25, 0.75, 1]))

	#negative input
	res = DatasetModel.basic_normalization(np.array([-5, -4, -3, -2, -1]))

	assert np.array_equal(res, np.array([0, 0.25, 0.5, 0.75, 1]))

