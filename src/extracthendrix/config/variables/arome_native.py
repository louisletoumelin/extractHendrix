import sys
from .utils import NativeVariable

"""
In this file you will find native variables names in AROME. 
If you need to implement a new variable, please give the native variable here.

Sometime, the name of a variable can change with time (ex: wind gust).
Here are alternative names (alternatives_names_fa) to check if first name is not found

See Documentation in arome.py for more details.
"""

model = "AROME"

vars = ['CLSTEMPERATURE', 'S090TEMPERATURE', 'SURFTEMPERATURE', 'CLSMINI.TEMPERAT', 'CLSMAXI.TEMPERAT',
        'CLSVENT.ZONAL', 'CLSVENT.MERIDIEN', 'CLSU.RAF60M.XFU', 'CLSV.RAF60M.XFU',
        'CLSHUMI.SPECIFIQ', 'S090HUMI.SPECIFI', 'CLSHUMI.RELATIVE',
        'SURFPRESSION', 'SPECSURFGEOPOTEN', 'CLPMHAUT.MOD.XFU',
        'SURFACCPLUIE', 'SURFACCGRAUPEL', 'SURFACCNEIGE', 'SURFRAYT THER DE', 'SURFFLU.RAY.THER', 'SOMMFLU.RAY.THER',
        'SRAYT THER CL', 'SURFRAYT DIR SUR', 'SURFRAYT SOLA DE', 'SOMMFLU.RAY.SOLA', 'SURFFLU.RAY.SOLA',
        'SRAYT SOL CL', 'SURFFLU.LAT.MEVA', 'SURFFLU.LAT.MSUB', 'SURFFLU.CHA.SENS',
        'SURFNEBUL.TOTALE', 'SURFNEBUL.BASSE', 'SURFNEBUL.MOYENN', 'SURFNEBUL.HAUTE', 'ATMONEBUL.TOTALE',
        'ATMONEBUL.BASSE', 'ATMONEBUL.MOYENN', 'ATMONEBUL.HAUTE',
        'S090WIND.U.PHYS', 'S090WIND.V.PHYS', 'S087WIND.U.PHYS', 'S087WIND.V.PHYS',
        'S084WIND.U.PHYS', 'S084WIND.V.PHYS', 'S075WIND.U.PHYS', 'S075WIND.V.PHYS',
        'S090TKE', 'S087TKE', 'S084TKE', 'S075TKE',
        'S090TEMPERATURE', 'S087TEMPERATURE', 'S084TEMPERATURE', 'S075TEMPERATURE',
        'S090CLOUD_WATER', 'S090ICE_CRYSTAL', 'S090SNOW', 'S090RAIN',
        'S087CLOUD_WATER', 'S087ICE_CRYSTAL', 'S087SNOW', 'S087RAIN',
        'S084CLOUD_WATER', 'S084ICE_CRYSTAL', 'S084SNOW', 'S084RAIN',
        'S075CLOUD_WATER', 'S075ICE_CRYSTAL', 'S075SNOW', 'S075RAIN']


alternatives_names_fa = {'CLSU.RAF60M.XFU': ['CLSU.RAF.MOD.XFU'],
                         'CLSV.RAF60M.XFU': ['CLSV.RAF.MOD.XFU'],
                         'X001ASN_VEG1': ['X001ASN_VEG']}

module = sys.modules[__name__]
for name in vars:
    alternative_names = alternatives_names_fa.get(name)
    native_var = NativeVariable(model_name=model, name=name, alternative_names=alternative_names)
    name = name.replace('.', '__').replace(' ', '__')  # Replace '.' in names by '__' and ' ' by '__'
    setattr(module, name, native_var)
