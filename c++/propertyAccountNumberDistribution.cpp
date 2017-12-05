accMap accounts;

result createDistribution(int lastTimestamp){
	result res = {}; //will init whole array to 0.

	const double smax0 = SCALE(static_cast<float>(max0) * SCALE_MUL), smax1 = SCALE(static_cast<float>(max1) * SCALE_MUL); //pre-scale our maximum values

	for (auto const &it : accounts){
		int arg0, arg1;

		if(it.second[0] <= 1){ //don't want log of 0
			if(minCutoff0) continue;
			arg0 = 0;
		} else if(it.second[0] >= max0){ //compare to the unscaled max
			if(maxCutoff0) continue;
			arg0 = group0-1;
		} else{
			arg0 = std::min(static_cast<int>(((SCALE(static_cast<castFloat>(it.second[0]) * SCALE_MUL ) ) / smax0) * group0), group0-1);
		}

		featType val = std::abs(it.second[1] - lastTimestamp);
		
		if(val >= max1){
			if(maxCutoff1) continue;
			arg1 = group1-1;
		} else if (val <= 1){
			if(minCutoff1) continue;
			arg1 = 0;
		} else {
			arg1 = std::min(static_cast<int>(((SCALE(static_cast<castFloat>(val) * SCALE_MUL ) ) / smax1) * group1), group1-1);
		}
		//std::cout<<arg0<<arg1<<std::endl;
		//std::cout<<(it.second[1] - lastTimestamp)<<((it.second[1] - lastTimestamp) / smax1)<<(((it.second[1] - lastTimestamp) / smax1) * group1)<<std::endl;

		res[arg0][arg1] ++;
	}

	return res;
}

result pythonDistribution(int lastTimestamp){
	return createDistribution(lastTimestamp);
}

void fakeData(){
	acc account = {"0xb794f5ea0ba39494ce839613fffba74279579268"};
	
	for(int i=0; i<10000000; i++){
		int num = i;
		for(int j=20; num>0; j++){
			account[j] = 48 + num % 10;
			num /= 10;
		}

		accounts[account] = {i,i};
	}

    std::cout<<"Length of resulting fake data is "<<accounts.size()<<std::endl;
}

acc transformKey(const char* rawKey){
	acc key = {0};

	std::copy(rawKey, rawKey+accLen, std::begin(key));

	return key;
}

acc transformKey(std::string rawKey){
	acc key = {0};

	const char* cstr = rawKey.c_str();
	std::copy(cstr, cstr+accLen, std::begin(key));

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
    fakeData();

    std::cout<<"length of fake data is "<<getLen()<<std::endl;

	auto start = std::chrono::high_resolution_clock::now();

	auto res = createDistribution(1000);

	auto end = std::chrono::high_resolution_clock::now();

	std::chrono::duration<double> elapsed = end - start;

	std::cout << "Elapsed time: " << elapsed.count() << " s\n";

    int sum = 0;

    for(int i=0; i<group0; i++){
        for(int j=0; j<group1; j++){
            sum += res[i][j];
        }
    }

    if(sum != getLen()){
        std::cout<<"Error- did not distribute all accounts!"<<std::endl;
    }
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

		//boost::multiprecision::SCALE(static_cast<largeFloat>(a));

		a.str();
	}
}

PYBIND11_MODULE(MODULE_NAME, m) {
	m.doc() = "pybind11 bindings of a c++ implementation of an account number distribution";
	
	m.def("setInt", &setItemInt, "");
	m.def("setStr", &setItemStr, "");
	m.def("getInt", &getItemInt, "");
	m.def("getStr", &getItemStr, "");
	m.def("len", &getLen, "");
	m.def("test", &test, "");
	m.def("test4", &test4, "");
	m.def("createDistribution", &pythonDistribution, "");
}
