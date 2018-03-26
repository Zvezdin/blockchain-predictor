//Downloads certain blockchain data of the given time period and saves it as the given file (.json)
const Web3 = require("web3");
const https = require("https");
const fs = require('fs');
const Stopwatch = require("node-stopwatch").Stopwatch;
const util = require('util')
const assert = require('assert').strict;

const sw = Stopwatch.create();

var web3;

var debug = true;

var datadir = 'data/'

var contractFile = datadir + 'contracts.json'

const maxAsyncRequests = 8;

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
			console.error("Unsuccessful connection!\nMake sure that you have a local node running and that RPC / web3 is enabled on it");
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

function downloadBlockchain(startBlock, endBlock){
	var blockDict = {}; //temp storage for the received blocks

	var requestedBlocks = 0; //the amount of blocks we have requested to receive
	var receivedBlocks = 0; //how many blocks have been successfully received
	var expectedBlocks = endBlock - startBlock + 1;
	var lastRequestedBlock = 0;

	console.log("Downloading blocks from "+startBlock+" to "+endBlock);

	sw.start();

	return new Promise(function(resolve, reject){
		var handler = function(err, block){
			if(err) console.error(err, block);
			else {
				//console.log("Got block "+block.number+" with "+block.transactions.length+" transactions in "+sw.elapsed.seconds+"s");
				if(block == null){
					console.error("Received empty block!");
				} else {
					cleanBlock(block)

					blockDict[block.number] = block;
				}

				receivedBlocks++;

				if(receivedBlocks >= expectedBlocks){
					let missing = listMissingBlocks(blockDict, startBlock, endBlock);

					if(missing.length > 0){
						console.error("Detected missing blocks: "+missing+" Re-requesting them!");
						requestBlocks(missing, handler);
						return;
					}

					console.log("Received all blocks at "+(receivedBlocks / sw.elapsed.seconds)+"bl/s!");
					resolve(blockDict);
				} else if(requestedBlocks < expectedBlocks){
					//get the next block
					lastRequestedBlock++;
					requestedBlocks++;
					requestBlock(lastRequestedBlock, handler);
				}
			}
		}

		let end = Math.min(startBlock + maxAsyncRequests - 1, endBlock);
		
		lastRequestedBlock = end;
		requestedBlocks = Math.abs(end - startBlock) + 1;
		requestBlockRange(startBlock, end, handler);

		sw.stop();
	});
}

//will get all logs from contracts within [start, end] block interval
function getContractLogs(start, end){
	return new Promise(function(resolve, reject) {
		var filter = web3.eth.filter({'fromBlock': start, 'toBlock': end});
		
		var handlerCB = function(err, res){
			if(err){
				console.error(err);
				reject(err);
				return;
			}

			for(var i=0; i<res.length; i++){ //clean the logs
				cleanLog(res[i]);
			}

			console.log("Received logs with length ", res.length);

			resolve(res);
		}

		filter.get(handlerCB)

		console.log("Getting logs for blocks from/to", start, end);
	});
}

//returns a promise for all transaction traces for the block range [start, end]
//requires the parity node to run! Only parity supports JSON RPC transaction tracing api!
function getTransactionTraces(start, end, noErrors=true){
	console.log("Getting all tx traces from "+start+" to "+end);
	return new Promise(function(resolve, reject) {
		web3.currentProvider.sendAsync({
			method: "trace_filter",
			params: [{fromBlock: "0x" + (+start).toString(16), toBlock: "0x" + (+end).toString(16)}],
			jsonrpc: "2.0",
			id: "1583"
		}, function (err, result) {
			if(err){
				reject(err);
				return;
			}

			rawResult = result.result;
			result = [];

			for(var i=0; i<rawResult.length; i++) {
				var el = rawResult[i];

				if(noErrors && el.error) {
					continue;
				}

				result.push(el);
		
				if(el.type !== 'reward' && el.type !== 'call' && el.type !== 'create' && el.type !== 'suicide'){
					console.log("Found something different!")
					console.dir(el, {depth:null})
				}

				cleanAndNormalizeTrace(el);
			}
			
			console.log("Received traces with length "+result.length);
			resolve(result);
		});
	});
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

	//unpack the topics array into four properties
	log.topic0 = null;
	log.topic1 = null;
	log.topic2 = null;
	log.topic3 = null;

	for(let i=0; i<log.topics.length; i++){
		log['topic' + i] = log.topics[i];
	}
	delete log.topics;

	//parity-related properties
	delete log.transactionLogIndex;

	if(saveSpace){
		log.dataLen = log.data.length; //keep at least some info about the data.
		delete log.data; //these are the non-indexed log arguments. They can be arbitrary in length, and so take up a lot of space.
	}

	return log;
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
	if(saveSpace){
		tx.dataLen = tx.input.length;
		delete tx.input;
	}
	delete tx.transactionIndex;

	//parity-related properties
	delete tx.standard_v;
	delete tx.standardV;
	delete tx.raw;
	delete tx.publicKey;
	delete tx.chainId;
	delete tx.condition;
	delete tx.creates;

	return tx;
}

