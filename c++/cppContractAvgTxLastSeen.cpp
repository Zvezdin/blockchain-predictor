#define MODULE_NAME cppContractAvgTxLastSeen
#define SCALE log10
#define BASE 1.2

typedef int featType;
const featType max0(10000000); //Max TX for scale, in ETH / 10
const featType max1(2592000*2*2*2); //in seconds, or 30*2*2*2 days

const bool maxCutoff0 = false;
const bool minCutoff0 = false;
const bool maxCutoff1 = false; 
const bool minCutoff1 = false;

const bool group1DifferenceLastTimestamp = true;

#include <commonStart.cpp>