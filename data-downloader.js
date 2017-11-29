//Downloads certain blockchain data of the given time period and saves it as the given file (.json)
var Web3 = require("web3");
var https = require("https");
var fs = require('fs');
var Stopwatch = require("node-stopwatch").Stopwatch;
var util = require('util')

var sw = Stopwatch.create();

var web3;

var debug = true;

var datadir = 'data/'

var contractFile = datadir + 'contracts.json'

const maxAsyncRequests = 3;

var requestedBlocks = 0;

const saveSpace = true;

function initBlockchain(){
	if (typeof web3 !== 'undefined') {
		web3 = new Web3(web3.currentProvider);
	} else {
	// set the provider from Web3.providers
		console.log("Attempting connection to RPC...");
		web3 = new Web3(new Web3.providers.HttpProvider("http://localhost:8545"));
		if(typeof web3.isConnected !== "undefined" && web3.isConnected()) console.log("Successful connection!");
		else{
			console.log("Unsuccessful connection!\nMake sure that you have a local node running and that RPC / web3 is enabled on it");
			return false;
		}
	}

	console.log("Latest block number is " + web3.eth.blockNumber);

	return true;
}

function JSONRequest(request, callback){
	https.get(request, (res) => {
		console.log('Status code from exchange:', res.statusCode);

		var responseString = "";

		res.on('data', function (chunk) {
			responseString += chunk;
		});

		res.on('end', function(){

			console.log("Received "+responseString.length+" bytes");

			callback(JSON.parse(responseString));
		});

	}).on('error', (e) => {
		console.error(e);
		callback(undefined);
	});
}

function saveJSON(json, filename){
	fs.writeFile(filename, JSON.stringify(json), function(err) {
		if(err) {
			console.log(err);
			return;
		}

		console.log("The data was saved as "+filename);
	}); 
}

function downloadCourseCryptocompare(start, end, callback){
	var data = []

	const firstTimestamp = 1438959600 //this timestamp is the first data that this source has

	var sendRequest = function(stB){
		var request = 'https://min-api.cryptocompare.com/data/histohour?fsym=ETH&tsym=USD&limit=2000&e=CCCAGG&toTs='+stB;
		JSONRequest(request, function(part){
			var partData = part.Data.reverse().filter(tick => tick.time >= firstTimestamp) //remove any invalid data that is before the first timestamps
			data.push.apply(data, partData)

			console.log(util.format("Received data chunk that starts at %d and ends at %d.", part.TimeTo, part.TimeFrom))

			if(part.TimeFrom > start && part.TimeFrom > firstTimestamp)
				sendRequest(part.TimeFrom-1) //request the next batch
			else{
				for(var i=0; i<data.length-1; i++){ //validate that we have all data in the correct hourly intervals
					if (data[i].time - 3600 != data[i+1].time){
						console.log(util.format("Mismatch between dates %d and %d with difference %d.", data[i].time, data[i+1].time, data[i+1].time-data[i].time))
					}
				}

				data.reverse()

				callback(data)
			}
		})
	}

	sendRequest(end)
}

function downloadCoursePoloniex(start, end, callback){
	var request = "https://poloniex.com/public?command=returnChartData&currencyPair=USDT_ETH&start="+start+"&end="+end+"&period=300"

	JSONRequest(request, function(res){
		callback(res)
	});
}

function downloadCourse(start, end, source, callback){

	var request = "";

	var saveCallback = function(data){
		if (data != undefined){
			console.log(data.length, data[0], data[data.length-1])

			saveJSON(data, datadir + source + "_price_data.json")
		}

		callback(data)
	}

	if(source == "poloniex"){
		downloadCoursePoloniex(start, end, saveCallback)
	}else if(source == "cryptocompare"){
		downloadCourseCryptocompare(start, end, saveCallback)
	} else callback(undefined)
}

function downloadWholeCourse(){
	downloadCourse(1, 999999999999999, "cryptocompare", function(result){
		if(result == undefined){
			console.error("Error while downloading course!")
		}
	});
}

