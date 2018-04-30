const Getter = require("./getter.js");
const Web3 = require("web3");
const assert = require("assert");
const fs = require("fs");
const get = new Getter(new Web3(new Web3.providers.HttpProvider("http://localhost:8545")));
const JsonUtil = require("./json_util.js");
const jsonUtil = new JsonUtil();

//spam: 3804900

module.exports = class Cacher {
	constructor(folder) {
		this.folder = folder;
		let filenames = fs.readdirSync(folder);
		this.sortFiles(filenames);
		this.filenames = filenames;

		this.prevEnd = -1;

		this.startToFile = {};
		this.blockToStart = {};

		this.updateFiles();

		console.log(this.prevEnd);
	}

	async cacheOne(start, end) {
		let filename = this.blockRangeToFilename(start, end);
		var path = this.folder + "/" + filename;
		if(!fs.existsSync(path)){
			this.updateNewFile(filename);

			const res = await get.getAll(start, end);
			
			jsonUtil.save(res, path);
		}
	}

	async cacheAll(series=50, end=5528000) {
		let startBlock = this.prevEnd+1;
		
		for(; startBlock <= end - series; startBlock += series){
			await this.cacheOne(startBlock, startBlock + series - 1);
		}
	}

	sortFiles(filenames) {
		var self = this;

		function cmp(a, b){
			let start1 = self.filenameToBlockRange(a)[0];
			let start2 = self.filenameToBlockRange(b)[0];

			return start1-start2;
		}

		filenames.sort(cmp);

		return filenames;
	}

	updateFiles() {
		for(let i=0; i<this.filenames.length; i++){
			this.updateNewFile(this.filenames[i]);
		}
	}

	updateNewFile(filename) {
		let tmp = this.filenameToBlockRange(filename);
		let start = tmp[0];
		let end = tmp[1];

		assert(this.prevEnd + 1 == start);
		this.prevEnd = end;
	
		assert(start<=end);

		for(let j=start; j<=end; j++){
			this.blockToStart[j] = start;
		}
		this.startToFile[start] = filename;
	}

	getFilesForBlockRange(start, end) {
		assert(this.blockToStart[start] !== undefined);
		assert(this.blockToStart[end] !== undefined);

		let files = [];

		let currentStart = start;
		let currentEnd = -1;

		while(currentEnd < end){
			let tmp = this.blockToStart[currentStart];
			assert(tmp !== undefined);

			let file = this.startToFile[tmp];
			assert(file !== undefined);

			files.push(file);

			currentEnd = this.filenameToBlockRange(file)[1];
			currentStart = currentEnd+1;
		}

		return files;
	}
	
	blockRangeToFilename(start, end) {
		return "blockchain_"+start+"_"+end+".json";
	}

	filenameToBlockRange(filename) {
		let pieces = filename.split("_");

		assert(pieces.length == 3);

		let start = +pieces[1];
		let end = +pieces[2].split(".")[0];

		assert(start <= end);

		return [start, end];
	}

	loadFile(filename, start=undefined, end=undefined) {
		let obj = jsonUtil.load(this.folder + "/" + filename);

		if(start !== undefined || end !== undefined){ //filter by given start or end
			for(let key in obj) { //for each key ex. block, trace, log, ...
				if(Array.isArray(obj[key])){
					let arr = obj[key];

					for(let i=0; i<arr.length; i++) {
						if(
							(start !== undefined && arr[i]['blockNumber'] < start) ||
							(end !== undefined && arr[i]['blockNumber'] > end)
						) {
							arr.splice(i, 1);
							i--;
						}
					}
					
					if(arr.length > 0){
						if(start !== undefined) {
							assert(arr[0]['blockNumber'] >= start);
						}

						if(end !== undefined) {
							assert(arr[arr.length-1]['blockNumber'] <= end);
						}
					}
				} else {
					let dict = obj[key];
					for(let blockN in dict) {
						assert(dict[blockN]['number'] == +blockN);

						if(
							(start !== undefined && +blockN < start) ||
							(end !== undefined && +blockN > end)
						) {
							delete dict[blockN];
						}
					}

					if(start !== undefined) {
						assert(dict[start] != undefined);
						assert(dict[start-1] == undefined);
					}

					if(end !== undefined) {
						assert(dict[end] != undefined);
						assert(dict[end+1] == undefined);
					}
				}
			}
		}

		return obj;
	}

	mergeTimeSeries(objects) {
		assert(objects.length >= 1);

		let obj = {};

		for(let key in objects[0]) {
			obj[key] = objects[0][key];
			let currSet = obj[key];

			for(let i=1; i<objects.length; i++) {
				if(Array.isArray(currSet)) {
					let currEl = objects[i][key];
					let newLen = currEl.length;
					let currLen = currSet.length;

					//make sure that we're appending from where we left off
					if(currSet.length > 0 && currEl.length > 0){
						assert(currSet[currSet.length-1]['blockNumber'] + 1 <= currEl[0]['blockNumber']);
					}
					
					//push the content
					for(let i=0; i<currEl.length; i++) {
						currSet.push(currEl[i]);
					}
					
					assert.deepEqual(currSet.length, currLen + newLen);
				} else {
					for(let blockN in objects[i][key]) {
						assert(currSet[blockN-1] != undefined);
						assert(currSet[blockN] == undefined);

						//copy the content key-by-key
						currSet[blockN] = objects[i][key][blockN];
					}
				}
			}
		}

		return obj;
	}

	getBlockRange(start, end, preprocessCallbacks={}) {
		if(end > this.prevEnd) {
			//update the cache by downloading everything up until this moment
			cacheAll(undefined, end);

			//this will often fail - the new end needs to be prevEnd+series or a factor of that in order to successfully cache it
			//TODO: in these cases, directly call the blockchain and cache when the new data reaches the size of 'series'
			assert(this.prevEnd >= end);
		}

		let files = this.getFilesForBlockRange(start, end);
		assert(files.length >= 1);

		let objects = [];

		for(let i=0; i<files.length; i++) {
			let currObj = this.loadFile(files[i], (i == 0 ? start : undefined), (i == files.length-1 ? end : undefined));
			for(let key in currObj) {	
				if(preprocessCallbacks[key] !== undefined) {
					currObj[key] = preprocessCallbacks[key](currObj[key]);
				}
			}
			objects.push(currObj);
		}

		let obj = this.mergeTimeSeries(objects);

		return obj;
	}
}
