import sys
from .utils import NativeVariable

"""
In this file you will find native variables names in AROME surface (SURFEX). 
If you need to implement a new variable, please give the native variable here.

Sometime, the name of a variable can change with time (ex: wind gust).
Here are alternative names (alternatives_names_fa) to check if first name is not found

See Documentation in arome.py for more details.
"""

model = 'AROME_SURFACE'

vars = ['X001WSN_VEG1']


alternatives_names_fa = {'X001ASN_VEG1': ['X001ASN_VEG']}

module = sys.modules[__name__]
for name in vars:
    alternative_names = alternatives_names_fa.get(name)
    native_var = NativeVariable(model_name=model, name=name, alternative_names=alternative_names)
    setattr(module, name.replace('.', '__'), native_var)  # Replace '.' in names by '__'
