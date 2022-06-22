import sys
from .utils import NativeVariable

model = "AROME"

vars = ['CLSTEMPERATURE', 'S090TEMPERATURE',
        'CLSVENT.ZONAL', 'CLSVENT.MERIDIEN', 'SURFTEMPERATURE']

module = sys.modules[__name__]
for name in vars:
    setattr(module, name.replace('.', '__'),
            NativeVariable(model_name=model, name=name))
