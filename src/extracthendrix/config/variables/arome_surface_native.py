import sys
from .utils import NativeVariable

model = 'AROME_SURFACE'

vars = ['X001WSN_VEG1']


module = sys.modules[__name__]
for name in vars:
    setattr(module, name, NativeVariable(model_name=model, name=name))
