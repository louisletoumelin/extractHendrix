import sys
from extracthendrix.config.post_proc_functions_new import \
    compute_temperature_in_degree_c, \
    compute_wind_speed, \
    compute_wind_direction,\
    copy, \
    compute_decumul,\
    compute_decumul_and_diff, \
    compute_psurf, \
    compute_zs, \
    compute_snowfall, \
    compute_sum_all_water_species, \
    compute_latent_heat_flux, \
    compute_decumul_and_negative, \
    compute_multiply_by_100, \
    compute_t_r_p2qv
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
         ),

    'T1':
    dict(native_vars=[ann.S090TEMPERATURE],
         compute=compute_temperature_in_degree_c,
         original_long_name="Prognostic lowest level temperature"),

    'ts':
    dict(native_vars=[ann.SURFTEMPERATURE],
         compute=copy,
         original_long_name="Surface temperature. Ts (the one used in radiation)"),

    'Tmin':
        dict(fa_fields_required=[ann.CLSMINI_TEMPERAT],
             compute=compute_temperature_in_degree_c,
             original_long_name="T2m mini since last output file"),

    #
    # Temperature
    #

    'Tmin':
        dict(fa_fields_required=[ann.CLSMINI__TEMPERAT],
             compute=compute_temperature_in_degree_c,
             original_long_name="T2m mini since last output file"),
    'Tmax':
        dict(fa_fields_required=[ann.CLSMAXI__TEMPERAT],
             compute=compute_temperature_in_degree_c,
             original_long_name="T2m maxi since last output file"),

    #
    # Humidity
    #

    # todo 1/3: Isabelle used the prognostic humidity and stored it in Qair. Now prognostic humidity is Q1. We
    # 2/3: should create a function that put the values of Q1 inside Qair when the user desires
    # 3/3: prognostic humidity to force SURFEX
    'Qair':
        dict(fa_fields_required=[ann.CLSHUMI__SPECIFIQ],
             compute=copy,
             original_long_name="2m specific humidity"),

    'Q1':
        dict(fa_fields_required=[ann.S090HUMI__SPECIFI],
             compute=copy,
             original_long_name="Specific moisture"),

    'RH2m':
        dict(fa_fields_required=[ann.CLSHUMI__RELATIVE],
             compute=compute_multiply_by_100,
             original_long_name=" 	2m relative humidity"),

    #
    # Wind
    #

    'Wind':
        dict(fa_fields_required=[ann.CLSVENT__ZONAL, ann.CLSVENT__MERIDIEN],
             compute=compute_wind_speed,
             original_long_name="10 m wind speed"),

    'Wind_Gust':
    # Wind gust name has changed few years ago
        dict(fa_fields_required=[ann.CLSU__RAF60M__XFU, ann.CLSV__RAF60M__XFU],
             compute=compute_wind_speed,
             original_long_name="U and V 10m wind gusts (max since last file)"),

    'Wind_DIR':
        dict(fa_fields_required=[ann.CLSVENT__ZONAL, ann.CLSVENT__MERIDIEN],
             compute=compute_wind_direction),

    #
    # Pressure, elevation
    #

    'PSurf':
        dict(fa_fields_required=[ann.SURFPRESSION],
             compute=compute_psurf,
             original_long_name="Surface pressure"),

    'ZS':
        dict(fa_fields_required=[ann.SPECSURFGEOPOTEN],
             compute=compute_zs,
             original_long_name="Surface elevation. "
                                    "This variable is added once to the netcdf: during the first forecast term"),

    'BLH':
        dict(fa_fields_required=[ann.CLPMHAUT__MOD__XFU],
             compute=copy,
             original_long_name="Boudary Layer Height (m)"),

    #
    # Precipitations
    #

    'Rainf':
        dict(fa_fields_required=[ann.SURFACCPLUIE],
             compute=compute_decumul),

    'Grauf':
        dict(fa_fields_required=[ann.SURFACCGRAUPEL],
             compute=compute_decumul),

    'Snowf':
        dict(fa_fields_required=[ann.SURFACCNEIGE, ann.SURFACCGRAUPEL],
             compute=compute_snowfall,
             original_long_name="Snowfall = Cumulative snow + graupel"),

    #
    # Longwave
    #

    'LWdown':
        dict(fa_fields_required=[ann.SURFRAYT__THER__DE],
             compute=compute_decumul),
    'LWU':
        dict(fa_fields_required=[ann.SURFRAYT__THER__DE, ann.SURFFLU__RAY__THER],
             compute=compute_decumul_and_diff),

    'TOA_LWnet':
        dict(fa_fields_required=[ann.SOMMFLU__RAY__THER],
             compute=compute_decumul,
             original_long_name="Cum. net IR flux top of atm."),
    'LWnet':
        dict(fa_fields_required=[ann.SURFFLU__RAY__THER],
             compute=compute_decumul,
             original_long_name="Cum. net IR flux at surface"),

    'clear_sky_LWnet':
        dict(fa_fields_required=[ann.SRAYT__THER__CL],
             compute=copy,
             original_long_name="Net Clear sky surf thermal radiation"),

    #
    # Shortwave
    #

    'DIR_SWdown':
        dict(fa_fields_required=[ann.SURFRAYT__DIR__SUR],
             compute=compute_decumul),
    'SCA_SWdown':
        dict(fa_fields_required=[ann.SURFRAYT__SOLA__DE, ann.SURFRAYT__DIR__SUR],
             compute=compute_decumul_and_diff,
             original_long_name="SURFRAYT SOLA DE = Cum. Downward solar flux at surface"),

    'TOA_SWnet':
        dict(fa_fields_required=[ann.SOMMFLU__RAY__SOLA],
             compute=compute_decumul,
             original_long_name="Cum. net solar flux top of atm."),
    'SWnet':
        dict(fa_fields_required=[ann.SURFFLU__RAY__SOLA],
             compute=compute_decumul,
             original_long_name="Cum. net solar flux at surface"),
    'SWD':
        dict(fa_fields_required=[ann.SURFRAYT__SOLA__DE],
             compute=compute_decumul,
             original_long_name="Cum. Downward solarflux at surface"),

    'SWU':
        dict(fa_fields_required=[ann.SURFRAYT__SOLA__DE, ann.SURFFLU__RAY__SOLA],
             compute=compute_decumul_and_diff,
             original_long_name="Cum. Downward solarflux at surface"),

    'clear_sky_SWnet':
        dict(fa_fields_required=[ann.SRAYT__SOL__CL],
             compute=copy,
             original_long_name="Net Clear sky surf solar radiation"),

    #
    # Turbulent fluxes
    #

    'LHF':
        dict(fa_fields_required=[ann.SURFFLU__LAT__MEVA, ann.SURFFLU__LAT__MSUB],
             compute=compute_latent_heat_flux,
             original_long_name="LHF =SURFFLU.LAT.MEVA' + 'SURFFLU.LAT.MSUB'"),
    'SHF':
        dict(fa_fields_required=[ann.SURFFLU__CHA__SENS],
             compute=compute_decumul_and_negative,
             original_long_name="Cum.Sensible heat flux"),

    #
    # Clouds
    #

    'CC_inst':
        dict(fa_fields_required=[ann.SURFNEBUL__TOTALE],
             compute=copy,
             original_long_name="Inst. Total nebulosity"),
    'CC_inst_low':
        dict(fa_fields_required=[ann.SURFNEBUL__BASSE],
             compute=copy,
             original_long_name="Inst. Low nebulosity"),
    'CC_inst_middle':
        dict(fa_fields_required=[ann.SURFNEBUL__MOYENN],
             compute=copy,
             original_long_name="Inst. Middle nebulosity"),
    'CC_inst_high':
        dict(fa_fields_required=[ann.SURFNEBUL__HAUTE],
             compute=copy,
             original_long_name="Inst. High nebulosity"),

    'CC_cumul':
        dict(fa_fields_required=[ann.ATMONEBUL__TOTALE],
             compute=compute_decumul,
             original_long_name="Cum. total nebulosity"),
    'CC_cumul_low':
        dict(fa_fields_required=[ann.ATMONEBUL__BASSE],
             compute=compute_decumul,
             original_long_name="Cum. total nebulosity. Used by Seity."),
    'CC_cumul_middle':
        dict(fa_fields_required=[ann.ATMONEBUL__MOYENN],
             compute=compute_decumul,
             original_long_name="Cum. total nebulosity. Used by Seity."),
    'CC_cumul_high':
        dict(fa_fields_required=[ann.ATMONEBUL__HAUTE],
             compute=compute_decumul,
             original_long_name="Cum. total nebulosity. Used by Seity."),
    #
    # Variables by level
    #

    'Wind90':
        dict(fa_fields_required=[ann.S090WIND__U__PHYS, ann.S090WIND__V__PHYS],
             compute=compute_wind_speed,
             original_long_name="5 m wind speed"),

    'Wind87':
        dict(fa_fields_required=[ann.S087WIND__U__PHYS, ann.S087WIND__V__PHYS],
             compute=compute_wind_speed,
             original_long_name="50 m wind speed"),

    'Wind84':
        dict(fa_fields_required=[ann.S084WIND__U__PHYS, ann.S084WIND__V__PHYS],
             compute=compute_wind_speed,
             original_long_name="126 m wind speed"),

    'Wind75':
        dict(fa_fields_required=[ann.S075WIND__U__PHYS, ann.S075WIND__V__PHYS],
             compute=compute_wind_speed,
             original_long_name="515 m wind speed"),

    'TKE90':
        dict(fa_fields_required=[ann.S090TKE],
             compute=copy,
             original_long_name="5 m TKE"),

    'TKE87':
        dict(fa_fields_required=[ann.S087TKE],
             compute=copy,
             original_long_name="50 m TKE"),

    'TKE84':
        dict(fa_fields_required=[ann.S084TKE],
             compute=copy,
             original_long_name="126 m TKE"),

    'TKE75':
        dict(fa_fields_required=[ann.S075TKE],
             compute=copy,
             original_long_name="515 m TKE"),

    'TT90':
        dict(fa_fields_required=[ann.S090TEMPERATURE],
             compute=copy,
             original_long_name="5 m Temperature"),

    'TT87':
        dict(fa_fields_required=[ann.S087TEMPERATURE],
             compute=copy,
             original_long_name="50 m Temperature"),

    'TT84':
        dict(fa_fields_required=[ann.S084TEMPERATURE],
             compute=copy,
             original_long_name="126 m Temperature"),

    'TT75':
        dict(fa_fields_required=[ann.S075TEMPERATURE],
             compute=copy,
             original_long_name="515 m Temperature"),

    'water_content90':
        dict(fa_fields_required=[ann.S090CLOUD_WATER, ann.S090ICE_CRYSTAL, ann.S090SNOW, ann.S090RAIN],
             compute=compute_sum_all_water_species,
             original_long_name="5 m water content"
                                    "water content = Cloud dropplets + Ice crystals + Snow + Rain"),

    'water_content87':
        dict(fa_fields_required=[ann.S087CLOUD_WATER, ann.S087ICE_CRYSTAL, ann.S087SNOW, ann.S087RAIN],
             compute=compute_sum_all_water_species,
             original_long_name="50 m water content"),

    'water_content84':
        dict(fa_fields_required=[ann.S084CLOUD_WATER, ann.S084ICE_CRYSTAL, ann.S084SNOW, ann.S084RAIN],
             compute=compute_sum_all_water_species,
             original_long_name="126 m water content"),

    'water_content75':
        dict(fa_fields_required=[ann.S075CLOUD_WATER, ann.S075ICE_CRYSTAL, ann.S075SNOW, ann.S075RAIN],
             compute=compute_sum_all_water_species,
             original_long_name="515 m water content"),
}

module = sys.modules[__name__]
for name in vars:
    setattr(module, name, Variable(**vars[name], name=name))
