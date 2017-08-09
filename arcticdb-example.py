from arctic import Arctic
store = Arctic('localhost')
library = store['test']
item = library.read('tick')
print(item.data)
