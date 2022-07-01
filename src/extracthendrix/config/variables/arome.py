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

    'Tmin':
        dict(fa_fields_required=[an.CLSMINI_TEMPERAT],
             compute=compute_temperature_in_degree_c,
             original_long_name="T2m mini since last output file"),

    #
    # Temperature
    #

    'Tmin':
        dict(fa_fields_required=[an.CLSMINI__TEMPERAT],
             compute=compute_temperature_in_degree_c,
             original_long_name="T2m mini since last output file"),
    'Tmax':
        dict(fa_fields_required=[an.CLSMAXI__TEMPERAT],
             compute=compute_temperature_in_degree_c,
             original_long_name="T2m maxi since last output file"),

    #
    # Humidity
    #

    # todo 1/3: Isabelle used the prognostic humidity and stored it in Qair. Now prognostic humidity is Q1. We
    # 2/3: should create a function that put the values of Q1 inside Qair when the user desires
    # 3/3: prognostic humidity to force SURFEX
    'Qair':
        dict(fa_fields_required=[an.CLSHUMI__SPECIFIQ],
             compute=copy,
             original_long_name="2m specific humidity"),

    'Q1':
        dict(fa_fields_required=[an.S090HUMI__SPECIFI],
             compute=copy,
             original_long_name="Specific moisture"),

    'RH2m':
        dict(fa_fields_required=[an.CLSHUMI__RELATIVE],
             compute=compute_multiply_by_100,
             original_long_name=" 	2m relative humidity"),

    #
    # Wind
    #

    'Wind':
        dict(fa_fields_required=[an.CLSVENT__ZONAL, an.CLSVENT__MERIDIEN],
             compute=compute_wind_speed,
             original_long_name="10 m wind speed"),

    'Wind_Gust':
    # Wind gust name has changed few years ago
        dict(fa_fields_required=[an.CLSU__RAF60M__XFU, an.CLSV__RAF60M__XFU],
             compute=compute_wind_speed,
             original_long_name="U and V 10m wind gusts (max since last file)"),

    'Wind_DIR':
        dict(fa_fields_required=[an.CLSVENT__ZONAL, an.CLSVENT__MERIDIEN],
             compute=compute_wind_direction),

    #
    # Pressure, elevation
    #

    'PSurf':
        dict(fa_fields_required=[an.SURFPRESSION],
             compute=compute_psurf,
             original_long_name="Surface pressure"),

    'ZS':
        dict(fa_fields_required=[an.SPECSURFGEOPOTEN],
             compute=compute_zs,
             original_long_name="Surface elevation. "
                                    "This variable is added once to the netcdf: during the first forecast term"),

    'BLH':
        dict(fa_fields_required=[an.CLPMHAUT__MOD__XFU],
             compute=copy,
             original_long_name="Boudary Layer Height (m)"),

    #
    # Precipitations
    #

    'Rainf':
        dict(fa_fields_required=[an.SURFACCPLUIE],
             compute=compute_decumul),

    'Grauf':
        dict(fa_fields_required=[an.SURFACCGRAUPEL],
             compute=compute_decumul),

    'Snowf':
        dict(fa_fields_required=[an.SURFACCNEIGE, an.SURFACCGRAUPEL],
             compute=compute_snowfall,
             original_long_name="Snowfall = Cumulative snow + graupel"),

    #
    # Longwave
    #

    'LWdown':
        dict(fa_fields_required=[an.SURFRAYT__THER__DE],
             compute=compute_decumul),
    'LWU':
        dict(fa_fields_required=[an.SURFRAYT__THER__DE, an.SURFFLU__RAY__THER],
             compute=compute_decumul_and_diff),

    'TOA_LWnet':
        dict(fa_fields_required=[an.SOMMFLU__RAY__THER],
             compute=compute_decumul,
             original_long_name="Cum. net IR flux top of atm."),
    'LWnet':
        dict(fa_fields_required=[an.SURFFLU__RAY__THER],
             compute=compute_decumul,
             original_long_name="Cum. net IR flux at surface"),

    'clear_sky_LWnet':
        dict(fa_fields_required=[an.SRAYT__THER__CL],
             compute=copy,
             original_long_name="Net Clear sky surf thermal radiation"),

    #
    # Shortwave
    #

    'DIR_SWdown':
        dict(fa_fields_required=[an.SURFRAYT__DIR__SUR],
             compute=compute_decumul),
    'SCA_SWdown':
        dict(fa_fields_required=[an.SURFRAYT__SOLA__DE, an.SURFRAYT__DIR__SUR],
             compute=compute_decumul_and_diff,
             original_long_name="SURFRAYT SOLA DE = Cum. Downward solar flux at surface"),

    'TOA_SWnet':
        dict(fa_fields_required=[an.SOMMFLU__RAY__SOLA],
             compute=compute_decumul,
             original_long_name="Cum. net solar flux top of atm."),
    'SWnet':
        dict(fa_fields_required=[an.SURFFLU__RAY__SOLA],
             compute=compute_decumul,
             original_long_name="Cum. net solar flux at surface"),
    'SWD':
        dict(fa_fields_required=[an.SURFRAYT__SOLA__DE],
             compute=compute_decumul,
             original_long_name="Cum. Downward solarflux at surface"),

    'SWU':
        dict(fa_fields_required=[an.SURFRAYT__SOLA__DE, an.SURFFLU__RAY__SOLA],
             compute=compute_decumul_and_diff,
             original_long_name="Cum. Downward solarflux at surface"),

    'clear_sky_SWnet':
        dict(fa_fields_required=[an.SRAYT__SOL__CL],
             compute=copy,
             original_long_name="Net Clear sky surf solar radiation"),

    #
    # Turbulent fluxes
    #

    'LHF':
        dict(fa_fields_required=[an.SURFFLU__LAT__MEVA, an.SURFFLU__LAT__MSUB],
             compute=compute_latent_heat_flux,
             original_long_name="LHF =SURFFLU.LAT.MEVA' + 'SURFFLU.LAT.MSUB'"),
    'SHF':
        dict(fa_fields_required=[an.SURFFLU__CHA__SENS],
             compute=compute_decumul_and_negative,
             original_long_name="Cum.Sensible heat flux"),

    #
    # Clouds
    #

    'CC_inst':
        dict(fa_fields_required=[an.SURFNEBUL__TOTALE],
             compute=copy,
             original_long_name="Inst. Total nebulosity"),
    'CC_inst_low':
        dict(fa_fields_required=[an.SURFNEBUL__BASSE],
             compute=copy,
             original_long_name="Inst. Low nebulosity"),
    'CC_inst_middle':
        dict(fa_fields_required=[an.SURFNEBUL__MOYENN],
             compute=copy,
             original_long_name="Inst. Middle nebulosity"),
    'CC_inst_high':
        dict(fa_fields_required=[an.SURFNEBUL__HAUTE],
             compute=copy,
             original_long_name="Inst. High nebulosity"),

    'CC_cumul':
        dict(fa_fields_required=[an.ATMONEBUL__TOTALE],
             compute=compute_decumul,
             original_long_name="Cum. total nebulosity"),
    'CC_cumul_low':
        dict(fa_fields_required=[an.ATMONEBUL__BASSE],
             compute=compute_decumul,
             original_long_name="Cum. total nebulosity. Used by Seity."),
    'CC_cumul_middle':
        dict(fa_fields_required=[an.ATMONEBUL__MOYENN],
             compute=compute_decumul,
             original_long_name="Cum. total nebulosity. Used by Seity."),
    'CC_cumul_high':
        dict(fa_fields_required=[an.ATMONEBUL__HAUTE],
             compute=compute_decumul,
             original_long_name="Cum. total nebulosity. Used by Seity."),
    #
    # Variables by level
    #

    'Wind90':
        dict(fa_fields_required=[an.S090WIND__U__PHYS, an.S090WIND__V__PHYS],
             compute=compute_wind_speed,
             original_long_name="5 m wind speed"),

    'Wind87':
        dict(fa_fields_required=[an.S087WIND__U__PHYS, an.S087WIND__V__PHYS],
             compute=compute_wind_speed,
             original_long_name="50 m wind speed"),

    'Wind84':
        dict(fa_fields_required=[an.S084WIND__U__PHYS, an.S084WIND__V__PHYS],
             compute=compute_wind_speed,
             original_long_name="126 m wind speed"),

    'Wind75':
        dict(fa_fields_required=[an.S075WIND__U__PHYS, an.S075WIND__V__PHYS],
             compute=compute_wind_speed,
             original_long_name="515 m wind speed"),

    'TKE90':
        dict(fa_fields_required=[an.S090TKE],
             compute=copy,
             original_long_name="5 m TKE"),

    'TKE87':
        dict(fa_fields_required=[an.S087TKE],
             compute=copy,
             original_long_name="50 m TKE"),

    'TKE84':
        dict(fa_fields_required=[an.S084TKE],
             compute=copy,
             original_long_name="126 m TKE"),

    'TKE75':
        dict(fa_fields_required=[an.S075TKE],
             compute=copy,
             original_long_name="515 m TKE"),

    'TT90':
        dict(fa_fields_required=[an.S090TEMPERATURE],
             compute=copy,
             original_long_name="5 m Temperature"),

    'TT87':
        dict(fa_fields_required=[an.S087TEMPERATURE],
             compute=copy,
             original_long_name="50 m Temperature"),

    'TT84':
        dict(fa_fields_required=[an.S084TEMPERATURE],
             compute=copy,
             original_long_name="126 m Temperature"),

    'TT75':
        dict(fa_fields_required=[an.S075TEMPERATURE],
             compute=copy,
             original_long_name="515 m Temperature"),

    'water_content90':
        dict(fa_fields_required=[an.S090CLOUD_WATER, an.S090ICE_CRYSTAL, an.S090SNOW, an.S090RAIN],
             compute=compute_sum_all_water_species,
             original_long_name="5 m water content"
                                    "water content = Cloud dropplets + Ice crystals + Snow + Rain"),

    'water_content87':
        dict(fa_fields_required=[an.S087CLOUD_WATER, an.S087ICE_CRYSTAL, an.S087SNOW, an.S087RAIN],
             compute=compute_sum_all_water_species,
             original_long_name="50 m water content"),

    'water_content84':
        dict(fa_fields_required=[an.S084CLOUD_WATER, an.S084ICE_CRYSTAL, an.S084SNOW, an.S084RAIN],
             compute=compute_sum_all_water_species,
             original_long_name="126 m water content"),

    'water_content75':
        dict(fa_fields_required=[an.S075CLOUD_WATER, an.S075ICE_CRYSTAL, an.S075SNOW, an.S075RAIN],
             compute=compute_sum_all_water_species,
             original_long_name="515 m water content"),

    #
    # Surface variables
    #

    'SWE':
        dict(fa_fields_required=[asn.X001WSN_VEG1],
             compute=copy,
             original_long_name="contenu équivalent en eau de la neige [km m-2]"),

    'snow_density':
        dict(fa_fields_required=[asn.X001RSN_VEG1],
             compute=copy,
             original_long_name="densité de la neige [km m-3]"),

    'snow_albedo':
        dict(fa_fields_required=[asn.X001ASN_VEG1],
             compute=copy,
             original_long_name="albédo de la neige"),

    'vegetation_fraction':
        dict(fa_fields_required=[asn.X001VEG],
             compute=copy,
             original_long_name="fraction de végétation"),

    'vegetation_rugosity':
        dict(fa_fields_required=[asn.X001Z0VEG],
             compute=copy,
             original_long_name="rugosité de la végétaton"),

}


module = sys.modules[__name__]
for name in vars:
    setattr(module, name, Variable(**vars[name], name=name))
