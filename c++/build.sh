set -e #terminate on error

for module in cppContractVolumeInERC20 cppBalanceLastSeen
do
    g++ -O3 -Wall -shared -std=c++11 -lgmpxx -lgmp -fPIC `python3-config --includes` -I`pwd` ${module}.cpp -o build/${module}`python3-config --extension-suffix`
    echo "Build of ${module} successful!"
done