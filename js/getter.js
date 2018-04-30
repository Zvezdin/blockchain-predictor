const sw = require("node-stopwatch").Stopwatch.create();
const assert = require('assert').strict;
const big = require("bignumber.js");

const maxAsyncRequests = 8;

module.exports = class Getter {
	constructor(web3) {
		this.web3 = web3;
	}

	assertConnected() {
		assert(this.web3.isConnected());
	}

	downloadBlocks(startBlock, endBlock){
		this.assertConnected();
		
		var self = this;

		return new Promise(function(resolve, reject){
			var blockDict = {}; //temp storage for the received blocks

			var requestedBlocks = 0; //the amount of blocks we have requested to receive
			var receivedBlocks = 0; //how many blocks have been successfully received
			var expectedBlocks = endBlock - startBlock + 1;
			var lastRequestedBlock = 0;
		
			console.log("Downloading blocks from "+startBlock+" to "+endBlock);

			//sw.start();

			var handler = function(err, block){
				if(err) console.error(err, block);
				else {
					//console.log("Got block "+block.number+" with "+block.transactions.length+" transactions in "+sw.elapsed.seconds+"s");
					if(block == null){
						console.error("Received empty block!");
					} else {
						blockDict[block.number] = block;
					}

					receivedBlocks++;

					if(receivedBlocks >= expectedBlocks){
						let missing = self.listMissingBlocks(blockDict, startBlock, endBlock);

						if(missing.length > 0){
							console.error("Detected missing blocks: "+missing+" Re-requesting them!");
							self.requestBlocks(missing, handler);
							return;
						}

						console.log("Received all blocks at "+(receivedBlocks / sw.elapsed.seconds)+"bl/s!");
						resolve(blockDict);
					} else if(requestedBlocks < expectedBlocks){
						//get the next block
						lastRequestedBlock++;
						requestedBlocks++;
						self.requestBlock(lastRequestedBlock, handler);
					}
				}
			}

			let end = Math.min(startBlock + maxAsyncRequests - 1, endBlock);
			
			lastRequestedBlock = end;
			requestedBlocks = Math.abs(end - startBlock) + 1;

			self.requestBlockRange(startBlock, end, handler);

			//sw.stop();
		});
	}

	//iterates the dict with keys from first to first+len and returns an array of missing keys
	listMissingBlocks(dict, first, last){
		let missing = [];

		for(let bl = first; bl <= last; bl++){
			if(dict[bl] == null){
				missing.push(bl);
			}
		}

		return missing;
	}

	//requests a given block range in the interval [start, end] (inclusive of end)
	requestBlockRange(start, end, handler){
		for(let i=start; i<=end; i++) {
			this.requestBlock(i, handler);
		}
	}

	//requests blocks from given array of block numbers
	requestBlocks(blocks, handler){
		for(let i=0; i<blocks.length; i++) {
			this.requestBlock(blocks[i], handler);
		}
	}

	//requests a block and calls the given handler with the result
	requestBlock(blockN, handler, includeTXs=true){
		this.web3.eth.getBlock(blockN, includeTXs, handler);
	}

	//returns a promise for all transaction traces for the block range [start, end]
	//requires the parity node to run! Only parity supports JSON RPC transaction tracing api!
	getTransactionTraces(start, end, batchSize=100000){
		this.assertConnected();

		//TODO: If an error occurs, try to get it in smaller chunks
		console.log("Getting all tx traces from "+start+" to "+end);

		var self = this;

		return new Promise(async function(resolve, reject) {
			var result = [];

			for(var offset=new big(0);; offset = offset.add(batchSize)){
				var params = {
					method: "trace_filter",
					params: [{fromBlock: "0x" + (+start).toString(16), toBlock: "0x" + (+end).toString(16), after: +offset.valueOf(), count: batchSize}],
					jsonrpc: "2.0",
					id: "1583"
				};

				//var out = web3.currentProvider.send(params);
				var out = await self.web3CustomSend(params);

				var len = out.result.length;
				result.push.apply(result, out.result)

				console.log("Received a batch of "+len+" traces.");

				if(len < batchSize){
					//this was the last batch of traces 
					break;
				}
			
			}

			assert(start == 0 || result[0].blockNumber == start);
			assert(result[result.length-1].blockNumber == end);

			console.log("Received traces with length "+result.length);
			resolve(result);
		});
	}

	web3CustomSend(params) {
		var self = this;
		return new Promise(function(resolve, reject){
			self.web3.currentProvider.sendAsync(params, function(err, res){
				if(err){
					reject(err);
				} else {
					resolve(res);
				}
			});
		});
	}

	//will get all logs from contracts within [start, end] block interval
	getContractLogs(start, end){
		this.assertConnected();

		var self = this;

		return new Promise(function(resolve, reject) {
			var filter = self.web3.eth.filter({'fromBlock': start, 'toBlock': end});
			
			var handlerCB = function(err, res){
				if(err){
					console.error(err);
					reject(err);
					return;
				}

				console.log("Received logs with length ", res.length);

				resolve(res);
			}

			filter.get(handlerCB)

			console.log("Getting logs for blocks from/to", start, end);
		});
	}

	async getAll(start, end) {
		this.assertConnected();

		const tracesReq = this.getTransactionTraces(start, end);
		const logsReq = this.getContractLogs(start, end);
		const blocksReq = this.downloadBlocks(start, end);

		const res = await Promise.all([blocksReq, logsReq, tracesReq]);
		const formatted = {log: res[1], trace: res[2], block: res[0]};

		return formatted;
	}
}