import sys
from .utils import NativeVariable

model = "AROME"

vars = ['CLSTEMPERATURE', 'S090TEMPERATURE',
        'CLSVENT.ZONAL', 'CLSVENT.MERIDIEN', 'SURFTEMPERATURE']


"""
Sometime, the name of a variable can change with time (ex: wind gust).
Here are alternative names to check if first name is not found
"""

alternatives_names_fa = {'CLSU.RAF60M.XFU': ['CLSU.RAF.MOD.XFU'],
                         'CLSV.RAF60M.XFU': ['CLSV.RAF.MOD.XFU'],
                         'X001ASN_VEG1': ['X001ASN_VEG']}

module = sys.modules[__name__]
for name in vars:
    alternative_names = alternatives_names_fa.get(name)
    native_var = NativeVariable(model_name=model, name=name, alternative_names=alternative_names)
    setattr(module, name.replace('.', '__'), native_var)  # Replace '.' in names by '__'
