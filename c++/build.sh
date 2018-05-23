set -e #terminate on error

for module in cppContractAvgTxLastSeen cppContractVolumeInERC20 cppBalanceLastSeen
do
    c++ -O3 -Wall -shared -std=c++11 -fPIC `python3-config --includes` -I`pwd` ${module}.cpp -o build/${module}`python3-config --extension-suffix`
    echo "Build of ${module} successful!"
done
