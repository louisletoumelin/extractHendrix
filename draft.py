import os
from datetime import datetime, timedelta
from collections import defaultdict

import numpy as np
import xarray as xr

import usevortex
import epygram

"""
Fonctions:
    - lecture d'un FA (un modèle, une date d'analyse, une date d'échéance, une sous-grille) et écriture dans un netcdf
        (ne pas se prendre la tête tout de suite avec les grilles qui peuvent être différentes)
    * génération d'un nom de fichier à partir d'une date d'analyse, d'une date d'échéance et d'un modèle (toutes les fonctions qui lisent, écrivent dans le cache utilisent cette fonction pour nommer)
    - lecture de la valeur d'une variable dans le cache à partir de analyse, échéance, modèle, nom de la variable
        Proposition: commencer par la méthode la plus bourrine (et la plus simple), affiner si ça pose des problèmes en termes de performance
    - fonction qui lit la valeur de toutes les variables dans le cache pour toutes les échéances données (et une date d'analyse) et les stocke dans un dictionnaire (clé: date)
    - fonction renvoyant la valeur d'une variable à un instant t depuis le "cache"
    - les fonctions définies par l'utilisateur utilisent cette fonction pour lire les valeurs
"""
# l'idée c'est de décrire le modèle, sans la date d'analyse, l'échéance et le nom du fichier, on les rajouter ensuite dans


