import sys
from extracthendrix.config.post_proc_functions_new import \
    compute_temperature_in_degree_c, \
    compute_wind_speed, \
    compute_wind_direction,\
    copy, \
    compute_psurf, \
    compute_zs, \
    compute_sum_all_water_species, \
    compute_multiply_by_100, \
    compute_sum
from .native import arome_analysis_p0_native as ann
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
         ),

    'T1':
    dict(native_vars=[ann.S090TEMPERATURE],
         compute=compute_temperature_in_degree_c,
         original_long_name="Prognostic lowest level temperature"),

    'ts':
    dict(native_vars=[ann.SURFTEMPERATURE],
         compute=copy,
         original_long_name="Surface temperature. Ts (the one used in radiation)"),

    #
    # Temperature
    #

    'Tmin':
        dict(native_vars=[ann.CLSMINI__TEMPERAT],
             compute=compute_temperature_in_degree_c,
             original_long_name="T2m mini since last output file"),
    'Tmax':
        dict(native_vars=[ann.CLSMAXI__TEMPERAT],
             compute=compute_temperature_in_degree_c,
             original_long_name="T2m maxi since last output file"),

    #
    # Humidity
    #

    # todo 1/3: Isabelle used the prognostic humidity and stored it in Qair. Now prognostic humidity is Q1. We
    # 2/3: should create a function that put the values of Q1 inside Qair when the user desires
    # 3/3: prognostic humidity to force SURFEX
    'Qair':
        dict(native_vars=[ann.CLSHUMI__SPECIFIQ],
             compute=copy,
             original_long_name="2m specific humidity"),

    'Q1':
        dict(native_vars=[ann.S090HUMI__SPECIFI],
             compute=copy,
             original_long_name="Specific moisture"),

    'RH2m':
        dict(native_vars=[ann.CLSHUMI__RELATIVE],
             compute=compute_multiply_by_100,
             original_long_name=" 	2m relative humidity"),

    #
    # Wind
    #

    'Wind':
        dict(native_vars=[ann.CLSVENT__ZONAL, ann.CLSVENT__MERIDIEN],
             compute=compute_wind_speed,
             original_long_name="10 m wind speed"),

    'Wind_Gust':
    # Wind gust name has changed few years ago
        dict(native_vars=[ann.CLSU__RAF60M__XFU, ann.CLSV__RAF60M__XFU],
             compute=compute_wind_speed,
             original_long_name="U and V 10m wind gusts (max since last file)"),

    'Wind_DIR':
        dict(native_vars=[ann.CLSVENT__ZONAL, ann.CLSVENT__MERIDIEN],
             compute=compute_wind_direction),

    #
    # Pressure, elevation
    #

    'PSurf':
        dict(native_vars=[ann.SURFPRESSION],
             compute=compute_psurf,
             original_long_name="Surface pressure"),

    'ZS':
        dict(native_vars=[ann.SPECSURFGEOPOTEN],
             compute=compute_zs,
             original_long_name="Surface elevation. "
                                    "This variable is added once to the netcdf: during the first forecast term"),

    'BLH':
        dict(native_vars=[ann.CLPMHAUT__MOD__XFU],
             compute=copy,
             original_long_name="Boudary Layer Height (m)"),

    #
    # Precipitations
    #

    #
    # Warning: no decumul for P0
    #

    'Rainf':
        dict(native_vars=[ann.SURFINSPLUIE],
             compute=copy),

    'Grauf':
        dict(native_vars=[ann.SURFINSGRAUPEL],
             compute=copy),

    'Snowf':
        dict(native_vars=[ann.SURFINSNEIGE, ann.SURFINSGRAUPEL],
             compute=compute_sum,
             original_long_name="Snowfall = Cumulative snow + graupel"),

    #
    # Clouds
    #

    'CC_inst':
        dict(native_vars=[ann.SURFNEBUL__TOTALE],
             compute=copy,
             original_long_name="Inst. Total nebulosity"),
    'CC_inst_low':
        dict(native_vars=[ann.SURFNEBUL__BASSE],
             compute=copy,
             original_long_name="Inst. Low nebulosity"),
    'CC_inst_middle':
        dict(native_vars=[ann.SURFNEBUL__MOYENN],
             compute=copy,
             original_long_name="Inst. Middle nebulosity"),
    'CC_inst_high':
        dict(native_vars=[ann.SURFNEBUL__HAUTE],
             compute=copy,
             original_long_name="Inst. High nebulosity"),
    #
    # Variables by level
    #

    'Wind90':
        dict(native_vars=[ann.S090WIND__U__PHYS, ann.S090WIND__V__PHYS],
             compute=compute_wind_speed,
             original_long_name="5 m wind speed"),

    'Wind87':
        dict(native_vars=[ann.S087WIND__U__PHYS, ann.S087WIND__V__PHYS],
             compute=compute_wind_speed,
             original_long_name="50 m wind speed"),

    'Wind84':
        dict(native_vars=[ann.S084WIND__U__PHYS, ann.S084WIND__V__PHYS],
             compute=compute_wind_speed,
             original_long_name="126 m wind speed"),

    'Wind75':
        dict(native_vars=[ann.S075WIND__U__PHYS, ann.S075WIND__V__PHYS],
             compute=compute_wind_speed,
             original_long_name="515 m wind speed"),

    'TKE90':
        dict(native_vars=[ann.S090TKE],
             compute=copy,
             original_long_name="5 m TKE"),

    'TKE87':
        dict(native_vars=[ann.S087TKE],
             compute=copy,
             original_long_name="50 m TKE"),

    'TKE84':
        dict(native_vars=[ann.S084TKE],
             compute=copy,
             original_long_name="126 m TKE"),

    'TKE75':
        dict(native_vars=[ann.S075TKE],
             compute=copy,
             original_long_name="515 m TKE"),

    'TT90':
        dict(native_vars=[ann.S090TEMPERATURE],
             compute=copy,
             original_long_name="5 m Temperature"),

    'TT87':
        dict(native_vars=[ann.S087TEMPERATURE],
             compute=copy,
             original_long_name="50 m Temperature"),

    'TT84':
        dict(native_vars=[ann.S084TEMPERATURE],
             compute=copy,
             original_long_name="126 m Temperature"),

    'TT75':
        dict(native_vars=[ann.S075TEMPERATURE],
             compute=copy,
             original_long_name="515 m Temperature"),

    'water_content90':
        dict(native_vars=[ann.S090CLOUD_WATER, ann.S090ICE_CRYSTAL, ann.S090SNOW, ann.S090RAIN],
             compute=compute_sum_all_water_species,
             original_long_name="5 m water content"
                                    "water content = Cloud dropplets + Ice crystals + Snow + Rain"),

    'water_content87':
        dict(native_vars=[ann.S087CLOUD_WATER, ann.S087ICE_CRYSTAL, ann.S087SNOW, ann.S087RAIN],
             compute=compute_sum_all_water_species,
             original_long_name="50 m water content"),

    'water_content84':
        dict(native_vars=[ann.S084CLOUD_WATER, ann.S084ICE_CRYSTAL, ann.S084SNOW, ann.S084RAIN],
             compute=compute_sum_all_water_species,
             original_long_name="126 m water content"),

    'water_content75':
        dict(native_vars=[ann.S075CLOUD_WATER, ann.S075ICE_CRYSTAL, ann.S075SNOW, ann.S075RAIN],
             compute=compute_sum_all_water_species,
             original_long_name="515 m water content"),
}

module = sys.modules[__name__]
for name in vars:
    setattr(module, name, Variable(**vars[name], name=name))
setattr(module, "vars", vars)
