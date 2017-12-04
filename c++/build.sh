g++ -O3 -Wall -shared -std=c++11 -lgmpxx -lgmp -fPIC `python3-config --includes` -I`pwd` propertyBalanceLastSeenDistribution.cpp -o build/cppBalanceLastSeen`python3-config --extension-suffix`
