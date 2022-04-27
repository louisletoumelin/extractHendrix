import sys
from .utils import NativeVariable

model = "PEAROME"

vars = {'t2m': dict(shortName='2t', productDefinitionTemplateNumber=1),
        'u10m': dict(shortName='10u'),
        'v10m': dict(shortName='10v')}

module = sys.modules[__name__]
for name, gribdict in vars.items():
    setattr(module, name,
            NativeVariable(model_name=model, name=gribdict))