function downloadBlockchain(startBlock, expectedBlocks){

	//var startBlock = 4130000; //where to start requesting from
	var blockDict = {}; //temp storage for the received blocks
	var receivedBlocks = 0; //how many blocks have been successfully received
	//var expectedBlocks = 5000; //the amount of blocks that we want to receive

	requestedBlocks = 0; //the amount of blocks we have requested to receive

	var contractPublishing = [] //array of tx hashes, where a contract has been published

	console.log("Downloading blocks...");

	sw.start();

	var handler = function(err, block){
		if(err) console.error(err, block);
		else {
			//console.log("Got block "+block.number+" with "+block.transactions.length+" transactions in "+sw.elapsed.seconds+"s");
			if(block == null){
				console.error("Received empty block!");
			} else {
				var contracts = cleanBlock(block)
				contractPublishing.push.apply(contractPublishing, contracts);

				blockDict[block.number] = block;
			}

			receivedBlocks ++;

			if(receivedBlocks >= expectedBlocks){
				if(!validateBlocks(blockDict, startBlock, expectedBlocks, handler)) return;

				console.log("Received all blocks at "+(receivedBlocks / sw.elapsed.seconds)+"bl/s!");

				getContractLogs(startBlock, startBlock + expectedBlocks - 1, function(err, logs){
					var pushed = 0;

					for(var i=0; i<logs.length; i++){
						var block = blockDict[logs[i].blockNumber];
						for(var j=0; j<block.transactions.length; j++){
							if(block.transactions[j].hash == logs[i].hash){
								if(block.transactions[j].logs == undefined) block.transactions[j].logs = []
								
								block.transactions[j].logs.push(logs[i]);
								pushed ++;
							}
						}
					}

					if (pushed != logs.length){
						console.error("Error! Unable to assign all logs to their transactions. Assigned x out of y", pushed, logs.length);
					}

					var processed = processBlocks(blockDict, startBlock);
					
					saveAsJSON(processed)
				});
			} else if(requestedBlocks < expectedBlocks){
				//get the next block
				getNextBlock(startBlock, handler);
			}
		}
	}

	for(i = 0; i<maxAsyncRequests && i<expectedBlocks; i++){
		getNextBlock(startBlock, handler);
	}

	sw.stop();
}

//will get all logs from contracts within [start, end] block interval
function getContractLogs(start, end, callback){
	var filter = web3.eth.filter({'fromBlock': start, 'toBlock': end});
	
	var handlerCB = function(err, res){
		if(err){
			console.error(err);
			callback(err, null);
		}

		for(var i=0; i<res.length; i++){ //clean the logs
			cleanLog(res[i]);
		}

		console.log("Received logs with length ", res.length);

		callback(null, res);
	}

	filter.get(handlerCB)

	console.log("Getting logs for blocks from/to", start, end);
}

//This method first finds all published contracts from the publishing transactions
//It scans the downloaded blocks to look or transactions where these contracts participate and returns those TX's receipts.
//This is really slow and doesn't show contracts that are published by contracts. We no longer use this method, but get contract logs directly.
function getContractTransactions(publishing, blocks, callback){
	contracts = getContracts();
	receipts = {}
	receivedPublish = 0;

	var handler2 = function(txs){
		for(var i=0; i<txs.length; i++){
			receipt = cleanReceipt(txs[i])
			if(receipts[receipt.blockNumber] == undefined){
				receipts[receipt.blockNumber] = []
			}

			receipts[receipt.blockNumber].push(receipt);
		}
		
		saveContracts(contracts);

		callback(undefined, receipts);
	}

	var handler = function(res){
		for(var i=0; i<res.length; i++){
			receipt = cleanReceipt(res[i])

			if(receipts[receipt.blockNumber] == undefined){
				receipts[receipt.blockNumber] = []
			}

			receipts[receipt.blockNumber].push(receipt);

			contracts[receipt.contractAddress] = true;
		}

		numbers = Object.keys(blocks).sort();

		txToRequest = []

		for(i=0; i<numbers.length; i++){
			block = blocks[numbers[i]];

			for(j=0; j<block.transactions.length; j++){
				if(contracts[block.transactions[j].to] || contracts[block.transactions[j].from]){ //if the tx is from/to a contract
					txToRequest.push(block.transactions[j].hash);
				}
			}
		}

		console.log("Requesting receipts:", txToRequest.length);

		if(txToRequest.length > 0)
			getAll(web3.eth.getTransactionReceipt, txToRequest, handler2);
		else
			callback(undefined, receipts);
	}

	if(publishing.length > 0)
		getAll(web3.eth.getTransactionReceipt, publishing, handler);
	else
		callback(undefined, receipts);
}

