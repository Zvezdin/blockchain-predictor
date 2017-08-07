//Downloads certain blockchain data of the given time period and saves it as the given file (.json)

var Web3 = require("web3");
var web3;

if (typeof web3 !== 'undefined') {
    web3 = new Web3(web3.currentProvider);
} else {
// set the provider from Web3.providers
    console.log("Attempting connection to RPC...");
    web3 = new Web3(new Web3.providers.HttpProvider("http://localhost:8545"));
    if(web3 != undefined) console.log("Successful connection!");
}

console.log(web3.eth.blockNumber);
console.log(web3.eth.accounts[0]);