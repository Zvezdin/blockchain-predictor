//Downloads certain blockchain data of the given time period and saves it as the given file (.json)
var Web3 = require("web3");
var https = require("https");

var web3;

var debug = true;

function initLibraries(){
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

}

function downloadPriceBefore(date, count, callback){
    var responseString = "";
    https.get('https://min-api.cryptocompare.com/data/histohour?fsym=ETH&tsym=USD&limit='+count+'&aggregate=3&e=CCCAGG&toTs='+date+'', (res) => {
        console.log('statusCode:', res.statusCode);
        console.log('headers:', res.headers);

        responseString = "";

        res.on('data', function (chunk) {
            if(debug) console.log("Got a chunk!");
            responseString += chunk;
        });

        res.on('end', function(){
            callback(JSON.parse(responseString));
        });

    }).on('error', (e) => {
        console.error(e);
        callback(undefined);
    });

}

initLibraries();
downloadPriceBefore(1440000000, 1500, function(result){
    console.log(result);
});