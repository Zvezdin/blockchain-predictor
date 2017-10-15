# blockchain-predictor

A set of tools and scripts that download and process blockchain and cryptocurrency course data, generate a dataset, use it to teach a deep learning neural network to make value predictions and evaluate the result.

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

For more info:
```bash
python3 property-generator.py -h
```

### Generation of a dataset

After the needed data properties are generated, you can proceed with generating the actual dataset. The dataset is generated using a certain dataset model. There are multiple dataset models that "compile" the properties and structure the dataset in a different way. The default is ```matrix```, which generates matrices from a moving window over all of the properties.

The correct labels for each entry in the dataset are also generated. The default label type is ```boolean```, which represents the sign of the next course change.

To generate a dataset from all available data with default settings, run:
```bash
python3 dataset_generator.py
```

To generate a dataset for a certain period of time, use:
```bash
python3 dataset_generator --start 2017-03-14-03 --end 2017-07-03-21
```

For all available options, please see:
```bash
python3 dataset_generator --help
```

### Training and evaluating the naural network

The deep network model is work-in-progress
