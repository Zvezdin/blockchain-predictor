var Web3 = require("web3");
const Getter = require("./getter.js");
const get = new Getter(new Web3(new Web3.providers.HttpProvider("http://localhost:8545")));
const Cacher = require("./cacher.js");
const cacher = new Cacher("/secondStorage/programming/chain/cache");

cacher.cacheAll(20);
