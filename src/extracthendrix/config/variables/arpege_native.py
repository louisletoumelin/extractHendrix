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

"""
Sometime, the name of a variable can change with time (ex: wind gust).
Here are alternative names to check if first name is not found
"""

alternatives_names = {}

module = sys.modules[__name__]
for name in vars:
    alternative_names = alternatives_names.get(name)
    native_var = NativeVariable(model_name=model, name=name, alternative_names=alternative_names)
    setattr(module, name.replace('.', '__'), native_var)  # Replace '.' in names by '__'
