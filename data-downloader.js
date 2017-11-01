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

const maxAsyncRequests = 2;

var requestedBlocks = 0;

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

	console.log("Downloading blocks...");

	sw.start();

	var handler = function(err, block){
		if(err) console.error(err, block);
		else {
			//console.log("Got block "+block.number+" with "+block.transactions.length+" transactions in "+sw.elapsed.seconds+"s");
			if(block == null){
				console.error("Received empty block!");
			} else {
				cleanBlock(block);
				blockDict[block.number] = block;
			}

			receivedBlocks ++;

			if(receivedBlocks >= expectedBlocks){
				if(!validateBlocks(blockDict, startBlock, expectedBlocks, handler)) return;

				console.log("Received all blocks at "+(receivedBlocks / sw.elapsed.seconds)+"bl/s!");
				processBlocks(blockDict, startBlock);
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

	for(i=0; i<block.transactions.length; i++){
		tx = block.transactions[i];

		delete tx.blockHash;
		delete tx.blockNumber;
		delete tx.hash;
		delete tx.nonce;
		delete tx.v;
		delete tx.r;
		delete tx.s;
		delete tx.input;
		delete tx.transactionIndex;
	}
}

function getBlock(blockN, handler){
	web3.eth.getBlock(blockN, true, handler);
}

function getNextBlock(startBlock, handler){
	getBlock(startBlock+requestedBlocks, handler);
	requestedBlocks++;
}

var blockchain = [];

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
	sw.start();
	var block;
	for(i = first;; i++){
		block = dict[i];

		if(block != undefined) blockchain.push(block);
		else break;
	}

	blockDict = {};

	console.log("Successfully loaded "+blockchain.length+" blocks");
	console.log("First block is "+blockchain[0].number+" with " + blockchain[0].transactions.length+" transactions!");
	console.log("Last block is "+blockchain[blockchain.length-1].number+" with " + blockchain[blockchain.length-1].transactions.length+" transactions!");

	var file = JSON.stringify(blockchain);
	var filename = datadir+"blocks "+blockchain[0].number+"-"+blockchain[blockchain.length-1].number+".json"
	console.log("Data to save is "+file.length+" bytes long.");
	fs.writeFile(filename, JSON.stringify(blockchain), function(err) {
		if(err) {
			console.log(err);
			sw.stop();
			return;
		}

		console.log("The data was saved in "+sw.elapsed.seconds+"s as "+filename);
	});
	sw.stop();
}

function compareBlocks(a, b){
	if (a.timestamp < b.timestamp)
		return -1;
	if (a.last_nom > b.last_nom)
		return 1;
	return 0;
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
		}
	}
}

processArgs();