const fs = require("fs");

module.exports = class JsonUtil {
	constructor(){}

	save(json, filename) {
		fs.writeFileSync(filename, JSON.stringify(json));
		console.log("The data was saved as "+filename);
	}

	load(filename) {
		let bytes = fs.readFileSync(filename);
		return JSON.parse(bytes);
	}
}