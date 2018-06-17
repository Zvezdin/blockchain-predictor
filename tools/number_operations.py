def exp_to_int(s):
	"""
	Converts numbers like 1.01e+2 or 1.007783151912803607421e+21 to integers.
	By default, these are parsed by the float function and lose precision
	"""
	if 'e' in s: #if it is exponential
		exp = int(s.split('+')[1])
		(whole, tmp) = s.split('.')
		frac = tmp.split('e')[0]
		assert(len(frac) <= exp)

		diff = exp - len(frac) #must be positive
		num = int(whole + frac)
		num = num*(10**diff)
	else:
		num = int(s)

	return num