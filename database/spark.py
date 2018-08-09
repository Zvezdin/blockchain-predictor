from datetime import datetime as dt

from pyspark import SparkContext, SparkConf

conf = SparkConf().setAppName("appName").setMaster("local")
sc = SparkContext(conf=conf)

df = sc.createDataFrame([{'a': 10, 'date': dt(2017,1,1)}, {'a': 23, 'date': dt(2018,1,1,1)}])

print(df.show())

