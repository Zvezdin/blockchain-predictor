import sys, os
sys.path.insert(0, os.path.realpath('./property_util'))

import pytest

from sorted_value_dict import SortedValueDict

def testAccess():
	a = SortedValueDict(increasing=False)

	a['four'] = 4
	a['three'] = 3

	assert(a['four'] == 4)
	assert(a['three'] == 3)

	b = SortedValueDict(increasing=True)

	b['four'] = 4
	b['three'] = 3

	assert(b['four'] == 4)
	assert(b['three'] == 3)

def testIncreasingIteration():
	a = SortedValueDict(increasing=True)

	a['four'] = 4
	a['three'] = 3

	vals = a.values()

	assert(list(vals) == [3,4])

def testDecreasingIteration():
	a = SortedValueDict(increasing=False)

	a['four'] = 4
	a['three'] = 3

	vals = a.values()

	assert(list(vals) == [4,3])

def testIterator():
	a = SortedValueDict(increasing=False)

	a['four'] = 4
	a['three'] = 3

	vals = []
	
	for x in a:
		vals.append(a[x])

	assert(vals == [4,3])

	a['one'] = 1
	a['five'] = 5

	vals = []

	for x in a:
		vals.append(a[x])

	assert(vals == [5, 4, 3, 1])