function cleanAndNormalizeTrace(trace){
	let type = trace.type;
	
	//normalize to the same object property set
	if(type == 'suicide'){
		assertHasProperties(trace.action, ['address', 'balance', 'refundAddress']);
		assert(trace.result == null);

		renameProp(trace.action, 'address', 'from');
		renameProp(trace.action, 'balance', 'value');
		renameProp(trace.action, 'refundAddress', 'to');
		trace.action.gas = null;

	} else if(type == 'reward'){
		assertHasProperties(trace.action, ['author', 'rewardType', 'value']);
		assert(trace.result == null);

		renameProp(trace.action, 'author', 'to');
		trace.action.from = null;
		trace.action.gas = null;

		trace.subtype = trace.action.rewardType;
		delete trace.action.rewardType;

	} else if(type == 'create'){
		assertHasProperties(trace.action, ['from', 'gas', 'init', 'value']);
		assertHasProperties(trace.result, ['gasUsed', 'address', 'code']);

		delete trace.action.init;
		trace.action.to = trace.result.address;
		delete trace.result.address;
		delete trace.result.code;

	} else if(type == 'call'){
		assertHasProperties(trace.action, ['callType', 'from', 'gas', 'input', 'to', 'value']);
		try{
			assertHasProperties(trace.result, ['gasUsed', 'output']);
		} catch(e){
			console.log(trace);
			throw new DOMException();
		}
		trace.subtype = trace.action.callType;
		delete trace.action.callType;
		delete trace.action.input;
		delete trace.result.output;
	} else {
		console.error("Received unknown trace type: ", type);
		assert(false);
	}

	//merge the action properties into the trace object
	let actionProps = ['from', 'gas', 'to', 'value'];
	assertHasProperties(trace.action, actionProps);
	for(let i=0; i<actionProps.length; i++){
		let prop = actionProps[i];

		trace[prop] = trace.action[prop];
	}
	delete trace.action;
	
	//merge the result properties into the trace object
	let resultProps = ['gasUsed'];
	if(!trace.result){ //create an empty object with null-valued properties
		trace.result = {};
		for(let i=0; i<resultProps.length; i++){
			let prop = resultProps[i];
			trace.result[prop] = null;
		}
	}
	assertHasProperties(trace.result, resultProps);
	for(let i=0; i<resultProps.length; i++){
		let prop = resultProps[i];

		trace[prop] = trace.result[prop];
	}
	delete trace.result;

	if(!trace.subtype){
		trace.subtype = null;
	}

	delete trace.blockHash;
	//we'll need that
	//delete trace.blockNumber;
	delete trace.subtraces;
	//do we really need the position of this trace in the whole tx?
	//for that, we'll need something more than arctic DB
	delete trace.traceAddress;
	//we may need this
	//delete trace.transactionHash;
	delete trace.transactionPosition;

	//this should be the final property set of the trace
	assertHasProperties(trace, ['transactionHash', 'type', 'subtype', 'from', 'gas', 'to', 'value', 'gasUsed']);

	return trace;
}

function assertHasProperties(obj, propertyList) {
	if(typeof propertyList !== 'object'){
		propertyList = [propertyList];
	}

	for(let i=0; i<propertyList.length; i++){
		assert(obj.hasOwnProperty(propertyList[i]));
	}
}

function renameProp(obj, prop, newProp) {
	assert(obj.hasOwnProperty(prop));

	obj[newProp] = obj[prop];
	delete obj[prop];

	return obj;
}

function cleanBlock(block){ //this function removes many useless for our cases fields in the block and txs
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

	//parity-related properties
	delete block.sealFields;
	delete block.author;

	if(block.transactions.length > 0 && typeof block.transactions[0] !== 'string'){
		for(i=0; i<block.transactions.length; i++){
			tx = block.transactions[i];

			cleanTransaction(tx);
		}
	}

	return block;
}

