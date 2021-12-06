import numpy as np

transformations = {
               'Tair':
                   dict(fa_fields_required=['CLSTEMPERATURE'],#CLSTEMPERATURE
                        compute="compute_decumul",
                        details="Diagnostic temperature"),
               'T1':
                   dict(fa_fields_required=['S090TEMPERATURE'],
                        compute=None,
                        details="Prognostic lowest level temperature"),

               # todo 1/3: Isabelle used the prognostic humidity and stored it in Qair. Now prognostic humidity is Q1. We
               # 2/3: should create a function that put the values of Q1 inside Qair when the user desires
               # 3/3: prognostic humidity to force SURFEX
               'Qair':
                   dict(fa_fields_required=['CLSHUMI.SPECIFIQ'],
                        compute=None,
                        details="Diagnostic specifiq humidity at 2m a.g.l."),

               'Q1':
                   dict(fa_fields_required=['S090HUMI.SPECIFI'],
                        compute=None,
                        details="Prognostic specific humidity at the lowest vertical level in the model"),

               'ts':
                   dict(fa_fields_required=['SURFTEMPERATURE'],
                        compute=None),

               'Wind':
                   dict(fa_fields_required=['CLSVENT.ZONAL', 'CLSVENT.MERIDIEN'],
                        compute="compute_wind_speed"),

               'Wind_Gust':
                   # Wind gust name has changed few years ago
                   dict(fa_fields_required=['CLSU.RAF60M.XFU', 'CLSV.RAF60M.XFU'],
                        compute="compute_wind_speed",
                        details="Wind gust has alternative names"),

               'Wind_DIR':
                   dict(fa_fields_required =['CLSVENT.ZONAL', 'CLSVENT.MERIDIEN'],
                        compute="compute_wind_direction"),

               'PSurf':
                   dict(fa_fields_required=['SURFPRESSION'],
                        compute="compute_psurf",
                        details="Surface pressure"),

               'ZS':
                   dict(fa_fields_required=['SPECSURFGEOPOTEN'],
                        compute="compute_zs",
                        details="Surface elevation. "
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
                         detail="Snowfall = snow + graupel"),

               'SCA_SWdown':
                   dict(fa_fields_required=['SURFRAYT SOLA DE', 'SURFRAYT DIR SUR'],
                        compute="compute_SCA_SWdown"),

               }

alternatives_names_fa = {'CLSU.RAF60M.XFU': ['CLSU.RAF.MOD.XFU'],
                         'CLSV.RAF60M.XFU': ['CLSV.RAF.MOD.XFU']}

domains = {
        'alp': {'first_i': np.intp(900), 'last_i': np.intp(1075), 'first_j': np.intp(525), 'last_j': np.intp(750)},
        'pyr': {'first_i': np.intp(480), 'last_i': np.intp(785), 'first_j': np.intp(350), 'last_j': np.intp(475)},
        'test_alp': {'first_i': np.intp(1090), 'last_i': np.intp(1100), 'first_j': np.intp(740), 'last_j': np.intp(750)},
        'jesus': {'first_i': np.intp(551), 'last_i': np.intp(593), 'first_j': np.intp(414), 'last_j': np.intp(435)}
        }
