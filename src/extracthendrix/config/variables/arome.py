import sys
from extracthendrix.config.post_proc_functions_new import compute_temperature_in_degree_c, compute_wind_speed, copy, compute_decumul
from . import arome_native as an
from . import arome_surface_native as asn
from .utils import Variable

"""
In this file you will find AROME variables following the user configuration.

For example, in AROME there is no "wind speed", bt only speed for each of the component wind vector.

Given thoses components we can compute wind speed as a post-processing step. 
If the user ask "Wind", the code will compute wind speed using AROME components. 

So we need to link what the user asks ("Wind") to the variables in AROME outputs ('CLSVENT.ZONAL', 'CLSVENT.MERIDIEN').
"""

vars = {
    'Tair':
    dict(native_vars=[an.CLSTEMPERATURE],
         compute=compute_temperature_in_degree_c,
         original_long_name="2 m Temperature"
         ),

    'T1':
    dict(native_vars=[an.S090TEMPERATURE],
         compute=compute_temperature_in_degree_c,
         original_long_name="Prognostic lowest level temperature"),

    'ts':
    dict(native_vars=[an.SURFTEMPERATURE],
         compute=copy,
         original_long_name="Surface temperature. Ts (the one used in radiation)"),

    'SWE':
    dict(native_vars=[asn.X001WSN_VEG1],
         compute=compute_decumul,
         original_long_name="contenu équivalent en eau de la neige [km m-2]")
}


module = sys.modules[__name__]
for name in vars:
    setattr(module, name, Variable(**vars[name], name=name))