//sets a 'date' field for each log and each trace, according to their block timestamp
//renames block.timestamp to block.date
//takes in a variable number of time series object arguments
function copyDateFromBlocks(blocks, objects){
	assert(arguments.length >= 2);
	
	for(let j=1; j<arguments.length; j++){
		let obj = arguments[j];
		for(let i=0; i<obj.length; i++){
			obj[i].date = blocks[obj[i].blockNumber].timestamp;
		}
	}
}

function sortByField(obj, field, ascending=true){
	obj.sort(function(a, b){
		if(ascending) {
			return a[field] - b[field];
		} else {
			return b[field] - a[field];
		}
	});

	return obj;
}

function dictToList(obj){
	let list = [];

	for(let key in obj) {
		list.push(obj[key]);
	}

	return list;
}

function extractTxsFromBlockDict(blockDict){
	let transactions = [];
	for(let key in blockDict){
		let txs = blockDict[key].transactions;

		transactions.push.apply(transactions, txs);

		delete blockDict[key].transactions;
	}

	return transactions;
}

//requests a given block range in the interval [start, end] (inclusive of end)
function requestBlockRange(start, end, handler){
	for(let i=start; i<=end; i++) {
		requestBlock(i, handler);
	}
}

//requests blocks from given array of block numbers
function requestBlocks(blocks, handler){
	for(let i=0; i<blocks.length; i++) {
		requestBlock(blocks[i], handler);
	}
}

//requests a block and calls the given handler with the result
function requestBlock(blockN, handler, includeTXs=true){
	web3.eth.getBlock(blockN, includeTXs, handler);
}

//iterates the dict with keys from first to first+len and returns an array of missing keys
function listMissingBlocks(dict, first, last){
	let missing = [];

	for(let bl = first; bl <= last; bl++){
		if(dict[bl] == null){
			missing.push(bl);
		}
	}

	return missing;
}

function structureBlockchainData(blockDict, logs, traces){
	let transactions = extractTxsFromBlockDict(blockDict);

	if(typeof transactions[0] === 'string'){
		transactions = []; //we don't need to store transactions if they consist only of tx hashes!
	}

	copyDateFromBlocks(blockDict, logs, traces, transactions);
	
	let blockList = dictToList(blockDict);
	sortByField(blockList, 'date');
	sortByField(logs, 'date');
	sortByField(traces, 'date');
	sortByField(transactions, 'date');


	console.log("Successfully loaded "+blockList.length+" blocks");
	console.log("First block is "+blockList[0].number+" and last one is "+blockList[blockList.length-1].number);
	
	let blockchain = {logs: logs, traces: traces, blocks: blockList, transactions: transactions};

	//remove if we don't have TXs
	if(transactions.length == 0){
		delete blockchain.transactions;
	}
	
	return blockchain;
}

function saveAsJSON(data){
	sw.start();

	var file = JSON.stringify(data);
	var filename = datadir+"blocks "+data['blocks'][0].number+"-"+data['blocks'][data['blocks'].length-1].number+".json";

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

	var start = (new Date).getTime();
	for(var i=0; i<expected; i++){
		web3.eth.getTransactionReceipt("0x674d990c9a298fd995f02ef4b923211f3e4208828014417ba45f8d467657ee38", handler2);
	}
}

//this function is to make quick functionality test - not to be confused with unit testing.
function testFilters(){
	initBlockchain();

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

async function processArgs(){
	if(process.argv.length == 2) printHelp();
	else{
		for(argIndex = 2; argIndex<process.argv.length; argIndex++){
			arg = process.argv[argIndex];

			if(arg.search('help') >=0) printHelp();
			else if(arg == 'course') downloadWholeCourse();
			else if(arg == 'blockchain'){
				var start = parseInt(process.argv[argIndex+1]);
				var end = parseInt(process.argv[argIndex+2]);
				argIndex += 2;
				if(isNaN(start) || isNaN(end)){
					console.log("Enter the start block and block count to download.");
					break;
				}

				if(!initBlockchain()) return;

				const tracesReq = getTransactionTraces(start, end);
				const logsReq = getContractLogs(start, end);
				const blocksReq = downloadBlockchain(start, end);

				const res = await Promise.all([blocksReq, logsReq, tracesReq]);

				let blockchain = structureBlockchainData(res[0], res[1], res[2]);
				saveAsJSON(blockchain);
			}
			else if(arg == 'test'){
				testFilters()
			}
		}
	}
}

processArgs();