dict_name_nc = {

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

model_description = dict(suite='oper',  # oper suite
                         kind='historic',  # model state
                         # the initial date and time
                         geometry='franmgsp',  # the name of the model domain
                         cutoff='prod',  # type of cutoff // 'prod' vs 'assim'
                         vapp='arome',  # type of application in operations namespace
                         vconf='3dvarfr',  # name of config in operation namespace
                         model='arome',  # name of the model, usually = vapp
                         namespace='oper.archive.fr',
                         block='forecast',
                         experiment='oper')

class ReaderWriter:
    # note: faire une classe serait vraiment bien ça permettrait de ne pas avoir à passer en argument folder,
    # variables, model_name, analysis_time  à toutes les fonctions (avec les risques d'incohérences que ça comporte)

    def __init__(self, folder, model_name, analysis_time, domain, variables_nc):
        self.folder = folder
        self.model_name = model_name
        self.analysis_time = analysis_time
        self.domain = domain
        self.variables_nc = variables_nc # Variables données par l'utilisateur (nom en netcdf, ex: Tair)
        self.variables_fa = self._nameNC2nameFA(dict_name_nc)

    def _nameNC2nameFA(self, dict_name_nc):
        variables_fa = []
        for variable_nc in self.variables_nc:
            variables_fa.extend(dict_name_nc[variable_nc]["fa_fields_required"])
        return variables_fa

    def _get_filename(self, step):
        """
        On écrit les 24 fichiers netcdf temporaires dans des fichiers, avec une fonction qui donne
        leur nom c'est beaucoup plus facile de les écrire et de les récupérer
        """
        analysis_time_str = self.analysis_time.strftime('%Y-%m-%d-%Hh')
        return os.path.join(self.folder, "%s_ana:%s_step:%s.nc"%(self.model_name, analysis_time_str, step))

    def get_resource_from_hendrix(self, model_description, step):
        resource_description = dict(
                **model_description,
                date=self.analysis_time,
                term=step,
                local='tmp_file.fa')
        resource = usevortex.get_resources(getmode='epygram', **resource_description)
        return resource

    def _extract_domain(self, field):

       """
       Extract field over a specific area.
       The indexes correspond to the AROME 1.3 km grid.
       """

       if self.domain =='alp':
          first_i = 900
          last_i = 1075
          first_j = 525
          last_j = 750
       elif self.domain=='pyr':
          first_i = 480
          last_i = 785
          first_j = 350
          last_j = 475
       elif self.domain=='test_alp':
          first_i = 1090
          last_i = 1100
          first_j = 740
          last_j = 750
       elif self.domain=='jesus':
           first_i=551
           last_i=593
           first_j=414
           last_j=435

       fld_zoom = field.extract_subarray(first_i, last_i, first_j, last_j)
       return fld_zoom

    def epygram2netcdf(self, epygram_resource, step):
        """
        Fabrication des fichiers netcdf temporaires (1 par heure)
        folder: le dossier de destination (ça pourrait se factoriser en faisant une classe mais on va d'abord faire
        des fonctions qui marchent pour toutes les étapes et on verra ensuite pour en faire des méthodes)
        """
        output_resource = epygram.formats.resource(self._get_filename(step), 'w', fmt='netCDF')
        # TODO: vérifier que c'est toujours ça qu'on veut
        # (par exemple la dimension 'Number_of_points' peut-être pas nécessaire pour Arome
        output_resource.behave(N_dimension='Number_of_points',
                           X_dimension='xx',
                           Y_dimension='yy'
                           )
        for variable in self.variables_fa:
            field = epygram_resource.readfield(variable)

            field.fid['netCDF'] = field.fid['FA']
            if field.spectral:
                field.sp2gp()

            # Il vaut mieux extraire le domaine maintenant, comme ca on stocke des netcdf beaucoup plus petits
            field = self._extract_domain(field)

            output_resource.writefield(field)

        #os.remove(os.path.join(self.folder, 'tmp_file.fa'))

    def readDataFromCache(self, stepmin, stepmax):
        """
        Lire dans le "cache" (le cache c'est le dossier ou on a placé tous nos netCDF), les netCDF pour en extraire les différentes variables dans un dictionnaire, de structure:
        {6: {variable1: tableau_numpy, variable2: tableau_numpy},
        7: {variable1: tableau_numpy, variable2: tableau_numpy},
        8: {variable1: tableau_numpy, variable2: tableau_numpy}
        .........
        }
        ou 6,7,8 sont les "steps"
        variable1, variable2 sont les éléments de la liste "variables".

        Louis: je l'ai testé sur 3 steps et ça marche
        """
        dict_data = defaultdict(lambda: defaultdict(dict))
        for step in range(stepmin-1, stepmax+1):
            # step-1 car on veut une heure avant le début pour les cumuls
            # step+1 car on veut que stepmax soit lu
            filename = self._get_filename(step)
            nc_file = xr.open_dataset(filename)
            dict_from_xarray = nc_file.to_dict()
            for variable in self.variables_fa:
                dict_data[step][variable] = np.array(dict_from_xarray["data_vars"][variable]["data"])

        return dict_data

    @staticmethod
    def read_dict(dict_data, step, variable):
        """
        sur le plan esthétique, mais je préfère appeler read(data, 'TEMPERATURE', 2)
        que data[2]['TEMPERATURE']
        et si on décide à l'avenir que notre façon de lire les données est pas terrible, il suffira de modifier cette fonction

        Louis: j'ai testé et ça marche
        """
        return dict_data[step][variable]

    # note: la forme des fonctions compute souhaitée
    def compute_decumul(self, dict_data, term, name_variable_FA):
        """
        Calcule le décumul pour l'échéance term
        (on est obligé de mettre term dans les paramètres pour pouvoir gérer le cas des cumuls)

        # Conversion: - from mm to kg/m2/s for precip
        #              - from J/m2 to W/m2 for incoming LW and SW

        Louis: j'ai testé et ça marche
        """
        return self.read_dict(dict_data, term, name_variable_FA) - self.read_dict(dict_data, term -1, name_variable_FA)


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


if __name__ == '__main__':
    # Chez moi ça fonctionne
    folder = '/cnrm/cen/users/NO_SAVE/letoumelinl/extractHendrix/folder'
    model_name = 'AROME'
    analysis_time = datetime(2019, 5, 1, 0)
    domain = "alp"
    variables = ['Tair', 'T1']
    r = ReaderWriter(folder, model_name, analysis_time, domain, variables)

    terms = range(5, 8)

    for term in terms:
        resource = r.get_resource_from_hendrix(model_description, term)[0]
        r.epygram2netcdf(resource, term)

    dict_data = r.readDataFromCache(6, 7)

    r.compute_decumul(dict_data, 6, 'CLSTEMPERATURE')
    r.compute_psurf(dict_data, 6, 'CLSTEMPERATURE')
    r.compute_zs(dict_data, 6, 'CLSTEMPERATURE')
    r.compute_snow(dict_data, 6, 'CLSTEMPERATURE', 'S090TEMPERATURE')
    r.compute_SCA_SWdown(dict_data, 6, 'CLSTEMPERATURE', 'S090TEMPERATURE')




"""
# reste l'écriture du netCDF final pas le temps de décrire mais ça devrait le faire
if __name__ == '__main__':
    # "tests"
    resource = epygram.formats.resource(filename='/home/merzisenh/NO_SAVE/AROME/AROME_ana:2019-05-01-00h_step:0',
                                        getmode='epygram',
                                        openmode='r')
    folder = '/home/merzisenh'
    model_name = 'AROME'
    analysis_time = datetime(2019, 5, 1, 0)
    variables = ['SURFTEMPERATURE', 'CLSTEMPERATURE']
    step = 1
    domain = "alps"
    epygram2netcdf(resource, domain, folder, model_name, variables, analysis_time, step)
"""
