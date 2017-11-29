#include <iostream>
#include <map>
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <chrono>

typedef std::array<char, 43> acc;
typedef std::array<int, 2> feat;
typedef std::map<acc, feat> accMap;

const int group0 = 10;
const int group1 = 10;

const int max0 = 1000000;
const int max1 = 2592000;

int lastTimestamp = 5;

void createDistribution(accMap accounts, int res[group0][group1]){
	const double smax0 = log10(max0), smax1 = log10(max1);

	for (auto const &it : accounts){
		int arg0 = std::min(int((log10(it.second[0]) / smax0) * group0), group0-1);
		int arg1 = std::min(int((log10(it.second[1] - lastTimestamp) / smax1) * group1), group1-1);

		res[arg0][arg1] ++;
	}
}

int main(){

	accMap accounts;

	acc acc = {"0xb794f5ea0ba39494ce839613fffba74279579268"};

	for(int i=0; i<1000000; i++){
		int num = i;
		for(int j=20; num>0; j++){
			acc[j] = 48 + num % 10;
			num /= 10;
		}

		accounts[acc] = {i,i};
	}

	int res[group0][group1] = {}; //will init whole array to 0.

	std::cout<<res[5][8]<<std::endl;

	auto start = std::chrono::high_resolution_clock::now();

	createDistribution(accounts, res);

	auto end = std::chrono::high_resolution_clock::now();

	std::chrono::duration<double> elapsed = end - start;

	std::cout << "Elapsed time: " << elapsed.count() << " s\n";

	return 0;
}