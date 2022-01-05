import numpy as np

# http://intra.cnrm.meteo.fr/aromerecherche/spip.php?article25
transformations = {
               'Tair':
                   dict(fa_fields_required=['CLSTEMPERATURE'],#CLSTEMPERATURE
                        grib_field_required=['CLSTEMPERATURE'],
                        surface_variable=False,
                        compute="compute_temperature_in_degree_c",
                        details_original_field="2 m Temperature"
                        ),
               'T1':
                   dict(fa_fields_required=['S090TEMPERATURE'],
                        compute="compute_temperature_in_degree_c",
                        details_original_field="Prognostic lowest level temperature"),

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

               'ts':
                   dict(fa_fields_required=['SURFTEMPERATURE'],
                        compute=None,
                        details_original_field="Surface temperature. Ts (the one used in radiation)"),

               'Wind':
                   dict(fa_fields_required=['CLSVENT.ZONAL', 'CLSVENT.MERIDIEN'],
                        compute="compute_wind_speed",
                        details_original_field="10 m wind speed"),

               'Wind_Gust':
                   # Wind gust name has changed few years ago
                   dict(fa_fields_required=['CLSU.RAF60M.XFU', 'CLSV.RAF60M.XFU'],
                        compute="compute_wind_speed",
                        details="U and V 10m wind gusts (max since last file)"),

               'Wind_DIR':
                   dict(fa_fields_required =['CLSVENT.ZONAL', 'CLSVENT.MERIDIEN'],
                        compute="compute_wind_direction"),

               'PSurf':
                   dict(fa_fields_required=['SURFPRESSION'],
                        compute="compute_psurf",
                        details_original_field="Surface pressure"),

               'ZS':
                   dict(fa_fields_required=['SPECSURFGEOPOTEN'],
                        compute="compute_zs",
                        details_original_field="Surface elevation. "
                                "This variable is added once to the netcdf: during the first forecast term"),

               'Rainf':
                   dict(fa_fields_required=['SURFACCPLUIE'],
                        compute="compute_decumul"),

               'Grauf':
                   dict(fa_fields_required=['SURFACCGRAUPEL'],
                        compute="compute_decumul"),

               'LWdown':
                    dict(fa_fields_required=['SURFRAYT THER DE'],
                         compute="compute_decumul"),

               'DIR_SWdown':
                    dict(fa_fields_required=['SURFRAYT DIR SUR'],
                         compute="compute_decumul"),

               'Snowf':
                    dict(fa_fields_required=['SURFACCNEIGE', 'SURFACCGRAUPEL'],
                         compute="compute_snowfall",
                         details_original_field="Snowfall = Cumulative snow + graupel"),

               'SCA_SWdown':
               # todo check decumul
                   dict(fa_fields_required=['SURFRAYT SOLA DE', 'SURFRAYT DIR SUR'],
                        compute="compute_SCA_SWdown",
                        details_original_field="SURFRAYT SOLA DE = Cum. Downward solar flux at surface"),









               'TOA_SWnet':
                    dict(fa_fields_required=['SOMMFLU.RAY.SOLA'],
                         compute="compute_decumul",
                         details="Cum. net solar flux top of atm."),
               'SWnet':
                    dict(fa_fields_required=['SURFFLU.RAY.SOLA'],
                         compute="compute_decumul",
                         details="Cum. net solar flux at surface"),
               'TOA_LWnet':
                    dict(fa_fields_required=['SOMMFLU.RAY.THER'],
                         compute="compute_decumul",
                         details="Cum. net IR flux top of atm."),
               'LWnet':
                    dict(fa_fields_required=['SURFFLU.RAY.THER'],
                         compute="compute_decumul",
                         details="Cum. net IR flux at surface"),
               'LHF':
                    dict(fa_fields_required=['SURFFLU.LAT.MEVA', 'SURFFLU.LAT.MSUB'],
                         compute="compute_latent_heat_flux",
                         details="LHF =SURFFLU.LAT.MEVA' + 'SURFFLU.LAT.MSUB'"),
               'SHF':
                    dict(fa_fields_required=['SURFFLU.CHA.SENS'],
                         compute="compute_decumul",
                         details="Cum.Sensible heat flux"),

               'Tmin':
                    dict(fa_fields_required=['CLSMINI.TEMPERAT'],
                         compute="compute_temperature_in_degree_c",
                         details="T2m mini since last output file"),
               'Tmax':
                    dict(fa_fields_required=['CLSMAXI.TEMPERAT'],
                         compute="compute_temperature_in_degree_c",
                         details="T2m maxi since last output file"),
               'RH2m':
                    dict(fa_fields_required=['CLSHUMI.RELATIVE'],
                         compute=None,
                         details=" 	2m relative humidity"),
               'CC_inst':
                    dict(fa_fields_required=['SURFNEBUL.TOTALE'],
                         compute=None,
                         details="Inst. Total nebulosity"),
               'CC_inst_low':
                    dict(fa_fields_required=['SURFNEBUL.BASSE'],
                         compute=None,
                         details="Inst. Low nebulosity"),
               'CC_inst_middle':
                    dict(fa_fields_required=['SURFNEBUL.MOYENN'],
                         compute=None,
                         details="Inst. Middle nebulosity"),
               'CC_inst_high':
                    dict(fa_fields_required=['SURFNEBUL.HAUTE'],
                         compute=None,
                         details="Inst. High nebulosity"),
               'CC_decumul':
                    dict(fa_fields_required=['ATMONEBUL.TOTALE'],
                         compute="compute_decumul",
                         details="Cum. total nebulosity"),
               'BLH':
                    dict(fa_fields_required=['CLPMHAUT.MOD.XFU'],
                         compute=None,
                         details="Boudary Layer Height (m)"),
               'clear_sky_SWnet':
                    dict(fa_fields_required=['SnnnRAYT SOL CL'],
                         compute=None,
                         details="Net Clear sky surf solar radiation"),
               'clear_sky_LWnet':
                    dict(fa_fields_required=['SnnnRAYT THER CL'],
                         compute=None,
                         details="Net Clear sky surf thermal radiation"),
               'SWD':
               # todo check decumul

                   dict(fa_fields_required=['SURFRAYT SOLA DE'],
                         compute=None,
                         details="Cum. Downward solarflux at surface"),
               'LWD':
               # todo check decumul
                   dict(fa_fields_required=['SURFRAYT THER DE'],
                         compute=None,
                         details="Cum. Downward IR at surface"),




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
                         details_original_field="5 m TKE"),

               'TT87':
                    dict(fa_fields_required=['S090TEMPERATURE'],
                         compute=None,
                         details_original_field="50 m TKE"),

               'TT84':
                    dict(fa_fields_required=['S090TEMPERATURE'],
                         compute=None,
                         details_original_field="126 m TKE"),

               'TT75':
                    dict(fa_fields_required=['S090TEMPERATURE'],
                         compute=None,
                         details_original_field="515 m TKE"),






               'TT90':
                    dict(fa_fields_required=['S090TEMPERATURE'],
                         compute=None,
                         details_original_field="5 m TKE"),

               'TT87':
                    dict(fa_fields_required=['S090TEMPERATURE'],
                         compute=None,
                         details_original_field="50 m TKE"),

               'TT84':
                    dict(fa_fields_required=['S090TEMPERATURE'],
                         compute=None,
                         details_original_field="126 m TKE"),

               'TT75':
                    dict(fa_fields_required=['S090TEMPERATURE'],
                         compute=None,
                         details_original_field="515 m TKE"),

}

