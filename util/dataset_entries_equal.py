import argparse

import numpy as np

from database import instance as db

class DatabaseContext():
	def __init__(self, loc):
		self.loc = loc
	
	def __enter__(self):
		if self.loc is not None:
			db.open(self.loc)
		else:
			db.open()

	def __exit__(self, exc_type, exc_value, traceback):
		db.close()

def run(key, key2=None, db1=None, db2=None):
	if key2 is None:
		key2 = key
	
	if db2 is None:
		db2 = db1

	with DatabaseContext(db1):
		met1 = db.getMeatdata(key)

	with DatabaseContext(db2):
		met2 = db.getMeatdata(key2)

	met = met1.copy()
	met['start'] = max(met1['start'], met2['start'])
	met['end'] = min(met1['end'], met2['end'])

	print("Final interval: ", met)

	with DatabaseContext(db1):
		dat1 = db.get(key, start=met['start'], end=met['end'])
	
	with DatabaseContext(db2):
		dat2 = db.get(key2, start=met['start'], end=met['end'])

	val1 = dat1.values
	val2 = dat2.values

	for x in range(val1.shape[0]):
		for j in range(val1[x].shape[0]):
			v1 = val1[x][j]
			v2 = val2[x][j]

			if isinstance(v1, np.ndarray):
				assert(np.array_equal(val1[x][j], val2[x][j]))
			else:
				assert(False)

	print("Success!")

if __name__ == "__main__": #if this is the main file, parse the command args
	parser = argparse.ArgumentParser(description="Module that gathers requested entries from a database (or two) and compares them by value.")
	parser.add_argument('key', help="The database entry.")
	parser.add_argument('--key2', help='The database entry from the second database, if different.')
	parser.add_argument('--db1', default=None, help="Location for the first database.")
	parser.add_argument('--db2', default=None, help="Location for the second database.")

	args, _ = parser.parse_known_args()

	run(args.key, key2=args.key2, db1=args.db1, db2=args.db2)