import sys
from extracthendrix.config.post_proc_functions_new import compute_temperature_in_degree_c, compute_wind_speed
from extracthendrix.config.variables import pearome_grib as pea
# from . import arome_surface_native as asn
from .utils import Variable

vars = {
    'Tair':
        dict(native_vars=[pea.t2m],
             compute=compute_temperature_in_degree_c,
             original_long_name="2 m Temperature"
             )

}

module = sys.modules[__name__]
for name in vars:
    setattr(module, name, Variable(**vars[name], name=name))