import argparse
import os.path

import dataset_generator as gen

def run(group, folder):
	directory = os.path.join(folder, group)

	if group == 'distributions':

		widths = [24, 24, 18, 23, 92, 92, 68, 88,48]
		slices = {3: [':', ':'], 7: [':', ':']} #accBalDistr doesn't need a cutoff
		distributions1 = ['balanceLastSeenDistribution_cpp_log2', 'contractBalanceLastSeenDistribution_log2_v2', 'contractVolumeInERC20Distribution_log2_v2_stateless', 'accountBalanceDistribution']

		distributions2 =['balanceLastSeenDistribution_log1_2', 'contractBalanceLastSeenDistribution_log1_2_v2', 'contractVolumeInERC20Distribution_log1_2_v2_stateless', 'accountBalanceDistribution_log1_2']
		basicProperties = ['highPrice,volumeFrom,volumeTo', 'highPrice_rel,volumeFrom_rel,volumeTo_rel']
		distributions = []
		distributions.extend(basicProperties)
		distributions.extend(distributions1)
		#distributions.extend(distributions2)
		distributions.append(str.join(',', distributions1)) #append all other distributions, concatenated into a string
		#distributions.append(str.join(',', distributions2)) these distributions are too memory-heavy

		for i, distribution in enumerate(distributions):
			for suffix in ['']:#, '_rel']: we found that relative values don't help
				distribution += suffix

				for target in ['highPrice_rel', 'highPrice_10max_rel', 'highPrice', 'highPrice_10max', 'uniqueAccounts', 'uniqueAccounts_rel']:
					for model in ['stacked']:#, 'matrix']:
						if 'volumeTo' in distribution: #it is a basic property
							model = 'matrix'
						for normalizationLevel in ['property', 'pixel', 'local']:
							for window in [8, 24, 104]:
								if 'distribution' in distribution.lower() and model == 'matrix' and window > 24:
									continue #bad combination

								filename = model + '-' + distribution + '-' + target + '-' + normalizationLevel + '-' + str(window)+'w' + '.pickle'
								filename = os.path.join(directory, filename)
								if not os.path.exists(filename): #no need to waste writes if already written
									print("Generating dataset %s." % filename)
									gen.run(model, target+','+distribution, '2017-03-01', None, filename, 'full', '1:6:1', False,\
									{'window': window, 'target': [target], 'normalization': {}, 'defaultNormalization': 'auto', 'blacklistTarget': True, 'width': widths[i],\
									'normalizationLevel': normalizationLevel, 'normalizationStd': 'global'},\
									{distribution: {'scale': 'log2', 'slices': slices.get(i, [':', '1:'])}}) #last line will break if there is more than one distribution
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
