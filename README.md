# blockchain-predictor

A set of tools and scripts that download and process blockchain and cryptocurrency course data, generate a dataset, use it to teach a deep learning neural network to make value predictions and evaluate the result.

The project is a work-in-progress and is yet to give (hopefully) accurate predictions.

## Installation

### System dependencies
The tools require the installation of [Ethereum geth](https://github.com/ethereum/go-ethereum/wiki/geth), [Node.js](https://nodejs.org/en/download/), [Python 3](https://www.python.org/downloads/) and [MongoDB](https://www.mongodb.com/download-center). Please install the appropriate packages for your system.

### Node dependencies

Clone the git repository and install the node dependencies:
```bash
git clone https://github.com/Zvezdin/blockchain-predictor.git
cd blockchain-predictor
npm install
```

### Python dependencies

Install the required python dependencies via the following script:
```bash
chmod u+x pip-install.sh
./pip-install.sh
```

You're all set!

## Usage

Run geth initially and wait for it to sync with the following command:

```bash
geth --rpc --fast --cache 2048 --datadir /path/to/your/data
```
The initial sync can take multiple hours

Consecutive runs can be done via:
```bash
geth --rpc --datadir /path/to/your/data
```

Run an instance of MongoDB with:
```bash
mongod --dbpath /path/to/your/db
```

### Basic data gathering

To download and save course data for the whole history of the cryptocurrency, run:
```bash
node data-downloader.js course
```

To download and save the first 100 blocks after the 10th block from the blockchain, use:
```bash
node data-downloader.js blockchain 10 100
```

For more info, run:
```bash
node data-downloader.js help
```

All data is saved in folder ```data```, relative to the script, as ```.json``` files.

### Database usage and managemenet

Saving files as simple ```.json``` files isn't very useful, scalable and optimal. This project implements a high-level database service that manages data gathering, processing, storage and retrieval.

To download and save historical course data in the database, run:
```bash
python3 arcticdb.py --course
```

To download, process and save blockchain data in the database, run:
```bash
python3 arcticdb.py --blockchain
```

For more info:
```bash
python3 arcticdb.py -h
```

### Generation of data properties

Data properties are calculated from the raw data. They are features which can represent certain activity in a better way for the deep network. They are generated for each course tick (time interval for which we have course data). 

To generate all of the available properties for all downloaded data, run the following command:
```bash
python3 property-generator.py --action generate
```

To generate one or more properties for all downloaded data, run the following command:
```bash
python3 property-generator.py --action generate --properties openPrice,closePrice
```

To remove all generated properties:
```bash
python3 property-generator.py --action remove
```

For more info:
```bash
python3 property-generator.py -h
```

### Generation of a dataset

After the needed data properties are generated, you can proceed with generating the actual dataset. The dataset is generated using a certain dataset model. There are multiple dataset models that "compile" the properties and structure the dataset in a different way. The default is ```matrix```, which generates matrices from a moving window over all of the properties.

The correct labels for each entry in the dataset are also generated. The default label type is ```boolean```, which represents the sign of the next course change. Label type of ```full``` represents the actual value change.

The result of dataset generation is a binary file, which is saved by default inside a ```data``` folder, relative to the tool's storage.

To generate a dataset from all available data with default settings and save in a different location, run:
```bash
python3 dataset_generator.py --filename /my/path/dataset.pickle
```

To generate a dataset for a certain period of time, use:
```bash
python3 dataset_generator --start 2017-03-14-03 --end 2017-07-03-21
```

To generate a dataset using a certain model and a set of properties, use:
```bash
python3 dataset_generator --model matrix --properties accountBalanceDistribution,transactionCount,gasUsed
```

In most cases when training neural networks, we will need two or three datasets - a ```train```, ```validation``` (optional) and a ```test``` dataset. These datasets can be generated using separate calls to our ```dataset_generator``` for different dates, but we recommend to use one date interval that covers all our data and then split the resulting dataset into the needed parts. In our tool, this is done the following way:

```bash
python3 dataset_generator --ratio 6:2:2
```

This splits the dataset to chunks with ratio 6:2:2, or 60%, 20% and 20%. One can generate only two datasets, for example with:

```bash
python3 dataset_generator --ratio 5:3
```

Please keep in mind that the ```matrix``` model has dozens of hyperparameters that have been tuned for most cases. If your case differs, you need to change them in the source code of the matrix model.

For all available options, please see:
```bash
python3 dataset_generator -h
```

### Training and evaluating the neural network

The generated dataset can be used to train neural networks. The supported networks depend on the chosen dataset model. The ```matrix``` model supports all networks. 

To train our convolutional network on an already generated dataset and also shuffle the train dataset, we can do the following:

```bash
python3 neural_trainer.py path/to/your/dataset.pickle --models CONV --shuffle
```

Traninng a neural network can't be that simple, right? Right! You ~~should~~ can override the default network hyperparameters to suit your dataset and problem needs. This can be done via:

```bash
python neural_trainer.py data/test.pickle --models CONV --args epoch=5,batch=1,lr=0.0001,kernel=3
```

This example sets the number of training epochs, the batch size, learning rate and kernel size for the whole convolutional network. Each network architecture has its own set of hyperparameters and they are defined with the network specification itself.

After training, the network's performance will be evaluated with the ```test``` dataset and measured by 4+ different accuracy/error scores. The performance on the train and test datasets will also be visualized on a graph by opening a new window. If you do not wish training to be blocked by a graph window, you can save the graph to a file instead, by passing the ```--quiet``` parameter. This is useful for automated training of multiple networks, as it allows you to review the results afterwards.

Our other neural models include ```CustomDeep```, ```LSTM``` and more to come.