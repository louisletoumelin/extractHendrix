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
                        surface_variable=[False],
                        compute="compute_temperature_in_degree_c",
                        details_original_field="2 m Temperature"
                        ),
               'T1':
                   dict(fa_fields_required=['S090TEMPERATURE'],
                        compute="compute_temperature_in_degree_c",
                        details_original_field="Prognostic lowest level temperature"),
                'ts':
                    dict(fa_fields_required=['SURFTEMPERATURE'],
                         grib_fields_required=[dict()],
                         compute=None,
                         surface_variable=[False],
                         details_original_field="Surface temperature. Ts (the one used in radiation)"),
               'Tmin':
                    dict(fa_fields_required=['CLSMINI.TEMPERAT'],
                         compute="compute_temperature_in_degree_c",
                         details_original_field="T2m mini since last output file"),
               'Tmax':
                    dict(fa_fields_required=['CLSMAXI.TEMPERAT'],
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
                        compute=None,
                        details_original_field="2m specific humidity"),

               'Q1':
                   dict(fa_fields_required=['S090HUMI.SPECIFI'],
                        compute=None,
                        details_original_field="Specific moisture"),

               'RH2m':
                    dict(fa_fields_required=['CLSHUMI.RELATIVE'],
                         compute="compute_multiply_by_100",
                         details_original_field=" 	2m relative humidity"),

               #
               # Wind
               #

               'Wind':
                   dict(fa_fields_required=['CLSVENT.ZONAL', 'CLSVENT.MERIDIEN'],
                        grib_fields_required=[dict(shortName='10u'), dict(shortName='10v')],
                        compute="compute_wind_speed",
                        surface_variable=[False, False],
                        details_original_field="10 m wind speed"),

               'Wind_Gust':
                   # Wind gust name has changed few years ago
                   dict(fa_fields_required=['CLSU.RAF60M.XFU', 'CLSV.RAF60M.XFU'],
                        compute="compute_wind_speed",
                        details_original_field="U and V 10m wind gusts (max since last file)"),

               'Wind_DIR':
                   dict(fa_fields_required =['CLSVENT.ZONAL', 'CLSVENT.MERIDIEN'],
                        compute="compute_wind_direction"),

               #
               # Pressure, elevation
               #

               'PSurf':
                   dict(fa_fields_required=['SURFPRESSION'],
                        compute="compute_psurf",
                        details_original_field="Surface pressure"),

               'ZS':
                   dict(fa_fields_required=['SPECSURFGEOPOTEN'],
                        compute="compute_zs",
                        details_original_field="Surface elevation. "
                                "This variable is added once to the netcdf: during the first forecast term"),

               'BLH':
                    dict(fa_fields_required=['CLPMHAUT.MOD.XFU'],
                         compute=None,
                         details_original_field="Boudary Layer Height (m)"),

               #
               # Precipitations
               #

               'Rainf':
                   dict(fa_fields_required=['SURFACCPLUIE'],
                        compute="compute_decumul"),

               'Grauf':
                   dict(fa_fields_required=['SURFACCGRAUPEL'],
                        compute="compute_decumul"),

               'Snowf':
                    dict(fa_fields_required=['SURFACCNEIGE', 'SURFACCGRAUPEL'],
                         compute="compute_snowfall",
                         details_original_field="Snowfall = Cumulative snow + graupel"),

               #
               # Longwave
               #

               'LWdown':
                    dict(fa_fields_required=['SURFRAYT THER DE'],
                         compute="compute_decumul"),
               'LWU':
                   dict(fa_fields_required=['SURFRAYT THER DE', 'SURFFLU.RAY.THER'],
                        compute="compute_decumul_and_diff"),

               'TOA_LWnet':
                    dict(fa_fields_required=['SOMMFLU.RAY.THER'],
                         compute="compute_decumul",
                         details_original_field="Cum. net IR flux top of atm."),
               'LWnet':
                    dict(fa_fields_required=['SURFFLU.RAY.THER'],
                         compute="compute_decumul",
                         details_original_field="Cum. net IR flux at surface"),

               'clear_sky_LWnet':
                    dict(fa_fields_required=['SnnnRAYT THER CL'],
                         compute=None,
                         details_original_field="Net Clear sky surf thermal radiation"),

               #
               # Shortwave
               #

               'DIR_SWdown':
                    dict(fa_fields_required=['SURFRAYT DIR SUR'],
                         compute="compute_decumul"),
               'SCA_SWdown':
                   dict(fa_fields_required=['SURFRAYT SOLA DE', 'SURFRAYT DIR SUR'],
                        compute="compute_decumul_and_diff",
                        details_original_field="SURFRAYT SOLA DE = Cum. Downward solar flux at surface"),

               'TOA_SWnet':
                    dict(fa_fields_required=['SOMMFLU.RAY.SOLA'],
                         compute="compute_decumul",
                         details_original_field="Cum. net solar flux top of atm."),
               'SWnet':
                    dict(fa_fields_required=['SURFFLU.RAY.SOLA'],
                         compute="compute_decumul",
                         details_original_field="Cum. net solar flux at surface"),
               'SWD':
                   dict(fa_fields_required=['SURFRAYT SOLA DE'],
                         compute="compute_decumul",
                         details_original_field="Cum. Downward solarflux at surface"),

               'SWU':
                   dict(fa_fields_required=['SURFRAYT SOLA DE', 'SURFFLU.RAY.SOLA'],
                         compute="compute_decumul_and_diff",
                         details_original_field="Cum. Downward solarflux at surface"),

               'clear_sky_SWnet':
                    dict(fa_fields_required=['SnnnRAYT SOL CL'],
                         compute=None,
                         details_original_field="Net Clear sky surf solar radiation"),


               #
               # Turbulent fluxes
               #

               'LHF':
                    dict(fa_fields_required=['SURFFLU.LAT.MEVA', 'SURFFLU.LAT.MSUB'],
                         compute="compute_latent_heat_flux",
                         details_original_field="LHF =SURFFLU.LAT.MEVA' + 'SURFFLU.LAT.MSUB'"),
               'SHF':
                    dict(fa_fields_required=['SURFFLU.CHA.SENS'],
                         compute="compute_decumul_and_negative",
                         details_original_field="Cum.Sensible heat flux"),

               #
               # Clouds
               #


               'CC_inst':
                    dict(fa_fields_required=['SURFNEBUL.TOTALE'],
                         compute=None,
                         details_original_field="Inst. Total nebulosity"),
               'CC_inst_low':
                    dict(fa_fields_required=['SURFNEBUL.BASSE'],
                         compute=None,
                         details_original_field="Inst. Low nebulosity"),
               'CC_inst_middle':
                    dict(fa_fields_required=['SURFNEBUL.MOYENN'],
                         compute=None,
                         details_original_field="Inst. Middle nebulosity"),
               'CC_inst_high':
                    dict(fa_fields_required=['SURFNEBUL.HAUTE'],
                         compute=None,
                         details_original_field="Inst. High nebulosity"),

               'CC_cumul':
                    dict(fa_fields_required=['ATMONEBUL.TOTALE'],
                         compute="compute_decumul",
                         details_original_field="Cum. total nebulosity"),
               'CC_cumul_low':
                    dict(fa_fields_required=['ATMONEBUL.BASSE'],
                         compute="compute_decumul",
                         details_original_field="Cum. total nebulosity. Used by Seity."),
               'CC_cumul_middle':
                    dict(fa_fields_required=['ATMONEBUL.MOYENN'],
                         compute="compute_decumul",
                         details_original_field="Cum. total nebulosity. Used by Seity."),
               'CC_cumul_high':
                    dict(fa_fields_required=['ATMONEBUL.HAUTE'],
                         compute="compute_decumul",
                         details_original_field="Cum. total nebulosity. Used by Seity."),
               #
               # Variables by level
               #

               'Wind90':
                   dict(fa_fields_required=['S090WIND.U.PHYS', 'S090WIND.V.PHYS'],
                        compute="compute_wind_speed",
                        details_original_field="5 m wind speed"),

               'Wind87':
                   dict(fa_fields_required=['S087WIND.U.PHYS', 'S087WIND.V.PHYS'],
                        compute="compute_wind_speed",
                        details_original_field="50 m wind speed"),

               'Wind84':
                   dict(fa_fields_required=['S084WIND.U.PHYS', 'S084WIND.V.PHYS'],
                        compute="compute_wind_speed",
                        details_original_field="126 m wind speed"),

               'Wind75':
                   dict(fa_fields_required=['S075WIND.U.PHYS', 'S075WIND.V.PHYS'],
                        compute="compute_wind_speed",
                        details_original_field="515 m wind speed"),

               'TKE90':
                    dict(fa_fields_required=['S090TKE'],
                         compute=None,
                         details_original_field="5 m TKE"),

               'TKE87':
                    dict(fa_fields_required=['S087TKE'],
                         compute=None,
                         details_original_field="50 m TKE"),

               'TKE84':
                    dict(fa_fields_required=['S084TKE'],
                         compute=None,
                         details_original_field="126 m TKE"),

               'TKE75':
                    dict(fa_fields_required=['S075TKE'],
                         compute=None,
                         details_original_field="515 m TKE"),

               'TT90':
                    dict(fa_fields_required=['S090TEMPERATURE'],
                         compute=None,
                         details_original_field="5 m Temperature"),

               'TT87':
                    dict(fa_fields_required=['S087TEMPERATURE'],
                         compute=None,
                         details_original_field="50 m Temperature"),

               'TT84':
                    dict(fa_fields_required=['S084TEMPERATURE'],
                         compute=None,
                         details_original_field="126 m Temperature"),

               'TT75':
                    dict(fa_fields_required=['S075TEMPERATURE'],
                         compute=None,
                         details_original_field="515 m Temperature"),

               'water_content90':
                    dict(fa_fields_required=['S090CLOUD_WATER', 'S090ICE_CRYSTAL', 'S090SNOW', 'S090RAIN'],
                         compute="compute_sum_all_water_species",
                         details_original_field="5 m water content"
                                                "water content = Cloud dropplets + Ice crystals + Snow + Rain"),

               'water_content87':
                    dict(fa_fields_required=['S087CLOUD_WATER', 'S087ICE_CRYSTAL', 'S087SNOW', 'S087RAIN'],
                         compute="compute_sum_all_water_species",
                         details_original_field="50 m water content"),

               'water_content84':
                    dict(fa_fields_required=['S084CLOUD_WATER', 'S084ICE_CRYSTAL', 'S084SNOW', 'S084RAIN'],
                         compute="compute_sum_all_water_species",
                         details_original_field="126 m water content"),

               'water_content75':
                    dict(fa_fields_required=['S075CLOUD_WATER', 'S075ICE_CRYSTAL', 'S075SNOW', 'S075RAIN'],
                         compute="compute_sum_all_water_species",
                         details_original_field="515 m water content"),

               #
               # Surface variables
               #

               'SWE':
                    dict(fa_fields_required=['X001WSN_VEG1'],
                         surface_variable=[True],
                         compute=None,
                         details_original_field="contenu équivalent en eau de la neige [km m-2]"),

               'snow_density':
                    dict(fa_fields_required=['X001RSN_VEG1'],
                         surface_variable=[True],
                         compute=None,
                         details_original_field="densité de la neige [km m-3]"),

               'snow_albedo':
                    dict(fa_fields_required=['X001ASN_VEG1'],
                         surface_variable=[True],
                         compute=None,
                         details_original_field="albédo de la neige"),

               'vegetation_fraction':
                    dict(fa_fields_required=['X001VEG'],
                         surface_variable=[True],
                         compute=None,
                         details_original_field="fraction de végétation"),

               'vegetation_rugosity':
                    dict(fa_fields_required=['X001Z0VEG'],
                         surface_variable=[True],
                         compute=None,
                         details_original_field="rugosité de la végétaton"),

}
"""
Sometime, the name of a variable can change with time (ex: wind gust).
Here are alternative names to check if first name is not found
"""

