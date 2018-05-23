import database_tools as db

def decodeDataframe(data, prop):
	if type(data.iloc[0][prop]) == str: #if the property values have been encoded, decode them
		data[prop] = data[prop].apply(lambda x: db.decodeObject(x))

	return data