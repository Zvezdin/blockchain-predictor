#include <iostream>
#include <map>
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <chrono>
#include <cstring>
#include <algorithm>

#include <boost/multiprecision/gmp.hpp>

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/stl_bind.h>

struct StrCompare : public std::binary_function<const char*, const char*, bool> {
public:
    bool operator() (const char* str1, const char* str2) const
    { return std::strcmp(str1, str2) < 0; }
};

struct cmp_str //a comparator for two cstrings, otherwise the map will compare the pointers.
{
	bool operator()(char const *a, char const *b)
	{
		return std::strcmp(a, b) < 0;
	}
};

#define MODULE_NAME cppBalanceLastSeen
#define SCALE log2

const double SCALE_MUL = 1.0;

typedef boost::multiprecision::mpz_int largeInt;
typedef boost::multiprecision::mpf_float largeFloat;

typedef double castFloat;

const int accLen = 43;

typedef std::array<char, accLen> acc;

typedef int featType;
typedef std::array<featType, 2> feat;
typedef const char* RawKey;
typedef std::map<acc, feat> accMap;

PYBIND11_MAKE_OPAQUE(accMap);

namespace py = pybind11;

const featType max0(10000000); //Max Bal for scale, in ETH / 10
const featType max1(2592000*2); //in seconds, or 60 days

//modern day capitalism 101
const bool maxCutoff0 = false; //don't cut off the richest 
const bool minCutoff0 = false; //don't cut off the poorest <=1 ETH
const bool maxCutoff1 = true; //cut off the inactive ones
const bool minCutoff1 = false; //no need to cut off the most active

const int group0 = int(SCALE(static_cast<castFloat>(max0) * SCALE_MUL)); //our group counts are dynamic and depend on our max values
const int group1 = int(SCALE(static_cast<castFloat>(max1) * SCALE_MUL));

typedef std::array<std::array<featType, group1>, group0> result;

castFloat linearScale(castFloat x){
	return x;
}

//It is bad practice to include .cpp files, but this is needed for our binding needs.
#include <propertyAccountNumberDistribution.cpp>
