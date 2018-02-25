import argparse
import os.path
from datetime import datetime as dt

import dataset_generator as gen
import database_tools as db

def getShapeOfKey(key):
	ch = db.getChunkstore()
	data = db.getLatestRow(ch, key)

	data[key] = data[key].apply(db.decodeObject) #decode it because we encode numpy arrays

	val = data[key].values[-1] #get the latest item

	return val.shape

def propToStr(props):
	if type(props) != str:
		return str.join(',', props)
	return props

def run(group, folder):
	print(
	getShapeOfKey('balanceLastSeenDistribution_cpp_log2')
	)

	directory = os.path.join(folder, group)

	if group == 'distributions':

		widths = {}
		slices = {}
		slices['accountBalanceDistribution'] = [':', ':'] #these distributions don't need cutoff
		slices['accountBalanceDistribution_log1_2'] = [':', ':']

		distributions1 = ['balanceLastSeenDistribution_cpp_log2', 'contractBalanceLastSeenDistribution_log2_v2', 'contractVolumeInERC20Distribution_log2_v2_stateless', 'accountBalanceDistribution']

		distributions2 =['balanceLastSeenDistribution_log1_2', 'contractBalanceLastSeenDistribution_log1_2_v2', 'contractVolumeInERC20Distribution_log1_2_v2_stateless', 'accountBalanceDistribution_log1_2']
		basicProperties = ['highPrice,volumeFrom,volumeTo'.split(','), 'highPrice_rel,volumeFrom_rel,volumeTo_rel'.split(','), 'volumeFrom,volumeTo'.split(','), 'volumeFrom_rel,volumeTo_rel'.split(',')]
		distributions = []
		distributions.extend(distributions1)
		#distributions.extend(distributions2)

		#custom width for that element
		widths[propToStr(distributions1)] = 48
		distributions.append(distributions1) #append all other distributions, concatenated into a string
		#distributions.append(distributions2) these distributions are too memory-heavy
		distributions.extend(basicProperties)
		distributions.extend([[x, 'highPrice', 'volumeFrom', 'volumeTo'] for x in distributions1])

		for i, distribution in enumerate(distributions):
			distributionStr = propToStr(distribution)
			for target in ['highPrice_ema', 'highPrice_ema_rel', 'highPrice_sma', 'highPrice_sma_rel', 'highPrice_rel', 'highPrice_10max_rel', 'highPrice', 'highPrice_10max', 'uniqueAccounts', 'uniqueAccounts_rel']:
				for model in ['stacked']:#, 'matrix']:
					if 'volumeTo' in distributionStr or distributionStr == 'accountBalanceDistribution' or distributionStr == 'accountBalanceDistribution_log1_2': #it is a basic property
						model = 'matrix'
					for normalizationLevel in ['property', 'pixel']:#, 'local']:
						for window in [8, 24, 104]:
							if 'distribution' in distributionStr.lower() and model == 'matrix' and window > 24:
								continue #bad combination

							filename = model + '-' + distributionStr + '-' + target + '-' + normalizationLevel + '-' + str(window)+'w' + '.pickle'
							filename = os.path.join(directory, filename)
							if not os.path.exists(filename): #no need to waste writes if already written
								print("Generating dataset %s." % filename)

								width = widths.get(distributionStr, None)

								preprocess={}

								if 'distribution' in distributionStr: #do not preprocess simple vlaues
									if type(distribution) == list:
										for distr in distribution:
											slice_ = slices.get(distr, [':', '1:'])
											preprocessElement = {'scale': 'log2', 'slices': slice_}
											preprocess[distr] = preprocessElement
									else:
										slice_ = slices.get(distribution, [':', '1:'])
										preprocessElement = {'scale': 'log2', 'slices': slice_}
										preprocess[distribution] = preprocessElement
								
								gen.run(model, distribution, target.split(','), filename, start=dt(2017,3,1), end=None, ratio=[1,6,1], shuffle=False,\
								args={'window': window, 'normalization': {}, 'defaultNormalization': 'auto', 'blacklistTarget': True, 'width': width,\
								'normalizationLevel': normalizationLevel, 'normalizationStd': 'global'},\
								preprocess=preprocess) #last line will break if there is more than one distribution
	elif group == 'experiments':
		args = []
		args.append({'prop': '', 'target': 'highPrice_rel', 'blacklistTarget': False, 'preprocessor': {}})
		args.append({'prop': 'volumeTo_rel,volumeFrom_rel,transactionCount_rel,gasUsed_rel', 'target': 'highPrice_rel', 'blacklistTarget': False, 'preprocessor': {}})
		args.append({'prop': 'volumeTo,volumeFrom,transactionCount,gasUsed', 'target': 'highPrice', 'blacklistTarget': False, 'preprocessor': {}})
		args.append({'prop': 'accountBalanceDistribution_rel', 'target': 'highPrice_rel', 'blacklistTarget': True, 'preprocessor': {'accountBalanceDistribution': {'scale': 'log2'}}})
		args.append({'prop': 'accountBalanceDistribution', 'target': 'highPrice_rel', 'blacklistTarget': True, 'preprocessor': {'accountBalanceDistribution': {'scale': 'log2'}}})
		args.append({'prop': 'accountBalanceDistribution', 'target': 'highPrice', 'blacklistTarget': True, 'preprocessor': {'accountBalanceDistribution': {'scale': 'log2'}}})
		args.append({'prop': 'accountBalanceDistribution', 'target': 'uniqueAccounts_rel', 'blacklistTarget': True, 'preprocessor': {'accountBalanceDistribution': {'scale': 'log2'}}})

		for i, arg in enumerate(args):
			filename = directory + str(i+1) + '_propnorm' + '.pickle'
			if not os.path.exists(filename): #no need to waste writes if already written
				print("Generating dataset %s." % filename)
				gen.run('matrix', arg['target']+','+arg['prop'], '2017-03-01', None, filename, 'full', '1:6:1', False,\
				{'window': 104, 'target': [arg['target']], 'normalization': {}, 'defaultNormalization': 'auto', 'blacklistTarget': arg['blacklistTarget'],\
				'normalizationLevel': 'property', 'normalizationStd': 'global'}, arg['preprocessor'])

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Automatically generates a group of datasets with predefined parameters.")
	parser.add_argument('group', type=str, choices=['distributions', 'experiments'], help='The name of the dataset group to be generated.')
	parser.add_argument('--filepath', type=str, default='data/', help="The save location for the datasets. \
	A subfolder will be created there with the name of the dataset group.")
	args, _ = parser.parse_known_args()

	run(args.group, args.filepath)
