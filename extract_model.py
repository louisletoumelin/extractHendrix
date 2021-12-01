# standard library imports
from collections import defaultdict

# local imports (todo remove the "import *" later)
from netcdf import *
from post_process import *
from input_user import *
from utils import *

#todo implement "details" bellow, inspired from text in the AROME variable database (description of the variables)
dict_name_nc = {

               'Tair':
                   dict(fa_fields_required=['CLSTEMPERATURE'],
                        compute=default,
                        details="Diagnostic temperature"),
               'T1':
                   dict(fa_fields_required=['S090TEMPERATURE'],
                        compute=default,
                        details="Prognostic lowest level temperature"),

               # todo 1/3: Isabelle used the prognostic humidity and stored it in Qair. Now prognostic humidity is Q1. We
               # 2/3: should create a function that put the values of Q1 inside Qair when the user desires
               # 3/3: prognostic humidity to force SURFEX
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


dates, initial_term, terms, domain, variables_to_extract = get_input_user()
check_if_files_are_already_downloaded_at_CEN()

# extract simulation at ay -1 and between end_term-1 and end_term
# first file is FORCING_day_alp_2020060206_2020060206.nc
# next files are FORCING_day_alp_20200*0*07_20200*0*06.nc
netcdf_resource = init_daily_netcdf_file()
initial_vortex_ressource = get_vortex_ressource()
for name_variable_nc in variables_to_extract:
    infos = dict_name_nc[name_variable_nc]
    field = infos['compute'](vortex_ressource, *infos["fa_fields_required"], domain,
                             term=term, initial_term=initial_term, stored_data=stored_data)
    add_hourly_field_to_netcdf(name_variable_nc, field)


stored_data = defaultdict() # we need this variable for cumulative fields where we need a memory of the previous time step
try:
    for idx_date, date in enumerate(dates):
        init_daily_netcdf_file()
        for idx_term, term in enumerate(terms):

            # for Hugo: I think we can "readfields" instead of "readfield", see in the doc,
            #  meaning that we can access many variables at once... If we implement it we should modify our code
            # http://www.umr-cnrm.fr/gmapdoc/meshtml/EPYGRAM1.4.3/_modules/epygram/base.html#Field

            vortex_ressource = get_vortex_ressource(date, term) # Load vortex file once then extract variables
            # Maybe storing each fields in a dictionary is necessary?
            for name_variable_nc in variables_to_extract:

                infos = dict_name_nc[name_variable_nc]

                field = infos['compute'](vortex_ressource, *infos["fa_fields_required"], domain,
                                         term=term, initial_term=initial_term, stored_data=stored_data)

                add_hourly_field_to_netcdf(name_variable_nc, field)

        add_SURFEX_metadata_to_netcdf()
except:
    send_a_mail_if_extraction_stopped()