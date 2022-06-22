import numpy as np

# http://intra.cnrm.meteo.fr/aromerecherche/spip.php?article25

"""
The dictionary transformations links output variable (ex: Wind), with the variables of 
the file on hendrix (ex: 'CLSVENT.ZONAL', 'CLSVENT.MERIDIEN')

The structure of the dictionary if the following:

transformations = {
               'Name_of_variable_in_final_netcdf_file':
                   dict(fa_fields_required=['fa_name'],
                        grib_fields_required=[dict(shortName='short_name', productDefinitionTemplateNumber=1)],
                        surface_variable=[False],
                        compute="name of the function to apply",
                        details_original_field="Description of the variable. Not used for computations"
                        ),

"""

transformations = {

               #
               # Temperature
               #

               'Tair':
                   dict(fa_fields_required=['CLSTEMPERATURE'],
                        grib_fields_required=[dict(shortName='2t', productDefinitionTemplateNumber=1)],
                        is_surface_variable=[False],
                        compute="compute_temperature_in_degree_c",
                        details_original_field="2 m Temperature"
                        ),
               'T1':
                   dict(fa_fields_required=['S090TEMPERATURE'],
                        grib_fields_required=[dict()],
                        is_surface_variable=[False],
                        compute="compute_temperature_in_degree_c",
                        details_original_field="Prognostic lowest level temperature"),
                'ts':
                    dict(fa_fields_required=['SURFTEMPERATURE'],
                         grib_fields_required=[dict()],
                         is_surface_variable=[False],
                         compute=None,
                         details_original_field="Surface temperature. Ts (the one used in radiation)"),
               'Tmin':
                    dict(fa_fields_required=['CLSMINI.TEMPERAT'],
                         grib_fields_required=[dict()],
                         is_surface_variable=[False],
                         compute="compute_temperature_in_degree_c",
                         details_original_field="T2m mini since last output file"),
               'Tmax':
                    dict(fa_fields_required=['CLSMAXI.TEMPERAT'],
                         grib_fields_required=[dict()],
                         is_surface_variable=[False],
                         compute="compute_temperature_in_degree_c",
                         details_original_field="T2m maxi since last output file"),

               #
               # Humidity
               #

               # todo 1/3: Isabelle used the prognostic humidity and stored it in Qair. Now prognostic humidity is Q1. We
               # 2/3: should create a function that put the values of Q1 inside Qair when the user desires
               # 3/3: prognostic humidity to force SURFEX
               'Qair':
                   dict(fa_fields_required=['CLSHUMI.SPECIFIQ'],
                        grib_fields_required=[dict()],
                        is_surface_variable=[False],
                        compute=None,
                        details_original_field="2m specific humidity"),

               'Q1':
                   dict(fa_fields_required=['S090HUMI.SPECIFI'],
                        grib_fields_required=[dict()],
                        is_surface_variable=[False],
                        compute=None,
                        details_original_field="Specific moisture"),

               'RH2m':
                    dict(fa_fields_required=['CLSHUMI.RELATIVE'],
                         grib_fields_required=[dict()],
                         is_surface_variable=[False],
                         compute="compute_multiply_by_100",
                         details_original_field=" 	2m relative humidity"),

               #
               # Wind
               #

               'Wind':
                   dict(fa_fields_required=['CLSVENT.ZONAL', 'CLSVENT.MERIDIEN'],
                        grib_fields_required=[dict(shortName='10u'), dict(shortName='10v')],
                        is_surface_variable=[False, False],
                        compute="compute_wind_speed",
                        details_original_field="10 m wind speed"),

               'Wind_Gust':
                   # Wind gust name has changed few years ago
                   dict(fa_fields_required=['CLSU.RAF60M.XFU', 'CLSV.RAF60M.XFU'],
                        grib_fields_required=[dict(), dict()],
                        is_surface_variable=[False, False],
                        compute="compute_wind_speed",
                        details_original_field="U and V 10m wind gusts (max since last file)"),

               'Wind_DIR':
                   dict(fa_fields_required =['CLSVENT.ZONAL', 'CLSVENT.MERIDIEN'],
                        grib_fields_required=[dict(), dict()],
                        is_surface_variable=[False, False],
                        compute="compute_wind_direction"),

               #
               # Pressure, elevation
               #

               'PSurf':
                   dict(fa_fields_required=['SURFPRESSION'],
                        grib_fields_required=[dict()],
                        is_surface_variable=[False],
                        compute="compute_psurf",
                        details_original_field="Surface pressure"),

               'ZS':
                   dict(fa_fields_required=['SPECSURFGEOPOTEN'],
                        grib_fields_required=[dict()],
                        is_surface_variable=[False],
                        compute="compute_zs",
                        details_original_field="Surface elevation. "
                                "This variable is added once to the netcdf: during the first forecast term"),

               'BLH':
                    dict(fa_fields_required=['CLPMHAUT.MOD.XFU'],
                         grib_fields_required=[dict()],
                         is_surface_variable=[False],
                         compute=None,
                         details_original_field="Boudary Layer Height (m)"),

               #
               # Precipitations
               #

               'Rainf':
                   dict(fa_fields_required=['SURFACCPLUIE'],
                        grib_fields_required=[dict()],
                        is_surface_variable=[False],
                        compute="compute_decumul"),

               'Grauf':
                   dict(fa_fields_required=['SURFACCGRAUPEL'],
                        grib_fields_required=[dict()],
                        is_surface_variable=[False],
                        compute="compute_decumul"),

               'Snowf':
                    dict(fa_fields_required=['SURFACCNEIGE', 'SURFACCGRAUPEL'],
                         grib_fields_required=[dict(), dict()],
                         is_surface_variable=[False, False],
                         compute="compute_snowfall",
                         details_original_field="Snowfall = Cumulative snow + graupel"),

               #
               # Longwave
               #

               'LWdown':
                    dict(fa_fields_required=['SURFRAYT THER DE'],
                         grib_fields_required=[dict()],
                         is_surface_variable=[False],
                         compute="compute_decumul"),
               'LWU':
                   dict(fa_fields_required=['SURFRAYT THER DE', 'SURFFLU.RAY.THER'],
                        grib_fields_required=[dict(), dict()],
                        is_surface_variable=[False, False],
                        compute="compute_decumul_and_diff"),

               'TOA_LWnet':
                    dict(fa_fields_required=['SOMMFLU.RAY.THER'],
                         grib_fields_required=[dict()],
                         is_surface_variable=[False],
                         compute="compute_decumul",
                         details_original_field="Cum. net IR flux top of atm."),
               'LWnet':
                    dict(fa_fields_required=['SURFFLU.RAY.THER'],
                         grib_fields_required=[dict()],
                         is_surface_variable=[False],
                         compute="compute_decumul",
                         details_original_field="Cum. net IR flux at surface"),

               'clear_sky_LWnet':
                    dict(fa_fields_required=['SRAYT THER CL'],
                         grib_fields_required=[dict()],
                         is_surface_variable=[False],
                         compute=None,
                         details_original_field="Net Clear sky surf thermal radiation"),

               #
               # Shortwave
               #

               'DIR_SWdown':
                    dict(fa_fields_required=['SURFRAYT DIR SUR'],
                         grib_fields_required=[dict()],
                         is_surface_variable=[False],
                         compute="compute_decumul"),
               'SCA_SWdown':
                   dict(fa_fields_required=['SURFRAYT SOLA DE', 'SURFRAYT DIR SUR'],
                        grib_fields_required=[dict(), dict()],
                        is_surface_variable=[False, False],
                        compute="compute_decumul_and_diff",
                        details_original_field="SURFRAYT SOLA DE = Cum. Downward solar flux at surface"),

               'TOA_SWnet':
                    dict(fa_fields_required=['SOMMFLU.RAY.SOLA'],
                         grib_fields_required=[dict()],
                         is_surface_variable=[False],
                         compute="compute_decumul",
                         details_original_field="Cum. net solar flux top of atm."),
               'SWnet':
                    dict(fa_fields_required=['SURFFLU.RAY.SOLA'],
                         grib_fields_required=[dict()],
                         is_surface_variable=[False],
                         compute="compute_decumul",
                         details_original_field="Cum. net solar flux at surface"),
               'SWD':
                   dict(fa_fields_required=['SURFRAYT SOLA DE'],
                        grib_fields_required=[dict()],
                        is_surface_variable=[False],
                        compute="compute_decumul",
                         details_original_field="Cum. Downward solarflux at surface"),

               'SWU':
                   dict(fa_fields_required=['SURFRAYT SOLA DE', 'SURFFLU.RAY.SOLA'],
                        grib_fields_required=[dict(), dict()],
                        is_surface_variable=[False, False],
                        compute="compute_decumul_and_diff",
                         details_original_field="Cum. Downward solarflux at surface"),

               'clear_sky_SWnet':
                    dict(fa_fields_required=['SRAYT SOL CL'],
                         grib_fields_required=[dict()],
                         is_surface_variable=[False],
                         compute=None,
                         details_original_field="Net Clear sky surf solar radiation"),


               #
               # Turbulent fluxes
               #

               'LHF':
                    dict(fa_fields_required=['SURFFLU.LAT.MEVA', 'SURFFLU.LAT.MSUB'],
                         grib_fields_required=[dict(), dict()],
                         is_surface_variable=[False, False],
                         compute="compute_latent_heat_flux",
                         details_original_field="LHF =SURFFLU.LAT.MEVA' + 'SURFFLU.LAT.MSUB'"),
               'SHF':
                    dict(fa_fields_required=['SURFFLU.CHA.SENS'],
                         grib_fields_required=[dict()],
                         is_surface_variable=[False],
                         compute="compute_decumul_and_negative",
                         details_original_field="Cum.Sensible heat flux"),

               #
               # Clouds
               #


               'CC_inst':
                    dict(fa_fields_required=['SURFNEBUL.TOTALE'],
                         grib_fields_required=[dict()],
                         is_surface_variable=[False],
                         compute=None,
                         details_original_field="Inst. Total nebulosity"),
               'CC_inst_low':
                    dict(fa_fields_required=['SURFNEBUL.BASSE'],
                         grib_fields_required=[dict()],
                         is_surface_variable=[False],
                         compute=None,
                         details_original_field="Inst. Low nebulosity"),
               'CC_inst_middle':
                    dict(fa_fields_required=['SURFNEBUL.MOYENN'],
                         grib_fields_required=[dict()],
                         is_surface_variable=[False],
                         compute=None,
                         details_original_field="Inst. Middle nebulosity"),
               'CC_inst_high':
                    dict(fa_fields_required=['SURFNEBUL.HAUTE'],
                         grib_fields_required=[dict()],
                         is_surface_variable=[False],
                         compute=None,
                         details_original_field="Inst. High nebulosity"),

               'CC_cumul':
                    dict(fa_fields_required=['ATMONEBUL.TOTALE'],
                         grib_fields_required=[dict()],
                         is_surface_variable=[False],
                         compute="compute_decumul",
                         details_original_field="Cum. total nebulosity"),
               'CC_cumul_low':
                    dict(fa_fields_required=['ATMONEBUL.BASSE'],
                         grib_fields_required=[dict()],
                         is_surface_variable=[False],
                         compute="compute_decumul",
                         details_original_field="Cum. total nebulosity. Used by Seity."),
               'CC_cumul_middle':
                    dict(fa_fields_required=['ATMONEBUL.MOYENN'],
                         grib_fields_required=[dict()],
                         is_surface_variable=[False],
                         compute="compute_decumul",
                         details_original_field="Cum. total nebulosity. Used by Seity."),
               'CC_cumul_high':
                    dict(fa_fields_required=['ATMONEBUL.HAUTE'],
                         grib_fields_required=[dict()],
                         is_surface_variable=[False],
                         compute="compute_decumul",
                         details_original_field="Cum. total nebulosity. Used by Seity."),
               #
               # Variables by level
               #

               'Wind90':
                   dict(fa_fields_required=['S090WIND.U.PHYS', 'S090WIND.V.PHYS'],
                        grib_fields_required=[dict(), dict()],
                        is_surface_variable=[False, False],
                        compute="compute_wind_speed",
                        details_original_field="5 m wind speed"),

               'Wind87':
                   dict(fa_fields_required=['S087WIND.U.PHYS', 'S087WIND.V.PHYS'],
                        grib_fields_required=[dict(), dict()],
                        is_surface_variable=[False, False],
                        compute="compute_wind_speed",
                        details_original_field="50 m wind speed"),

               'Wind84':
                   dict(fa_fields_required=['S084WIND.U.PHYS', 'S084WIND.V.PHYS'],
                        grib_fields_required=[dict(), dict()],
                        is_surface_variable=[False, False],
                        compute="compute_wind_speed",
                        details_original_field="126 m wind speed"),

               'Wind75':
                   dict(fa_fields_required=['S075WIND.U.PHYS', 'S075WIND.V.PHYS'],
                        grib_fields_required=[dict(), dict()],
                        is_surface_variable=[False, False],
                        compute="compute_wind_speed",
                        details_original_field="515 m wind speed"),

               'TKE90':
                    dict(fa_fields_required=['S090TKE'],
                         grib_fields_required=[dict()],
                         is_surface_variable=[False],
                         compute=None,
                         details_original_field="5 m TKE"),

               'TKE87':
                    dict(fa_fields_required=['S087TKE'],
                         grib_fields_required=[dict()],
                         is_surface_variable=[False],
                         compute=None,
                         details_original_field="50 m TKE"),

               'TKE84':
                    dict(fa_fields_required=['S084TKE'],
                         grib_fields_required=[dict()],
                         is_surface_variable=[False],
                         compute=None,
                         details_original_field="126 m TKE"),

               'TKE75':
                    dict(fa_fields_required=['S075TKE'],
                         grib_fields_required=[dict()],
                         is_surface_variable=[False],
                         compute=None,
                         details_original_field="515 m TKE"),

               'TT90':
                    dict(fa_fields_required=['S090TEMPERATURE'],
                         grib_fields_required=[dict()],
                         is_surface_variable=[False],
                         compute=None,
                         details_original_field="5 m Temperature"),

               'TT87':
                    dict(fa_fields_required=['S087TEMPERATURE'],
                         grib_fields_required=[dict()],
                         is_surface_variable=[False],
                         compute=None,
                         details_original_field="50 m Temperature"),

               'TT84':
                    dict(fa_fields_required=['S084TEMPERATURE'],
                         grib_fields_required=[dict()],
                         is_surface_variable=[False],
                         compute=None,
                         details_original_field="126 m Temperature"),

               'TT75':
                    dict(fa_fields_required=['S075TEMPERATURE'],
                         grib_fields_required=[dict()],
                         is_surface_variable=[False],
                         compute=None,
                         details_original_field="515 m Temperature"),

               'water_content90':
                    dict(fa_fields_required=['S090CLOUD_WATER', 'S090ICE_CRYSTAL', 'S090SNOW', 'S090RAIN'],
                         grib_fields_required=[dict(), dict(), dict(), dict()],
                         is_surface_variable=[False, False, False, False],
                         compute="compute_sum_all_water_species",
                         details_original_field="5 m water content"
                                                "water content = Cloud dropplets + Ice crystals + Snow + Rain"),

               'water_content87':
                    dict(fa_fields_required=['S087CLOUD_WATER', 'S087ICE_CRYSTAL', 'S087SNOW', 'S087RAIN'],
                         grib_fields_required=[dict(), dict(), dict(), dict()],
                         is_surface_variable=[False, False, False, False],
                         compute="compute_sum_all_water_species",
                         details_original_field="50 m water content"),

               'water_content84':
                    dict(fa_fields_required=['S084CLOUD_WATER', 'S084ICE_CRYSTAL', 'S084SNOW', 'S084RAIN'],
                         grib_fields_required=[dict(), dict(), dict(), dict()],
                         is_surface_variable=[False, False, False, False],
                         compute="compute_sum_all_water_species",
                         details_original_field="126 m water content"),

               'water_content75':
                    dict(fa_fields_required=['S075CLOUD_WATER', 'S075ICE_CRYSTAL', 'S075SNOW', 'S075RAIN'],
                         grib_fields_required=[dict(), dict(), dict(), dict()],
                         is_surface_variable=[False, False, False, False],
                         compute="compute_sum_all_water_species",
                         details_original_field="515 m water content"),

               #
               # Surface variables
               #

               'SWE':
                    dict(fa_fields_required=['X001WSN_VEG1'],
                         grib_fields_required=[dict()],
                         is_surface_variable=[True],
                         compute=None,
                         details_original_field="contenu équivalent en eau de la neige [km m-2]"),

               'snow_density':
                    dict(fa_fields_required=['X001RSN_VEG1'],
                         grib_fields_required=[dict()],
                         is_surface_variable=[True],
                         compute=None,
                         details_original_field="densité de la neige [km m-3]"),

               'snow_albedo':
                    dict(fa_fields_required=['X001ASN_VEG1'],
                         grib_fields_required=[dict()],
                         is_surface_variable=[True],
                         compute=None,
                         details_original_field="albédo de la neige"),

               'vegetation_fraction':
                    dict(fa_fields_required=['X001VEG'],
                         grib_fields_required=[dict()],
                         is_surface_variable=[True],
                         compute=None,
                         details_original_field="fraction de végétation"),

               'vegetation_rugosity':
                    dict(fa_fields_required=['X001Z0VEG'],
                         grib_fields_required=[dict()],
                         is_surface_variable=[True],
                         compute=None,
                         details_original_field="rugosité de la végétaton"),

}

"""
Sometime, the name of a variable can change with time (ex: wind gust).
Here are alternative names to check if first name is not found
"""

alternatives_names_fa = {'CLSU.RAF60M.XFU': ['CLSU.RAF.MOD.XFU'],
                         'CLSV.RAF60M.XFU': ['CLSV.RAF.MOD.XFU'],
                         'X001ASN_VEG1': ['X001ASN_VEG']}
