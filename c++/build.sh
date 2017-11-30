g++ -O3 -Wall -shared -std=c++11 -lgmpxx -lgmp -fPIC `python3-config --includes` propertyBalanceLastSeenDistribution.cpp -o build/example`python3-config --extension-suffix`
