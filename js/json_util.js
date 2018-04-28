const fs = require("fs");

module.exports = class JsonUtil {
	constructor(){}

	save(json, filename) {
		let bytes = JSON.stringify(json);
		console.log("Saving "+bytes.length+" bytes as "+filename);
		fs.writeFileSync(filename, JSON.stringify(json));
	}

	load(filename) {
		let bytes = fs.readFileSync(filename);
		return JSON.parse(bytes);
	}
}