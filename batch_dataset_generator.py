import argparse
import os.path

import dataset_generator as gen

def run(group, folder):
	if group == 'distributions':
		directory = folder + group + '/'

		widths = [24, 24, 18, 23, 92, 92, 68, 88,48]
		slices = {3: [':', ':'], 7: [':', ':']} #accBalDistr doesn't need a cutoff
		distributions1 = ['balanceLastSeenDistribution_cpp_log2', 'contractBalanceLastSeenDistribution_log2_v2', 'contractVolumeInERC20Distribution_log2_v2_stateless', 'accountBalanceDistribution']

		distributions2 =['balanceLastSeenDistribution_log1_2', 'contractBalanceLastSeenDistribution_log1_2_v2', 'contractVolumeInERC20Distribution_log1_2_v2_stateless', 'accountBalanceDistribution_log1_2']
		distributions = []
		distributions.extend(distributions1)
		#distributions.extend(distributions2)
		distributions.append(str.join(',', distributions1)) #append all other distributions, concatenated into a string
		distributions.append(str.join(',', distributions2))

		for i, distribution in enumerate(distributions):
			for suffix in ['']:#, '_rel']: we found that relative values don't help
				distribution += suffix

				for target in ['highPrice_rel', 'highPrice', 'uniqueAccounts', 'uniqueAccounts_rel']:
					for model in ['stacked', 'matrix']:
						for normStd in ['global']:#, 'local']:
							for window in [1, 5, 24, 104]:
								filename = directory + model + '-' + distribution + '-' + target + '-' + normStd + '-' + str(window)+'w' + '.pickle'
								if not os.path.exists(filename): #no need to waste writes if already written
									print("Generating dataset %s." % filename)
									gen.run(model, target+','+distribution, '2017-03-01', None, filename, 'full', '1:6:1', False,\
									{'window': window, 'target': [target], 'normalization': {}, 'defaultNormalization': 'auto', 'blacklistTarget': True, 'width': widths[i],\
									'normalizationLevel': 'pixel', 'normalizationStd': normStd},\
									{distribution: {'scale': 'log2', 'slices': slices.get(i, [':', '1:'])}}) #last line will break if there is more than one distribution

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Automatically generates a group of datasets with predefined parameters.")
	parser.add_argument('group', type=str, choices=['distributions'], help='The name of the dataset group to be generated.')
	parser.add_argument('--filepath', type=str, default='data/', help="The save location for the datasets. \
	A subfolder will be created there with the name of the dataset group.")
	args, _ = parser.parse_known_args()

	run(args.group, args.filepath)