function getAll(web3Function, inputs, callback){
	results = []
	received = 0;
	expected = inputs.length
	requested = 0

	var getNext = function(hdlr){
		web3Function(inputs[requested], hdlr);

		requested++;
	}

	var handler = function(err, res){
		if(err){
			console.error(err);
			getNext(handler); //there was problem, try again
		}
		else {
			if(res == null){
				console.error("Received empty result!");
			} else {
				results.push(res)
			}

			received++;

			if(received >= expected){
				callback(results);

			} else if(requested < expected){
				//get the next item
				getNext(handler);
			}
		}
	}

	for(i = 0; i<maxAsyncRequests*2 && i<expected; i++){
		getNext(handler);
	}
}

function cleanLog(log){
	log.hash = log.transactionHash; //rename to just hash, so it falls in line with 'hash' in a transaction
	delete log.transactionHash;

	delete log.transactionIndex;
	delete log.blockHash;
	delete log.logIndex;

	if(saveSpace){
		log.dataLen = log.data.length; //keep at least some info about the data.
		delete log.data; //these are the non-indexed log arguments. They can be arbitrary in length, and so take up a lot of space.
	}
}

function cleanReceipt(receipt){
	delete receipt.blockHash;
	delete receipt.logsBloom;
	delete receipt.root;
	
	for(i=0; i<receipt.logs.length; i++){
		log = receipt.logs[i];

		cleanLog(log);
	}

	return receipt;
}

function cleanTransaction(tx){
	delete tx.blockHash;
	delete tx.nonce;
	delete tx.v;
	delete tx.r;
	delete tx.s;
	delete tx.input;
	delete tx.transactionIndex;
}

function cleanBlock(block){ //this function removes many useless for our cases fields in the block and txs
	//it returns the tx hashes, where contracts were deployed
	contractHashes = [];

	delete block.extraData;
	delete block.hash;
	delete block.logsBloom;
	delete block.mixHash;
	delete block.nonce;
	delete block.parentHash;
	delete block.receiptsRoot;
	delete block.sha3Uncles;
	delete block.stateRoot;
	delete block.transactionsRoot;
	delete block.uncles;
	block.date = block.timestamp;
	delete block.timestamp;

	for(i=0; i<block.transactions.length; i++){
		tx = block.transactions[i];

		cleanTransaction(tx);

		if(tx.to == null){ //if this is a contract creation
			contractHashes.push(tx.hash);
		}
	}

	return contractHashes;
}

function getBlock(blockN, handler){
	web3.eth.getBlock(blockN, true, handler);
}

function getNextBlock(startBlock, handler){
	getBlock(startBlock+requestedBlocks, handler);
	requestedBlocks++;
}

function validateBlocks(dict, first, len, handler){ //checks to see if all blocks are reseived accordingly and requests the missing ones
	for(bl = 0; bl < len; bl++){
		if(dict[bl+first] == null){
			getBlock(bl+first, handler);
			console.log("Requesting missing block #"+(bl+first));
			return false;
		}
	}

	return true;
}

