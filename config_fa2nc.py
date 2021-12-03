transformations = {
               'Tair':
                   dict(fa_fields_required=['CLSTEMPERATURE'],
                        compute=None,
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
                        compute=None),

               'Wind_Gust':
                   # Wind gust name has changed few years ago
                   dict(fa_fields_required=['CLSU.RAF60M.XFU', 'CLSV.RAF60M.XFU', 'CLSU.RAF.MOD.XFU', 'CLSV.RAF.MOD.XFU'],
                        compute=None),

               'Wind_DIR':
                   dict(fa_fields_required =['CLSVENT.ZONAL', 'CLSVENT.MERIDIEN'],
                        compute=None),

               'PSurf':
                   dict(fa_fields_required=['SURFPRESSION'],
                        compute=None,
                        details="Surface pressure"),

               'ZS':
                   dict(fa_fields_required=['SPECSURFGEOPOTEN'],
                        compute=None,
                        details="Surface elevation. "
                                "This variable is added once to the netcdf: during the first forecast term"),

               'Rainf':
                   dict(fa_fields_required=['SURFACCPLUIE'],
                        compute=None),
               'Grauf':
                   dict(fa_fields_required=['SURFACCGRAUPEL'],
                        compute=None),

               'LWdown':
                    dict(fa_fields_required=['SURFRAYT THER DE'],
                         compute=None),

               'DIR_SWdown':
                    dict(fa_fields_required=['SURFRAYT DIR SUR'],
                         compute=None),

               'Snowf':
                    dict(fa_fields_required=['SURFACCNEIGE', 'SURFACCGRAUPEL'],
                         compute=None,
                         detail="Snowfall = snow + graupel"),

               'SCA_SWdown':
                   dict(fa_fields_required=['SURFRAYT SOLA DE', 'SURFRAYT DIR SUR'],
                        compute=None),

               }


domains = {
        'alp':{'first_i': 900, 'last_i' : 1075, 'first_j' : 525, 'last_j' : 750},
        'pyr': { 'first_i' : 480, 'last_i' : 785, 'first_j' : 350, 'last_j' : 475},
        'test_alp':{ 'first_i' : 1090, 'last_i' : 1100, 'first_j' : 740, 'last_j' : 750},
        'jesus': {'first_i':551, 'last_i':593, 'first_j':414, 'last_j':435}
        }


'''
def compute_decumul(dict_data, term, name_variable_FA):
    """
    Calcule le décumul pour l'échéance term
    (on est obligé de mettre term dans les paramètres pour pouvoir gérer le cas des cumuls)

    # Conversion: - from mm to kg/m2/s for precip
    #              - from J/m2 to W/m2 for incoming LW and SW

    Louis: j'ai testé et ça marche
    """
    return read_dict(dict_data, term, name_variable_FA) - read_dict(dict_data, term -1, name_variable_FA)


def compute_psurf(self, dict_data, term, name_variable_FA):
    """Testé"""
    return np.exp(self.read_dict(dict_data, term, name_variable_FA))


def compute_zs(self, dict_data, term, name_variable_FA):
    """Testé"""
    return self.read_dict(dict_data, term, name_variable_FA) / 9.81


def compute_snow(self, dict_data, term, name_snow_FA, name_graupel_FA):
    """Testé"""
    return self.compute_decumul(dict_data, term, name_snow_FA) + self.compute_decumul(dict_data, term, name_graupel_FA)

def compute_SCA_SWdown(self, dict_data, term, name_surfrayt_sola_de_FA, name_surfrayt_dir_sur_FA):
    """Testé"""
    surfrayt_sola_de = self.compute_decumul(dict_data, term, name_surfrayt_sola_de_FA)
    name_surfrayt_dir_sur = self.compute_decumul(dict_data, term, name_surfrayt_dir_sur_FA)
    return surfrayt_sola_de - name_surfrayt_dir_sur
'''
