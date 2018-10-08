# blockchain-predictor

A set of tools and scripts that download and process blockchain and cryptocurrency course data, generate a dataset, use it to teach a deep learning neural network to make value predictions and evaluate the result.

The project implements the theoretical and experimental setup of a paper, which is currently undergoing peer review.

## Installation

### System dependencies
The tools require the installation of [Parity client](https://github.com/paritytech/parity), [Node.js](https://nodejs.org/en/download/), [Python 3](https://www.python.org/downloads/), [Pipenv](https://github.com/pypa/pipenv) and *optionally* [MongoDB](https://www.mongodb.com/download-center).

The project includes C++ optimized code. Installation of the [GCC Compiler](https://gcc.gnu.org), as well as the [Pybind11](https://github.com/pybind/pybind11) library is required in order to compile the C++ parts of the project.

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
pipenv install
```

### Building the C++ modules

Run the script `build.sh` under `c++` folder.

## Usage

### Pipenv

Proceed to use/run this project after running `pipenv shell`

### Python CLI

All python tools implement a CLI with a help page. It can be displayed by running `python something.py -h`.

### Initial data collection and storage

#### Blockchain node

Run a parity instance with **--tracing on** flag. A possible configuration could be:
```bash
parity -d /some/where --tracing on --mode active --cache-size 16384 --force-sealing --allow-ips public --min-peers 50 --max-peers 100 --jsonrpc-threads 10
```
The initial sync can take multiple hours. **Wait for full sync** before proceeding.

#### Database & data location

There are multiple options for a data store as a backend. Available options are defined in `database/`. By default, `hdfs_store_database.py` is used and hence no database instance needs to be started. The filepath to the h5 store file is defined that database file (for now).

If instead you want to use `arctic_store_database.py`, you have to first run an instance of MongoDB with:
```bash
mongod --dbpath /path/to/your/db
```

#### Initial database sync

The blockchain information needs to be downloaded from the running parity client to the database. This is done using:
```bash
python arcticdb.py --course
python arcticdb.py --blockchain
```

It may take a while depending on which database is used.

#### Property generation

Data properties are an extraction of the most important moments from the bulk raw data. They are generated for each course tick (time interval for which we have course data). 

To generate all of the available properties for all downloaded data, run the following command:
```bash
python property-generator.py --action generate
```

To generate one or more properties for all downloaded data, run the following command:
```bash
python property-generator.py --action generate --properties openPrice,closePrice
```

### Generation of a dataset

After the needed data properties are generated, you can proceed with generating the actual dataset. The dataset is generated using a certain dataset model. There are multiple dataset models that "compile" the properties and structure the dataset in a different way. The default is ```matrix```, which generates matrices from a moving window over all of the properties.

Dataset generation requires providing a list of comma separated properties to be included in the body and also a list (or a single item) of comma separated properties as a target / expected output.

Example:
```bash
python dataset_generator.py openPrice,closePrice stickPrice --filename some/where/dataset.pickle
```

Arguments `--start` and `--end` can be used as trimmers for the dataset:

```bash
python dataset_generator.py openPrice,closePrice stickPrice --start 2017-03-14-03 --end 2017-07-03-21
```


In most cases when training neural networks, we will need two or three datasets - a ```train```, ```validation``` (optional) and a ```test``` dataset. These datasets can be generated using separate calls to our ```dataset_generator``` for different dates, but we recommend to use one date interval that covers all our data and then split the resulting dataset into the needed parts. In our tool, this is done the following way:

```bash
python dataset_generator.py openPrice,closePrice stickPrice --ratio 6:2:2
```

Please keep in mind that the ```matrix``` model has dozens of hyperparameters that have been tuned for most cases. If your case differs, you need to change them in the source code of the matrix model.

### Training and evaluating the neural network

The generated dataset can be used to train neural networks. The supported networks depend on the chosen dataset model. The ```matrix``` model supports all networks. 

To train our convolutional network on an already generated dataset and also shuffle the train dataset, we can do the following:

```bash
python neural_trainer.py path/to/your/dataset.pickle --models CONV --shuffle
```

Training a neural network can't be that simple, right? Right! You ~~can~~ should override the default network hyperparameters to suit your dataset and problem needs. This can be done via:

```bash
python neural_trainer.py data/test.pickle --models CONV --args epoch=5,batch=1,lr=0.0001,kernel=3
```

This example sets the number of training epochs, the batch size, learning rate and kernel size for the whole convolutional network. Each network architecture has its own set of hyperparameters and they are defined with the network specification itself.

After training, the network's performance will be evaluated with the ```test``` dataset and measured by 4+ different accuracy/error scores. The performance on the train and test datasets will also be visualized on a graph by opening a new window. If you do not wish training to be blocked by a graph window, you can save the graph to a file instead, by passing the ```--quiet``` parameter. This is useful for automated training of multiple networks, as it allows you to review the results afterwards.

Our other neural models include ```CustomDeep```, ```LSTM``` and more to come.

### Basic data gathering
If needed, this project also provides a low-level tool that can download data from a crypto exchange / a blockchain node and save it as a .json in a given directory (by the `--filename some/where` argument).

To download and save course data for the whole history of the cryptocurrency, run:
```bash
node data-downloader.js --course
```

To download blocks 10 through 100, use:
```bash
node data-downloader.js --blockchain 10 100
```