function processBlocks(dict, first){
	var blockchain = [];

	var block;
	for(i = first;; i++){
		block = dict[i];

		if(block != undefined) blockchain.push(block);
		else break;
	}

	console.log("Successfully loaded "+blockchain.length+" blocks");
	console.log("First block is "+blockchain[0].number+" with " + blockchain[0].transactions.length+" transactions!");
	console.log("Last block is "+blockchain[blockchain.length-1].number+" with " + blockchain[blockchain.length-1].transactions.length+" transactions!");

	return blockchain;
}

function saveAsJSON(data){
	sw.start();

	var file = JSON.stringify(data);
	var filename = datadir+"blocks "+data[0].number+"-"+data[data.length-1].number+".json"
	console.log("Data to save is "+file.length+" bytes long.");
	fs.writeFile(filename, JSON.stringify(data), function(err) {
		if(err) {
			console.log(err);
			sw.stop();
			return;
		}

		console.log("The data was saved in "+sw.elapsed.seconds+"s as "+filename);
	});
	sw.stop();
}

function getContracts(){
	contracts = {};

	try{
		contracts = JSON.parse(fs.readFileSync(contractFile));
	} catch(e){}

	return contracts;
}

function saveContracts(contracts){
	fs.writeFileSync(contractFile, JSON.stringify(contracts));
}

function compareBlocks(a, b){
	if (a.timestamp < b.timestamp)
		return -1;
	if (a.timestamp > b.timestamp)
		return 1;
	return 0;
}

function compareReceipts(a, b){
	if (a.blockNumber < b.blockNumber)
		return -1;
	if (a.blockNumber > b.blockNumber)
		return 1;
	return 0;
}

//this function is to make quick functionality test - not to be confused with unit testing.
function testAsyncRequests(){
	initBlockchain()

	received = 0
	expected = 10000

	var handler2 = function(err, res){
		received++

		if (err){
			console.error("res is null! Error:");
			console.error(err);
			console.log("Progress", received, expected);
		}

		delete res.blockHash;

		var curr = (new Date).getTime();

		if(received == expected){
			console.log("Time it took was", (curr-start))
		}
	}

	console.log(getContracts())

	var start = (new Date).getTime();
	for(var i=0; i<expected; i++){
		web3.eth.getTransactionReceipt("0x674d990c9a298fd995f02ef4b923211f3e4208828014417ba45f8d467657ee38", handler2);
	}
}

//this function is to make quick functionality test - not to be confused with unit testing.
function testFilters(){
	initBlockchain();

	contracts = getContracts();

	var filter = web3.eth.filter({'fromBlock': 3500000, 'toBlock': 3510000});

	var handlerCB = function(err, res){
		if(err) console.error(err);

		console.log("Received results with length ", res.length);

		for(var i=0; i<res.length; i++){
			if(!contracts[res[i].address]){
				console.error("Addess", res[i].address, "is not in our contracts db!!!");
			}
		}

		console.log(res[0])
		console.log(res[res.length-1])
	}

	filter.get(handlerCB)
}

function printHelp(){
	console.log("A tool to download cryptocurrency course and blockchain data and save them as a json");
	console.log("Arguments:");
	console.log("course - downloads the whole history of the token course from an exchange");
	console.log("blockchain - downloads some blockchain data (transactions, balances, ect..) from a local node");
}

function processArgs(){
	if(process.argv.length == 2) printHelp();
	else{
		for(argIndex = 2; argIndex<process.argv.length; argIndex++){
			arg = process.argv[argIndex];

			if(arg.search('help') >=0) printHelp();
			else if(arg == 'course') downloadWholeCourse();
			else if(arg == 'blockchain'){
				var start, count;

				start = parseInt(process.argv[argIndex+1]);
				count = parseInt(process.argv[argIndex+2]);
				argIndex += 2;
				if(isNaN(start) || isNaN(count)){
					console.log("Enter the start block and block count to download.");
					break;
				}

				if(!initBlockchain()) return;
				downloadBlockchain(start, count);
			}
			else if(arg == 'test'){
				testFilters()
			}
		}
	}
}

processArgs();