alternatives_names_fa = {'CLSU.RAF60M.XFU': ['CLSU.RAF.MOD.XFU'],
                         'CLSV.RAF60M.XFU': ['CLSV.RAF.MOD.XFU']}

domains = {
        'alp': {'first_i': np.intp(900), 'last_i': np.intp(1075), 'first_j': np.intp(525), 'last_j': np.intp(750)},
        'pyr': {'first_i': np.intp(480), 'last_i': np.intp(785), 'first_j': np.intp(350), 'last_j': np.intp(475)},
        'test_alp': {'first_i': np.intp(1090), 'last_i': np.intp(1100), 'first_j': np.intp(740), 'last_j': np.intp(750)},
        'jesus': {'first_i': np.intp(551), 'last_i': np.intp(593), 'first_j': np.intp(414), 'last_j': np.intp(435)},
        # switzerland: lower left corner = 45.56420273320563, 5.609121093614332,
        # upper right corner = 47.971669285287895, 10.684804314227717
        'switzerland': {'first_i': np.intp(931), 'last_i': np.intp(1211), 'first_j': np.intp(671), 'last_j': np.intp(899)},
        #corsica: lower left corner = 41.261440607733036, 8.339223910913976
        # upper right corner = 43.141222812632364, 9.718007989240773
        'corsica': {'first_i': np.intp(1124), 'last_i': np.intp(1197), 'first_j': np.intp(314), 'last_j': np.intp(482)}
}
