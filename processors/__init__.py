import inspect

from .util import state

from .properties import properties_imports
from .postprocessors import postprocessors_imports

propertyClasses = [x[1] for x in inspect.getmembers(properties_imports, inspect.isclass)]
propertyObjects = [clas() for clas in propertyClasses]

postprocessorClasses = [x[1] for x in inspect.getmembers(postprocessors_imports, inspect.isclass)]
postprocessorObjects = [clas() for clas in postprocessorClasses]
