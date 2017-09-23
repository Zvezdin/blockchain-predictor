from property import Property

class PropertyGasPrice(Property):
	def __init__(self):
		self.name = "gasPrice"

	def processTick(self, block, tx, course):
		index = tx.columns.searchsorted('gasPrice')

		val = tx.values

		avg = 0
		for i in range(len(val)):
			avg += int(val[i][index])
		if avg == 0 or len(val) == 0: print(tx) #debug
		avg /= len(val)

		return avg