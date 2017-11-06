import argparse


if __name__ == "__main__": #if this is the main file, parse the command args
	parser = argparse.ArgumentParser(description="Module that parses the log from trained networks and ranks their performance.")
	parser.add_argument('file', type=str, help="The filepath to the output log.")

	args, _ = parser.parse_known_args()

	f = open(args.file, 'r')
	txt = f.read()
	lines = txt.split('\n')

	results = []
	files = []

	for i, line in enumerate(lines):
		if line.find('Scores for') >= 0:
			line2 = lines[i+1]
			scores = line2.split('\t')
			for i, score in enumerate(scores):
				scores[i] = float(score.split(' ')[0])
			val = {'rmse': scores[0], 'sign': scores[1], 'custom': scores[2], 'r2': scores[3]}
			if line.find('train') >= 0:
				results.append({'train': val})
			elif line.find('valid') >= 0:
				results[len(results)-1]['valid']= val
			elif line.find('test') >= 0:
				results[len(results)-1]['test'] = val
		elif line.find("Saved") >= 0:
			files.append(line.replace("Saved accuracy graph at ", ""))
	print(results[0], results[1])

	for typ in ['train', 'test']:
		print("Results for %s" %typ)
		res = {}
		for i in ['rmse', 'custom', 'sign', 'r2']:
			seq = [x[typ][i] for x in results]
			while float('inf') in seq: seq.remove(float('inf'))
			res[i] = {'max': max(seq), 'min': min(seq)}
			print("File for max %s is %s." % (i, files[seq.index(max(seq))] ))
			print("File for min %s is %s." % (i, files[seq.index(min(seq))] ))
		print(res)