#include <iostream>
#include <map>
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <chrono>
#include <cstring>
#include <algorithm>

#include <gmp.h>
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

const int group0 = 10;
const int group1 = 10;

typedef std::array<std::array<int, group0>, group1> result;

typedef std::array<char, 43> acc;
typedef int featType;
typedef std::array<featType, 2> feat;
typedef const char* RawKey;
typedef std::map<acc, feat> accMap;

typedef boost::multiprecision::mpz_int largeInt;
typedef boost::multiprecision::mpf_float largeFloat;

PYBIND11_MAKE_OPAQUE(accMap);

namespace py = pybind11;

const int max0 = 1000000;
const int max1 = 2592000;

//It is bad practice to include .cpp files, but this is needed for our binding needs.
#include <propertyAccountNumberDistribution.cpp>