import sys
from extracthendrix.config.post_proc_functions_new import compute_temperature_in_degree_c, compute_wind_speed, \
    compute_t_r_p2qv, compute_wind_direction, sum_solid_prec, percent2fraction, joule2watt_hourly
from extracthendrix.config.variables import pearome_grib as pea
# from . import arome_surface_native as asn
from .utils import Variable

"""
In this file you will find PEAROME variables following the user configuration.

See Documentation in arome.py for more details.
"""

vars = {
    'Psurf': dict(native_vars=[pea.pres0m], compute=None, original_long_name="Surface pressure"),
    'ZS': dict(native_vars=[pea.zs], compute=None, original_long_name="Geometrical height"),
    'Tair':
        dict(native_vars=[pea.t2m],
             compute=compute_temperature_in_degree_c,
             original_long_name="2 m Temperature",
             units="°C"
             ),
    'Qair': dict(native_vars=[pea.t2m, pea.r2m, pea.pres0m], compute=compute_t_r_p2qv,
                 original_long_name="Near Surface Specific Humidity", units="kg/kg"),
    'Wind': dict(native_vars=[pea.u10m, pea.v10m], compute=compute_wind_speed,
                 original_long_name="10m wind speed", units="m/s"),
    'Wind_DIR': dict(native_vars=[pea.u10m, pea.v10m], compute=compute_wind_direction,
                 original_long_name="10m wind direction", units="degrees"),
    'Rainf': dict(native_vars=[pea.rprate], compute=None, original_long_name="Rain precipitation rate",
                  units="kg/m2/s"),
    'Snowf': dict(native_vars=[pea.sprate, pea.gprate, pea.hailrate], compute=sum_solid_prec,
                  original_long_name="Solid precipitation rate", units="kg/m2/s"),
    'LWdown': dict(native_vars=[pea.strd], compute=joule2watt_hourly,
                   original_long_name="Surface Incident Longwave Radiation", units="W/m2"),
    'SWdown': dict(native_vars=[pea.ssrd], compute=joule2watt_hourly,
                   original_long_name="Surface Incident Shortwave Radiation", units="W/m2"),
    'tcc': dict(native_vars=[pea.tcc0m], compute=None, original_long_name="Total Cloud Cover", units="%"),
    'NEB': dict(native_vars=[pea.tcc0m], compute=percent2fraction,
                original_long_name="Total Cloud Cover fraction", units="between 0 and 1"),
    'HUMREL': dict(native_vars=[pea.r2m], compute=None, original_long_name="Relative humidity", units="%"),
    'isoZeroAltitude': dict(native_vars=[pea.isoT27315cK], compute=None,
                            original_long_name="freezing level altitude", units="m"),
    'isowetbt0': dict(native_vars=[pea.isowetbt27315cK], compute=None,
                      original_long_name="level of 0 deg wet bulb temperature", units="m"),
    'isowetbt1': dict(native_vars=[pea.isowetbt27415cK], compute=None,
                      original_long_name="level of 1 deg wet bulb temperature", units="m"),
    'isowetbt1_5': dict(native_vars=[pea.isowetbt27465cK], compute=None,
                      original_long_name="level of 1.5 deg wet bulb temperature", units="m"),
}

module = sys.modules[__name__]
for name in vars:
    setattr(module, name, Variable(**vars[name], name=name))