import sys
from extracthendrix.config.post_proc_functions_new import compute_temperature_in_degree_c, compute_wind_speed, copy, compute_decumul
from . import arpege_native as arpn
from .utils import Variable


vars = {
    'ZS': dict(native_vars=[arpn.zs], compute=None, original_long_name="Geometrical height"),
    'Tair':
        dict(native_vars=[arpn.t2m],
             compute=compute_temperature_in_degree_c,
             original_long_name="2 m Temperature",
             units="°C"
             )}

module = sys.modules[__name__]
for name in vars:
    setattr(module, name, Variable(**vars[name], name=name))
