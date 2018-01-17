import pytest
import numpy as np

from datetime import datetime as dt
import sys, os
sys.path.insert(0, os.path.realpath('./dataset_models'))

from aroundZeroNormalizer import AroundZeroNormalizer
from basicNormalizer import BasicNormalizer
from imageNormalizer import ImageNormalizer

def test_image():
	a = np.random.random((2,3))

	for algorithm in [BasicNormalizer, AroundZeroNormalizer, ImageNormalizer]:
		norm = algorithm(a)
		std = np.std(a)
		b = norm.transform(a)
		b = norm.inverse_transform(b)

		print(a,b)

		assert(np.allclose(a,b))