import sys
from extracthendrix.config.variables.utils import NativeVariable

"""
In this file you will find native variables names in ARPEGE_analysis_4dvar. 
If you need to implement a new variable, please give the native variable here.

Sometime, the name of a variable can change with time (ex: wind gust).
Here are alternative names (alternatives_names) to check if first name is not found

See Documentation in arome.py for more details.

29/06/2022: the variables have to be implemented.
"""

model = "ARPEGE_analysis_4dvar"

vars = {'zs': dict(name='Geometrical height', shortName='h', parameterCategory=3, parameterNumber=6,
                   typeOfFirstFixedSurface=1, level=0, productDefinitionTemplateNumber=1),
        # Warning: please verify if "t2m" correspond to this dictionary
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
for name, gribdict in vars.items():
    setattr(module, name,
            NativeVariable(model_name=model, name=gribdict, outname=name))
