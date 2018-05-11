

def smaValues(values, periods=10, fillWithNone=True):
	newValues = []

	for i, val in enumerate(values):
		if i < periods -1 and fillWithNone:
			newValues.append(None)
		else:
			newValues.append(sum(values[i-(periods-1): i+1]) / float(periods)) #the avg of last 'periods' periods

	return newValues

def emaValues(values, periods=10):
	newValues = []

	multiplier = 2 / float(periods + 1)

	smaVals = smaValues(values, periods=periods)

	initialSMA = False

	for i, sma in enumerate(smaVals):
		if sma is None:
			newValues.append(None)
			continue
		
		if not initialSMA:
			ema = sma #the first value is the first available SMA
			initialSMA = True
		else:
			ema = (values[i] - newValues[i-1]) * multiplier + newValues[i-1]
		newValues.append(ema)

	return newValues

def average(values):
    if not values:
        return 0
    return sum(values) / len(values)

class Average():
    def __init__(self):
        self.values = []

    def add(self, value):
        self.values.append(value)

    def get(self):
        return average(self.values)