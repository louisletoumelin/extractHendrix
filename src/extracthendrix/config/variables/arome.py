import sys
from extracthendrix.config.post_proc_functions_new import compute_temperature_in_degree_c, compute_wind_speed, copy, compute_decumul
from . import arome_native as an
from . import arome_surface_native as asn
from .utils import Variable


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
