import sys
from extracthendrix.config.variables.utils import NativeVariable

"""
In this file you will find native variables names in AROME. 
If you need to implement a new variable, please give the native variable here.

See Documentation in arome.py for more details.
"""

model = "AROME_analysis_p0"

vars = ['CLSTEMPERATURE', 'S090TEMPERATURE', 'SURFTEMPERATURE', 'CLSMINI.TEMPERAT', 'CLSMAXI.TEMPERAT',
        'CLSVENT.ZONAL', 'CLSVENT.MERIDIEN', 'CLSU.RAF60M.XFU', 'CLSV.RAF60M.XFU', 'CLSHUMI.SPECIFIQ',
        'S090HUMI.SPECIFI', 'CLSHUMI.RELATIVE', 'SURFPRESSION', 'SPECSURFGEOPOTEN', 'CLPMHAUT.MOD.XFU',
        'SURFACCGRAUPEL', 'SURFRAYT THER DE', 'SOMMFLU.RAY.THER', 'SURFRAYT DIR SUR', 'SOMMFLU.RAY.SOLA',
        'SRAYT SOL CL', 'SURFFLU.LAT.MSUB', 'SURFNEBUL.TOTALE', 'SURFNEBUL.BASSE', 'SURFNEBUL.MOYENN',
        'SURFNEBUL.HAUTE', 'ATMONEBUL.BASSE', 'ATMONEBUL.HAUTE', 'S090WIND.U.PHYS', 'S090WIND.V.PHYS',
        'S087WIND.U.PHYS', 'S087WIND.V.PHYS', 'S084WIND.U.PHYS', 'S084WIND.V.PHYS', 'S075WIND.U.PHYS',
        'S075WIND.V.PHYS', 'S090TKE', 'S087TKE', 'S084TKE', 'S075TKE', 'S090TEMPERATURE', 'S087TEMPERATURE',
        'S084TEMPERATURE', 'S075TEMPERATURE', 'S090CLOUD_WATER', 'S090ICE_CRYSTAL', 'S090SNOW', 'S090RAIN',
        'S087CLOUD_WATER', 'S087ICE_CRYSTAL', 'S087SNOW', 'S087RAIN', 'S084CLOUD_WATER', 'S084ICE_CRYSTAL',
        'S084SNOW', 'S084RAIN', 'S075CLOUD_WATER', 'S075ICE_CRYSTAL', 'S075SNOW', 'S075RAIN', 'SURFINSPLUIE',
        'SURFINSNEIGE', 'SURFINSGRAUPEL']

module = sys.modules[__name__]
for name in vars:
    setattr(module, name.replace('.', '__').replace(' ', '__'),
            NativeVariable(model_name=model, name=name))
