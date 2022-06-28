import sys
from .utils import NativeVariable

model = "AROME_analysis"

vars = ['CLSTEMPERATURE']

module = sys.modules[__name__]
for name in vars:
    setattr(module, name.replace('.', '__'),
            NativeVariable(model_name=model, name=name))
