#define MODULE_NAME cppContractVolumeInERC20
#define SCALE log2

typedef int featType;
const featType max0(10000000); //Max volume in for scale, in ETH / 10
const featType max1(262144); //max number of ERC20 txs

const bool maxCutoff0 = false;
const bool minCutoff0 = false;
const bool maxCutoff1 = false; 
const bool minCutoff1 = false;

const bool group1DifferenceLastTimestamp = false;

#include <commonStart.cpp>