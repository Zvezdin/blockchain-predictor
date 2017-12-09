import argparse
import os.path

import dataset_generator as gen

#python dataset_generator.py --model stacked highPrice_rel,balanceLastSeenDistribution_log2 --start 2017-03-01 --filename --ratio 1:6:1 --labels full --no-shuffle

def run(group, folder):
	if group == 'distributions':
		directory = folder + group + '/'

		widths = [24, 24, 18]

		for i, distribution in enumerate(['balanceLastSeenDistribution_cpp_log2', 'contractBalanceLastSeenDistribution_log2_v2', 'contractVolumeInERC20Distribution_log2_v2_stateless']):
			for suffix in ['', '_rel']:
				distribution += suffix

				for target in ['highPrice_rel', 'highPrice']:
					for model in ['stacked', 'matrix']:
						for window in [1, 5, 24, 104]:
							filename = directory + model + '-' + distribution + '-' + target + '-' + str(window)+'w' + '.pickle'
							if not os.path.exists(filename): #no need to waste writes if already written
								gen.run(model, target+','+distribution, '2017-03-01', None, filename, 'full', '1:6:1', False,\
								{'window': window, 'target': [target], 'normalization': {}, 'defaultNormalization': 'auto', 'blacklistTarget': True, 'width': widths[i]},\
								{distribution: {'scale': 'log2', 'slices': [':', '1:']}})

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Automatically generates a group of datasets with predefined parameters.")
	parser.add_argument('group', type=str, choices=['distributions'], help='The name of the dataset group to be generated.')
	parser.add_argument('--filepath', type=str, default='data/', help="The save location for the datasets. \
	A subfolder will be created there with the name of the dataset group.")
	args, _ = parser.parse_known_args()

	run(args.group, args.filepath)