//Downloads certain blockchain data of the given time period and saves it as the given file (.json)
var Web3 = require("web3");
var https = require("https");
var fs = require('fs');

var web3;

var debug = true;

function initLibraries(){
    if (typeof web3 !== 'undefined') {
        web3 = new Web3(web3.currentProvider);
    } else {
    // set the provider from Web3.providers
        console.log("Attempting connection to RPC...");
        web3 = new Web3(new Web3.providers.HttpProvider("http://localhost:8545"));
        if(typeof web3.isConnected !== "undefined" && web3.isConnected()) console.log("Successful connection!");
    }

    console.log(web3.eth.blockNumber);
    console.log(web3.eth.accounts);

    web3.eth.getBlock(48, function(error, result){
        if(!error)
            console.log(result)
        else
            console.error(error);
    })
}

function downloadPrice(start, end, count, source, callback){
    var responseString = "";

    request = "";

    if(source == "poloniex"){
        request = "https://poloniex.com/public?command=returnChartData&currencyPair=USDT_ETH&start="+start+"&end="+end+"&period=300"
    }else if(source == "cryptocompare"){
        request = 'https://min-api.cryptocompare.com/data/histohour?fsym=ETH&tsym=USD&limit='+count+'&aggregate=3&e=CCCAGG&toTs='+start;
    } else callback(undefined)

    https.get(request, (res) => {
        console.log('statusCode:', res.statusCode);
        console.log('headers:', res.headers);

        responseString = "";

        res.on('data', function (chunk) {
            responseString += chunk;
        });

        res.on('end', function(){
            var filename = source + "_price_data.json"

            console.log("Received size is "+responseString.length);

            fs.writeFile("data/"+filename, responseString, function(err) {
                if(err) {
                    console.log(err);
                    callback(undefined);
                    return;
                }

                console.log("The data was saved as "+filename);
            }); 

            callback(JSON.parse(responseString));
        });

    }).on('error', (e) => {
        console.error(e);
        callback(undefined);
    });

}

initLibraries();
downloadPrice(1, 999999999999999, undefined, "poloniex", function(result){
    //console.log(result);
});