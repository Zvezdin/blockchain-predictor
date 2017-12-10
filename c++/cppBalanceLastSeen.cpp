#define MODULE_NAME cppBalanceLastSeen
#define SCALE log10
#define BASE 1.2

typedef int featType;
const featType max0(10000000); //Max Bal for scale, in ETH / 10
const featType max1(2592000*2*2*2); //in seconds, or 30*2*2*2 days

//modern day capitalism 101
const bool maxCutoff0 = false; //don't cut off the richest 
const bool minCutoff0 = false; //don't cut off the poorest <=1 ETH
const bool maxCutoff1 = true; //cut off the inactive ones
const bool minCutoff1 = false; //no need to cut off the most active

const bool group1DifferenceLastTimestamp = true;

#include <commonStart.cpp>