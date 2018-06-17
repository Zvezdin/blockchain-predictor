//Downloads certain blockchain data of the given time period and saves it as the given file (.json)
const https = require("https");
const fs = require('fs');
const Stopwatch = require("node-stopwatch").Stopwatch;
const util = require('util')
const assert = require('assert').strict;
const ArgumentParser = require("argparse").ArgumentParser;
const big = require("bignumber.js");

const Cacher = require("./js/cacher.js");
const cacher = new Cacher("/secondStorage/programming/chain/cache");

const JsonUtil = require("./js/json_util.js");
const jsonUtil = new JsonUtil();

const sw = Stopwatch.create();

var debug = true;

var datadir = 'data/'

const maxAsyncRequests = 8;

const saveSpace = true;


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

function downloadCourseCryptocompare(start, end, callback){
	var data = []

	const firstTimestamp = 1438959600 //this timestamp is the first data that this source has

	return new Promise(function(resolve, reject){
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

					resolve(data)
				}
			})
		}

		sendRequest(end)
	});
}

function downloadCoursePoloniex(start, end){
	var request = "https://poloniex.com/public?command=returnChartData&currencyPair=USDT_ETH&start="+start+"&end="+end+"&period=300"

	return new Promise(function(resolve, reject){
		JSONRequest(request, function(res){
			resolve(res)
		});
	});
}

function downloadCourse(start, end, source){
	var request = "";

	return new Promise(function(resolve, reject){
		if(source == "poloniex"){
			downloadCoursePoloniex(start, end).then(res => {
				resolve(res);
			});
		} else if(source == "cryptocompare"){
			downloadCourseCryptocompare(start, end).then(res => {
				resolve(res);
			});
		} else reject("Invalid source specified: "+source);
	});
}

function downloadWholeCourse(){
	return downloadCourse(1, 999999999999999, "cryptocompare");
}


function preprocessBlocks(blocks) {
	for(let key in blocks) {
		cleanBlock(blocks[key]);
	}

	return blocks;
}

function preprocessContractLogs(logs) {
	for(var i=0; i<logs.length; i++){ //clean the logs
		cleanLog(logs[i]);
	}

	return logs;
}


function preprocessTransactionTraces(traces, noErrors=true, noEmpty=true, noSuicideSpam=true){
	let result = [];

	let emptyRemovals = 0;
	let errorRemovals = 0;
	let suicideRemovals = 0;

	//key -> value of failed transactions
	//because in traces, only the first trace is errored
	let failedTransactions = {};

	//addr -> bool whether a contract has been killed
	//to filter any further calls to this contract
	//see: https://etherscan.io/tx/0x5c8628001bcfca3f2f4e8e3e345491d3971c61af36b6d37b57117ac97e711ab5 for example
	let killedContracts = {};

	let rawResult = traces;

	
	for(let i=0; i<rawResult.length; i++) {
		let el = rawResult[i];

		if(noErrors) {
			//block rewards don't have a transaction hash
			if(el.transactionHash && (el.error || failedTransactions[el.transactionHash.toLowerCase()])) {
				failedTransactions[el.transactionHash.toLowerCase()] = true;
				//TODO: What about gas spendings and this depleting the account balance?
				errorRemovals++;
				continue;
			}
		}

		cleanAndNormalizeTrace(el);

		if(noSuicideSpam) {
			if(killedContracts[el.to] || killedContracts[el.from]) {
				suicideRemovals++;
				continue;
			}
		}

		if(el.type == 'suicide') {
			killedContracts[el.from] = true;
		}

		if(noEmpty && el.value == '0x0' && el.gasUsed == '0x0' && el.gas == '0x0') {
			//Warning: There are transactions that use 0 gas and transfer 0 wei, but have provided gas.
			//not sure if we should discard those or not. 
			//they don't look like to change blockchain state though
			
			emptyRemovals++;
			continue;
		}

		result.push(el);
	}

	console.log("Cleaned traces with "+emptyRemovals+" empty, "+errorRemovals+" error and "+suicideRemovals+" suicide removals.");

	return result;
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

	//since this was loaded from a JSON, the BigNumber objects are no longer present
	//tx.gasPrice = tx.gasPrice.toFixed()
	//tx.value = tx.value.toFixed()

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

	//since this was loaded from a JSON, the BigNumber objects are no longer present
	//block.difficulty = block.difficulty.toFixed()
	//block.totalDifficulty = block.totalDifficulty.toFixed()

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
			obj[i].date = blocks[obj[i].blockNumber].date;
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
	
	let blockchain = {log: logs, trace: traces, block: blockList, tx: transactions};

	//remove if we don't have TXs
	if(transactions.length == 0){
		delete blockchain.transactions;
	}
	
	return blockchain;
}

async function saveBlockchain(start, end, filename) {
	let preprocessCallbacks = {'block': preprocessBlocks, 'log': preprocessContractLogs, 'trace': preprocessTransactionTraces};

	let res = cacher.getBlockRange(start, end, preprocessCallbacks);

	let txCount = 0;
	let blCount = 0;

	for(let bl in res['block']) {
		txCount += res['block'][bl].transactions.length;
		blCount++;
	}

	let traceCount = res['trace'].length;

	console.log("The resulting package contains "+txCount+" transactions, "+res['log'].length+" logs and "+traceCount+" traces.");
	
	//check if there have been too many traces, but only if we actually had enough transactions
	if(txCount > blCount && traceCount > txCount * 5) {
		console.error("Too many traces compared to transactions! Breaking, take a look.");
		assert(false);
	}

	let blockchain = structureBlockchainData(res['block'], res['log'], res['trace']);
	
	if(filename == null){
		filename = datadir+"blocks "+blockchain['block'][0].number+"-"+blockchain['block'][blockchain['block'].length-1].number+".json";
	}

	jsonUtil.save(blockchain, filename);
}

async function saveCourse(filename) {
	let course = await downloadWholeCourse()
	if(!filename){
		filename = 'data/course.json';
	}
	jsonUtil.save(course, filename)
}

function main() {
	var parser = new ArgumentParser({
		version: '0.1.0',
		addHelp:true,
		description: 'A tool to download cryptocurrency course and blockchain data and save them as a json'
	});

	parser.addArgument(
		[ '--blockchain' ],
		{
			help: 'Download blockchain data with for a block range of given start and end block number',
			nargs: 2,
			defaultValue: false,
			type: Number,
		},
	);

	parser.addArgument(
		['--course'],
		{
			help: 'Downloads the whole history of the token course from an exchange',
			defaultValue: false,
			action: "storeTrue",
		},
	)

	parser.addArgument(
		['--filename'],
		{
			help: 'Location to save downloaded data',
			type: String,
		},
	)


	var args = parser.parseArgs();

	if(!args.course && !args.blockchain) {
		console.error("Please choose an action! Run with '-h' for a help page.");
		return;
	}

	if(args.course){
		saveCourse(args.filename);
	} else if (args.blockchain != null) {
		let start = args.blockchain[0];
		let end = args.blockchain[1];

		if(isNaN(start) || isNaN(end)){
			console.log("Enter the start block and block count to download.");
			return;
		}

		saveBlockchain(start, end, args.filename);
	}
}

main();
