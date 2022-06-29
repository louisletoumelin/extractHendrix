import sys
from .utils import NativeVariable

"""
In this file you will find native variables names in AROME. 
If you need to implement a new variable, please give the native variable here.

See Documentation in arome.py for more details.
"""

model = "AROME_analysis"

vars = ['CLSTEMPERATURE']

module = sys.modules[__name__]
for name in vars:
    setattr(module, name.replace('.', '__'),
            NativeVariable(model_name=model, name=name))
