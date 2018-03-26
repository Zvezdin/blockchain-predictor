var Web3 = require("web3");

web3 = new Web3(new Web3.providers.HttpProvider("http://localhost:8545"));

console.log("Block N:", web3.eth.blockNumber);
console.log("Accounts:", web3.eth.accounts);


web3.currentProvider.sendAsync({
	method: "trace_transaction",
	params: ['0xd464bca4552371be4aa96a74370dafa9d3efa4f7196e21444644c852d44f79ca'],
	jsonrpc: "2.0",
	id: "2"
}, function (err, result) {
	console.log(err);
	console.dir(result, {depth:null})
});

var start = 4000000;
var end = 4000100;

web3.currentProvider.sendAsync({
	method: "trace_filter",
	params: [{fromBlock: "0x" + start.toString(16), toBlock: "0x" + end.toString(16)}],
	jsonrpc: "2.0",
	id: "2"
}, function (err, result) {
	console.log("Err:", err);
	result = result.result;

	console.log(result.length);

	for(var i=0; i<result.length; i++) {
		var res = result[i];

		if(res.type !== 'reward' && res.type !== 'call' && res.type !== 'create' && res.type !== 'suicide'){
			console.log("Found something different!")
			console.dir(res, {depth:null})
		}

		if(res.type === 'call' && res.action.callType !== 'call' && res.action.callType !== 'delegatecall' && res.action.callType !== 'staticcall'){
			console.log("Got a different call type!");
			console.dir(res, {depth:null})
		}

		if(res.type === 'reward' && res.action.rewardType !== 'block' && res.action.rewardType !== 'uncle'){
			console.log("Got a different reward type!");
			console.dir(res, {depth:null})
		}
	}
});