alternatives_names_fa = {'CLSU.RAF60M.XFU': ['CLSU.RAF.MOD.XFU'],
                         'CLSV.RAF60M.XFU': ['CLSV.RAF.MOD.XFU']}

"""
A domain can be defined by coordinates (lat/lon) or indices on the grid of the model
If indices are given, they will be prioritized.
"""

domains = {
        # alp
        'alp': {'first_i': np.intp(900), 'last_i': np.intp(1075), 'first_j': np.intp(525), 'last_j': np.intp(750),
                'lon_llc': 5.0144, 'lat_llc': 43.88877, 'lon_urc': 8.125426, 'lat_urc': 46.395446},
        # pyr
        'pyr': {'first_i': np.intp(480), 'last_i': np.intp(785), 'first_j': np.intp(350), 'last_j': np.intp(475),
                'lon_llc': -1.65953, 'lat_llc': 41.825578, 'lon_urc': 3.139407, 'lat_urc':43.3406425},
        # test_alp
        'test_alp': {'first_i': np.intp(1090), 'last_i': np.intp(1100), 'first_j': np.intp(740), 'last_j': np.intp(750),
                     'lon_llc': 8.36517, 'lat_llc': 46.26501, 'lon_urc': 8.5477, 'lat_urc': 46.3719},
        # jesus
        'jesus': {'first_i': np.intp(551), 'last_i': np.intp(593), 'first_j': np.intp(414), 'last_j': np.intp(435),
                  'lon_llc': -0.582946, 'lat_llc': 42.60378, 'lon_urc': 0.074149, 'lat_urc': 42.8626},
        # switzerland
        'switzerland': {'first_i': np.intp(931), 'last_i': np.intp(1211), 'first_j': np.intp(671),
                        'last_j': np.intp(899), 'lon_llc': 5.609121, 'lat_llc': 45.5642, 'lon_urc': 10.6848,
                        'lat_urc': 47.97167},
        # corsica
        'corsica': {'first_i': np.intp(1124), 'last_i': np.intp(1197), 'first_j': np.intp(314), 'last_j': np.intp(482),
                    'lon_llc': 8.33922, 'lat_llc': 41.26144, 'lon_urc': 9.718, 'lat_urc': 43.14122}
}
