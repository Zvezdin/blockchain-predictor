var fs = require('fs')

var f = fs.readFileSync('data/blocks 4000000-4009999.json');
var data = JSON.parse(f);

printDataLength(data)

function printDataLength(data){
	lens = []

	for (var i=0; i<data.length; i++){
		var block = data[i];

		if (block.transactions != undefined) {
			for(var j=0; j<block.transactions.length; j++){
				var tx = block.transactions[j];
				if(tx.logs != undefined){
					for(var k=0; k<tx.logs.length; k++){
						lens.push(tx.logs[k].data.length);
					}
				}
			}
		}
	}

	lens.sort(function(a, b){return b - a});

	console.log(lens);

	console.log(typeof lens[0])
}