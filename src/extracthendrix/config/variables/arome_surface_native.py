import sys
from .utils import NativeVariable

model = 'AROME_SURFACE'

vars = ['X001WSN_VEG1']

alternatives_names_fa = {'X001ASN_VEG1': ['X001ASN_VEG']}

"""
Sometime, the name of a variable can change with time (ex: wind gust).
Here are alternative names to check if first name is not found
"""

module = sys.modules[__name__]
for name in vars:
    alternative_names = alternatives_names_fa.get(name)
    native_var = NativeVariable(model_name=model, name=name, alternative_names=alternative_names)
    setattr(module, name.replace('.', '__'), native_var)  # Replace '.' in names by '__'
