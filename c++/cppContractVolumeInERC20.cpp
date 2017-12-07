#include <iostream>
#include <map>
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <chrono>
#include <cstring>
#include <algorithm>

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/stl_bind.h>

#define MODULE_NAME cppContractVolumeInERC20
#define SCALE log2

const double SCALE_MUL = 1.0;

typedef double castFloat;

const int accLen = 43;

typedef std::array<char, accLen> acc;

typedef int featType;
typedef std::array<featType, 2> feat;
typedef const char* RawKey;
typedef std::map<acc, feat> accMap;

namespace py = pybind11;

const featType max0(10000000); //Max volume in for scale, in ETH / 10
const featType max1(262144); //max number of ERC20 txs

const bool maxCutoff0 = false;
const bool minCutoff0 = false;
const bool maxCutoff1 = false; 
const bool minCutoff1 = false;

const int group0 = int(SCALE(static_cast<castFloat>(max0) * SCALE_MUL)); //our group counts are dynamic and depend on our max values
const int group1 = int(SCALE(static_cast<castFloat>(max1) * SCALE_MUL));

typedef std::array<std::array<featType, group1>, group0> result;

castFloat linearScale(castFloat x){
	return x;
}

accMap accounts;

result createDistribution(int lastTimestamp){
	result res = {}; //will init whole array to 0.

	for (auto const &it : accounts){
		int arg0, arg1;

		if(it.second[0] <= 1){ //don't want log of 0
			if(minCutoff0) continue;
			arg0 = 0;
		} else if(it.second[0] >= max0){ //compare to the unscaled max
			if(maxCutoff0) continue;
			arg0 = group0-1;
		} else{
			arg0 = std::min(static_cast<int>(SCALE(static_cast<castFloat>(it.second[0]) * SCALE_MUL)), group0-1);
		}

		featType val = it.second[1];

		if(val >= max1){
			if(maxCutoff1) continue;
			arg1 = group1-1;
		} else if (val <= 1){
			if(minCutoff1) continue;
			arg1 = 0;
		} else {
			arg1 = std::min(static_cast<int>(SCALE(static_cast<castFloat>(val) * SCALE_MUL)), group1-1);
		}

		res[arg0][arg1] ++;
	}

	return res;
}

//It is bad practice to include .cpp files, but this is needed for our binding needs.
#include <propertyAccountNumberDistribution.cpp>
