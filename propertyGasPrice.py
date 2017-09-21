from property import Property

class PropertyGasPrice(Property):
	def __init__(self):
		self.name = ""

	def processTick(self, block, tx, course):
		index = tx.columns.searchsorted('gasPrice')

		val = tx.values

		print(val, tx)

		avg = 0
		for i in range(len(val)):
			avg += int(val[i][index])
		avg /= len(val)

		print("Calculated average of", avg)

		return avg