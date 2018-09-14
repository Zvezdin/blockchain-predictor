import numpy as np

from .postprocessor import Postprocessor


class PostprocessorStani(Postprocessor):

	def __init__(self):
		super().__init__()

		self.requires = ["highPrice"]
		self.name = "%s_stani"
		self.previousTicks = 1
		self.nextTicks = 2 #we calculate the value for a given moment based on the previous value and the preceding 2.
						   #and when we predict, it will be based on the current value and preceding 3.

	def calculateAction(self, data):
		assert(len(data) == self.previousTicks + self.nextTicks + 1)

		#print(data)

		point_val = data[0]
		max_val = max(data)
		min_val = min(data)

		max_growth = (max_val - point_val) * 100 / max_val
		min_growth = (min_val - point_val) * 100 / point_val
		# Classic
		condition = max_growth > 0.8 and min_growth > -0.2

		if False:
			print('-----------------------------')
			print(list(data))
			print('Point_Value:', point_val)
			print('Max_Value:', max_val)
			print('Min_Value:', min_val)
			print('Max_Growth:', max_growth)
			print('Min_Growth:', min_growth)
			print('Poin_of_Interest:', condition)

		return int(condition)
