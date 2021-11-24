from collections import defaultdict

from netcdf import *
from post_process import *


#todo implement "details" bellow, inspired from text in the AROME variable database (description of the variables)
dict_name_nc  = {

               'Tair':
                   dict(fa_fields_required=['CLSTEMPERATURE'],
                        compute=default,
                        details="Diagnostic temperature"),
               'T1':
                   dict(fa_fields_required=['S090TEMPERATURE'],
                        compute=default,
                        details="Prognostic lowest level temperature"),

               # todo 1/3: Isabelle used the prognostic humidity and stored it in Qair. Now prognostic humidity is Q1. We
               # todo 2/3: should create a function that put the values of Q1 inside Qair when the user desires
               # todo 3/3: prognostic humidity to force SURFEX
               'Qair':
                   dict(fa_fields_required=['CLSHUMI.SPECIFIQ'],
                        compute=default,
                        details="Diagnostic specifiq humidity at 2m a.g.l."),

               'Q1':
                   dict(fa_fields_required=['S090HUMI.SPECIFI'],
                        compute=default,
                        details="Prognostic specific humidity at the lowest vertical level in the model"),

               'ts':
                   dict(fa_fields_required=['SURFTEMPERATURE'],
                        compute=default),

               'Wind':
                   dict(fa_fields_required=['CLSVENT.ZONAL', 'CLSVENT.MERIDIEN'],
                        compute=wind_speed_from_components),

               'Wind_Gust':
                   # Wind gust name has changed few years ago
                   dict(fa_fields_required=['CLSU.RAF60M.XFU', 'CLSV.RAF60M.XFU', 'CLSU.RAF.MOD.XFU', 'CLSV.RAF.MOD.XFU'],
                        compute=wind_gust),

               'Wind_DIR':
                   dict(fa_fields_required =['CLSVENT.ZONAL', 'CLSVENT.MERIDIEN'],
                        compute=wind_direction_from_components),

               'PSurf':
                   dict(fa_fields_required=['SURFPRESSION'],
                        compute=Psurf,
                        details="Surface pressure"),

               'ZS':
                   dict(fa_fields_required=['SPECSURFGEOPOTEN'],
                        compute=zs,
                        details="Surface elevation. "
                                "This variable is added once to the netcdf: during the first forecast term"),

               'Rainf':
                   dict(fa_fields_required=['SURFACCPLUIE'],
                        compute=cumul),
               'Grauf':
                   dict(fa_fields_required=['SURFACCGRAUPEL'],
                        compute=cumul),

               'LWdown':
                    dict(fa_fields_required=['SURFRAYT THER DE'],
                         compute=cumul),

               'DIR_SWdown':
                    dict(fa_fields_required=['SURFRAYT DIR SUR'],
                         compute=cumul),

               'Snowf':
                    dict(fa_fields_required=['SURFACCNEIGE', 'SURFACCGRAUPEL'],
                         compute=cumul_snow_graupel,
                         detail="Snowfall = snow + graupel"),

               'SCA_SWdown':
                   dict(fa_fields_required=['SURFRAYT SOLA DE', 'SURFRAYT DIR SUR'],
                        compute=SCA_SWdown),

               }


def _get_terms_from_input_user():
    """
    Input = config file from user
    Output = tuple(initial_term, list of terms)
    """
    # todo implement this function
    pass


def _get_domain_from_input_user():
    # todo implement this function
    pass


def _get_dates_of_simulation_from_input_user():
    """
    Input: user file
    Output: dates
    """
    # todo implement this function
    pass


def _get_variable_to_extract_from_input_user():
    # todo implement this function
    pass


def select_namespace():
    # todo clean this implementation
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


def _get_vortex_ressource():
    """This function search for existing ressource description and get it using epygram"""
    # todo implement this function

    resource_description = dict(experiment='B6LR',  # oper suite
                                kind='analysis',  # model state
                                block='surfan',
                                date=date + datetime.timedelta(hours=30),
                                # Next day is used since the analysis is done between D-1 6 and D 6
                                term=6,
                                geometry='franmgsp',  # the name of the model domain
                                local=nom_temporaire_local_ana,  # the local filename of the resource, once fetched.
                                cutoff='assim',  # type of cutoff // 'prod' vs 'assim'
                                vapp='arome',  # type of application in operations namespace
                                vconf='france',  # name of config in operation namespace
                                model='arome',  # name of the model, usually = vapp
                                origin='canari',
                                namespace=namespace2)

    r1 = \
        usevortex.get_resources(getmode='epygram',  # on veut récupérer l'objet epygram correspondant à la ressource
                                **resource_description)[0]
    pass


def get_input_user():
    dates = _get_dates_of_simulation_from_input_user()
    initial_term, terms = _get_terms_from_input_user()
    domain = _get_domain_from_input_user()
    variables_to_extract = _get_variable_to_extract_from_input_user()

    return dates, initial_term, domain, variables_to_extract


dates, initial_term, terms, domain, variables_to_extract = get_input_user()


# extract simulation at ay -1 and between end_term-1 and end_term
# first file is FORCING_day_alp_2020060206_2020060206.nc
# next files are FORCING_day_alp_20200*0*07_20200*0*06.nc
init_daily_netcdf_file()
initial_vortex_ressource = get_vortex_ressource(date-1 day, end_term-1)
create_first_hour_netcdf(initial_vortex_ressource)


stored_data = defaultdict() # we need this variable for cumulative fields where we need a memory of the previous time step
for idx_date, date in enumerate(dates):
    init_daily_netcdf_file()
    for idx_term, term in enumerate(terms):
        vortex_ressource = get_vortex_ressource(date, term) # Load vortex file once then extract variables
        for name_variable_nc in variables_to_extract:
            infos = dict_name_nc[name_variable_nc]
            hourly_array = infos['compute'](vortex_ressource, *infos["fa_fields_required"], domain,
                                     term=term, initial_term=initial_term, stored_data=stored_data)
            add_hourly_array_to_netcdf(name_variable_nc, hourly_array)
    add_SURFEX_metadata_to_nc()



# Input from the user
"""
01/01/2018
02/01/2018
Tair
humidity
rayonnement,
vent
"""