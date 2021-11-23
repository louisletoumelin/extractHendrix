from post_process import difference, cumul, postprocess_default, wind_speed_from_components, \
    postprocess_wind_gust, wind_direction_from_components

#todo implement the following variables
{'CLSHUMI.SPECIFIQ':'Qair',
                  'SURFPRESSION':'PSurf','SPECSURFGEOPOTEN':'ZS', 'SURFACCPLUIE':'Rainf',
                  'SURFACCNEIGE':'Snowf','SURFACCGRAUPEL':'Grauf','SURFRAYT THER DE':'LWdown',
                  'SURFRAYT SOLA DE':'SCA_SWdown','SURFRAYT DIR SUR':'DIR_SWdown','CLSVENT.ZONAL':'Wind',
                  'SURFPREC.ANA.EAU':'Rainf_ana','SURFPREC.ANA.NEI':'Snowf_ana'
                       }
name_nc  = {   'Tair':
                   dict(fa_fields_required=['CLSTEMPERATURE'],
                        compute=postprocess_default,
                        details="Diagnostic temperature"),
               'T1':
                   dict(fa_fields_required=['S090TEMPERATURE'],
                        compute=postprocess_default,
                        details="Prognostic lowest level temperature"),

               'SCA_SWdown':
                   dict(fa_fields_required=['SURFRAYT SOLA DE', 'SURFRAYT DIR SUR'],
                        #todo change this function
                        compute=difference),

               'Wind':
                   dict(fa_fields_required=['CLSVENT.ZONAL', 'CLSVENT.MERIDIEN'],
                        compute=wind_speed_from_components),

               'Wind_Gust':
                   # Wind gust name has changed few years ago
                   dict(fa_fields_required=['CLSU.RAF60M.XFU', 'CLSV.RAF60M.XFU', 'CLSU.RAF.MOD.XFU', 'CLSV.RAF.MOD.XFU'],
                        compute=postprocess_wind_gust),

               'Wind_DIR':
                   dict(fa_fields_required =['CLSVENT.ZONAL', 'CLSVENT.MERIDIEN'],
                        compute=wind_direction_from_components),

               'ts':
                   dict(fa_fields_required=['SURFTEMPERATURE'],
                        compute=wind_direction_from_components),

               }


def init_netcdf_file():
    forcing_file = 'FORCING_day_' + domain + '_' + date_beg.strftime("%Y%m%d%H") + '_' + date_end.strftime(
        "%Y%m%d%H") + '.nc'
    output_resource = epygram.formats.resource(forcing_file, 'w',
                                               fmt='netCDF')  # on ouvre le netCDF de sortie en écriture
    # et on lui dit quel comportement on veut qu'il adopte (du point de vue conventions netCDF)
    output_resource.behave(N_dimension='Number_of_points',
                           X_dimension='xx',
                           Y_dimension='yy',
                           force_a_T_dimension=True
                           )


def get_terms():
    """
    Input=config file from user
    Output=list of terms
    """
    # todo implement this function
    pass

def add_to_netcdf():
    pass

def select_namespace():
    namespace =  'oper.archive.fr'  # archive + local cache : le temps de mettre au point le script, C)vite de retransfC)rer les fichiers C  chaque fois
    #IG++
    if date_beg.date() > datetime.date(2019,7,2): # date codee en dur : elle correspond au moment ou la localisation des archives a change.
        #print('date > 2 juil 2019\n')
        #print(date_beg)
        namespace = 'vortex.archive.fr'  # the files we request are archived (on hendrix), coming from DSI suites
        #print('ISA check namespace\n')
        #print(namespace)
    #IG--
    namespace2 = 'olive.archive.fr' # Name space for MESCAN experiment

def add_necessary_data_to_SURFEX():
    pass


init_netcdf_file()
term = get_terms()
for index, term in enumerate(terms):
    for name, infos in name_nc.items():
        compute_func = infos['compute']
        final[name] = compute_func(vortexreader_readfield, *infos[fields_required], index)
        add_to_netcdf()





# Utilisateur: rentre

01/01/2018
02/01/2018
temp, diagnostic
humidity, prognostic
rayonnement,
vent

# TODO: fonction de lecture Vortex
# lire tous les fields_required dans name_nc -> names_fa
# data_from_vortex =  {}
# for name in names_fa:
#      data[name] = vortex.readfield(var1)

# for name in name_nc:
#     final_array = name_nc[compute].get_data()(data, *fields_required)


# fonctions :

# lecture d'un champ FA (argument: nom_fa) (et le mapping pour field_alternate)

# transformation des champs FA en champs finaux

