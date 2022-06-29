import sys
from .utils import NativeVariable

"""
In this file you will find native variables names in ARPEGE. 
If you need to implement a new variable, please give the native variable here.

Sometime, the name of a variable can change with time (ex: wind gust).
Here are alternative names (alternatives_names) to check if first name is not found

See Documentation in arome.py for more details.

29/06/2022: the variables have to be implemented.
"""

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


alternatives_names = {}

module = sys.modules[__name__]
for name in vars:
    alternative_names = alternatives_names.get(name)
    native_var = NativeVariable(model_name=model, name=name, alternative_names=alternative_names)
    setattr(module, name.replace('.', '__'), native_var)  # Replace '.' in names by '__'
