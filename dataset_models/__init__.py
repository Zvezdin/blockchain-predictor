import inspect

from .models import model_imports

modelClasses = [x[1] for x in inspect.getmembers(model_imports, inspect.isclass)]
modelObjects = [clas() for clas in modelClasses]