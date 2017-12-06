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

void clearState(){
	accounts.clear();
}

void clearIndex(int index){
	for (auto const &it : accounts){
		accounts[it.first][index] = 0;
	}
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

PYBIND11_MODULE(MODULE_NAME, m) {
	m.doc() = "pybind11 bindings of a c++ implementation of an account number distribution";
	
	m.def("setInt", &setItemInt, "");
	m.def("setStr", &setItemStr, "");
	m.def("getInt", &getItemInt, "");
	m.def("getStr", &getItemStr, "");
	m.def("len", &getLen, "");
	m.def("test", &test, "");
	m.def("clear", &clearState, "");
	m.def("createDistribution", &pythonDistribution, "");
}
