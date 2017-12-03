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

accMap accounts;

result createDistribution(accMap accounts, int lastTimestamp){
	result res = {}; //will init whole array to 0.

	const double smax0 = log10(max0), smax1 = log10(max1); //pre-scale our maximum values

	for (auto const &it : accounts){
		int arg0 = std::min(int((log10(it.second[0]) / smax0) * group0), group0-1);
		int arg1 = std::min(int((log10(std::abs(it.second[1] - lastTimestamp)) / smax1) * group1), group1-1);

		std::cout<<arg0<<arg1<<std::endl;
		std::cout<<(it.second[1] - lastTimestamp)<<((it.second[1] - lastTimestamp) / smax1)<<(((it.second[1] - lastTimestamp) / smax1) * group1)<<std::endl;

		res[arg0][arg1] ++;
	}

	return res;
}

result pythonDistribution(int lastTimestamp){
	return createDistribution(accounts, lastTimestamp);
}

void fakeData(accMap accounts){
	acc acc = {"0xb794f5ea0ba39494ce839613fffba74279579268"};
	
	for(int i=0; i<1000000; i++){
		int num = i;
		for(int j=20; num>0; j++){
			acc[j] = 48 + num % 10;
			num /= 10;
		}

		accounts[acc] = {i,i};
	}
}

acc transformKey(const char* rawKey){
	acc key = {0};

	std::copy(rawKey, rawKey+43, std::begin(key));

	return key;
}

acc transformKey(std::string rawKey){
	acc key = {0};

	const char* cstr = rawKey.c_str();
	std::copy(cstr, cstr+43, std::begin(key));

	return key;
}

void setItem(RawKey rawKey, short index, featType val, bool add, bool subtract, bool stayPositive){
	featType* currVal = &accounts[transformKey(rawKey)][index];

	if(add){
		*currVal += val;
	}
	else if(subtract){
		if(stayPositive && *currVal < val){
			*currVal = 0; 
		} else {
			*currVal -= val;
		}
	}
	else {
		*currVal = val;
	}
}

//for values that are small enough to fit within an int
void setItemInt(RawKey rawKey, short index, int val, bool add, bool subtract, bool stayPositive){
	std::cout<<"Setting with int"<<std::endl;
	
	setItem(rawKey, index, val, add, subtract, stayPositive);
}

void setItemStr(RawKey rawKey, short index, char* val, bool add, bool subtract, bool stayPositive){
	//not needed when featType is int
	//setItem(rawKey, index, featType(val), add, subtract, stayPositive);
}



featType getItem(RawKey rawKey, short index){
	return accounts[transformKey(rawKey)][index];
}

int getItemInt(RawKey rawKey, short index){
	return static_cast<int>(getItem(rawKey, index));
}

char* getItemStr(RawKey rawKey, short index){
	//return getItem(rawKey, index).str();
	//doesn't work with integer featType
	return NULL;
}

int getLen(){
	return accounts.size();
}

void test(){
	createDistribution(accounts, 100);
}

int test2(char* a){
	std::array<char, 43> test;// = a;
	std::copy(a, a+43, std::begin(test));

	int sum = 0;

	for (int i=0; i<43; i++){
		sum += test[i];
	}

	return sum;
}

int test3(std::string a){
	const char *test = a.c_str();// = a;
	
	int sum = 0;

	for (int i=0; i<43; i++){
		sum += test[i];
	}

	return sum;
}

void test4(const char* numStr){
	largeInt a(numStr);
	for(int i=0; i<1000000; i++){

		/*for(int i=0; numStr[i] != '\0'; i++){
			a *= 10;
			a += int(numStr[i]) - 48;
		}*/

		//std::cout<<a<<std::endl;

		//largeFloat b = static_cast<largeFloat>(a);

		//std::cout<<b<<std::endl;

		//std::cout<<boost::multiprecision::log1p(a)<<std::endl;

		//boost::multiprecision::acos(a);

		boost::multiprecision::log10(static_cast<largeFloat>(a));

		a.str();
	}
}

int main(){
	fakeData(accounts);

	auto start = std::chrono::high_resolution_clock::now();

	createDistribution(accounts, 5);

	auto end = std::chrono::high_resolution_clock::now();

	std::chrono::duration<double> elapsed = end - start;

	std::cout << "Elapsed time: " << elapsed.count() << " s\n";

	return 0;
}

PYBIND11_MODULE(example, m) {
	m.doc() = "pybind11 bindings of a c++ implementation of an account number distribution";
	
	m.def("setInt", &setItemInt, "");
	m.def("setStr", &setItemStr, "");
	m.def("getInt", &getItemInt, "");
	m.def("getStr", &getItemStr, "");
	m.def("len", &getLen, "");
	m.def("test", &test, "");
	m.def("test2", &test2, "");
	m.def("test3", &test3, "");
	m.def("test4", &test4, "");
	m.def("createDistribution", &pythonDistribution, "");
}