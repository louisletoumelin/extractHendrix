import sys
from .utils import NativeVariable

model = "ARPEGE"

vars = {'zs': dict(name='Geometrical height', shortName='h', parameterCategory=3, parameterNumber=6,
                   typeOfFirstFixedSurface=1, level=0, productDefinitionTemplateNumber=1),
        't2m': {'editionNumber': 2,
                'name': 'Temperature',
                'shortName': 't',
                'discipline': 0,
                'parameterCategory': 0,
                'parameterNumber': 0,
                'typeOfFirstFixedSurface': 1,
                'level': 0,
                'typeOfSecondFixedSurface': 255,
                'tablesVersion': 15,
                'productDefinitionTemplateNumber': 0}
        }

module = sys.modules[__name__]
for name, gribdict in vars.items():
    setattr(module, name,
            NativeVariable(model_name=model, name=gribdict, outname=name))
