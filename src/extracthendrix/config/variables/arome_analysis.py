import sys
from extracthendrix.config.post_proc_functions_new import compute_temperature_in_degree_c, compute_wind_speed, copy, compute_decumul
from . import arome_analysis_native as ann
from .utils import Variable

"""
In this file you will find AROME analysis variables following the user configuration.

See Documentation in arome.py for more details.
"""

vars = {
    'Tair':
    dict(native_vars=[ann.CLSTEMPERATURE],
         compute=compute_temperature_in_degree_c,
         original_long_name="2 m Temperature"
         )
}


module = sys.modules[__name__]
for name in vars:
    setattr(module, name, Variable(**vars[name], name=name))
