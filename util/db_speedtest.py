import numpy as np
import pandas as pd
from time import time
from datetime import datetime as dt

from ..database import instance as db

def f(start, end, key):
    t = time()

    q = "index >= '%s' and index <= '%s'" % (str(start), str(end))
    print(q)
    res=st.select(key, where=q, iterator=True)
    for x in res:
        print(x.head())
    print("Reading of %s (q=%s) took %d" % (key, q, time()-t))

db.open()

st = db.store

f(dt(1980,1,1), dt(2040,1,1), 'test')

db.close()