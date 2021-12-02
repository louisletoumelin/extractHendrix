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


def get_filename(folder, model_name, analysis_time, step):
    """
    On écrit les 24 fichiers netcdf temporaires dans des fichiers, avec une fonction qui donne
    leur nom c'est beaucoup plus facile de les écrire et de les récupérer
    """
    analysis_time_str = analysis_time.strftime('%Y-%m-%d-%Hh')
    return os.path.join(folder, "%s_ana:%s_step:%s.nc"%(model_name, analysis_time_str, step))


# l'idée c'est de décrire le modèle, sans la date d'analyse, l'échéance et le nom du fichier, on les rajouter ensuite dans 
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


def get_resource_from_hendrix(folder, model_description, model_name, analysis_time, term):
    resource_description = dict(
            **model_description,
            date= analysis_time,
            term=term,
            local= 'tmp_file.fa' # a priori on se fiche du nom du fichier fa on a un pointeur dessus avec resource
            # ils vont sécrire les uns sur les autres
            )
    resource = usevortex.get_resources(getmode='epygram', **resource_description)
    return resource


def extract_domain(field, domain):

   """
   Extract field over a specific area.
   The indexes correspond to the AROME 1.3 km grid.
   """

   if domain =='alp':
      first_i = 900
      last_i = 1075
      first_j = 525
      last_j = 750
   elif domain=='pyr':
      first_i = 480
      last_i = 785
      first_j = 350
      last_j = 475
   elif domain=='test_alp':
      first_i = 1090
      last_i = 1100
      first_j = 740
      last_j = 750
   elif domain=='jesus':
       first_i=551
       last_i=593
       first_j=414
       last_j=435

   fld_zoom = field.extract_subarray(first_i, last_i,
                        first_j, last_j)
   return (fld_zoom)


def epygram2netcdf(epygram_resource, domain, folder, model_name, variables, analysis_time, step):
    """
    Fabrication des fichiers netcdf temporaires (1 par heure)
    folder: le dossier de destination (ça pourrait se factoriser en faisant une classe mais on va d'abord faire
    des fonctions qui marchent pour toutes les étapes et on verra ensuite pour en faire des méthodes)
    """
    output_resource = epygram.formats.resource(
            get_filename(folder, model_name, analysis_time, step),
            'w',
            fmt='netCDF')
    # TODO: vérifier que c'est toujours ça qu'on veut
    # (par exemple la dimension 'Number_of_points' peut-être pas nécessaire pour Arome
    output_resource.behave(N_dimension='Number_of_points',
                       X_dimension='xx',
                       Y_dimension='yy'
                       )
    for variable in variables:
        field = epygram_resource.readfield(variable)
        # Il vaut mieux extraire le domaine maintenant, comme ca on stocke des netcdf beaucoup plus petits
        field = extract_domain(field, domain)
        field.fid['netCDF'] = field.fid['FA']
        if field.spectral:
            field.sp2gp()
        output_resource.writefield(field)


def readDataFromCache(analysis_time, folder, model_name, stepmin, stepmax, variables):
    """
    Lire dans le "cache" (le cache c'est le dossier ou on a placé tous nos netCDF), les netCDF pour en extraire les différentes variables dans un dictionnaire, de structure:
    {6: {variable1: tableau_numpy, variable2: tableau_numpy},
    7: {variable1: tableau_numpy, variable2: tableau_numpy},
    8: {variable1: tableau_numpy, variable2: tableau_numpy}
    .........
    }
    ou 6,7,8 sont les "steps"
    variable1, variable2 sont les éléments de la liste "variables".
    """
    dict_variables = defaultdict(lambda: defaultdict(dict))
    for step in range(stepmin-1, stepmax+1):
        # step-1 car on veut une heure avant le début pour les cumuls
        # step+1 car on veut que stepmax soit lu
        filename = get_filename(folder, model_name, analysis_time, step)
        nc_file = xr.open_dataset(filename)
        dict_from_xarray = nc_file.to_dict()
        for variable in variables:
            dict_variables[str(step)][variable] = np.array(dict_from_xarray["data_vars"][variable]["data"])

    return dict_variables

# note: faire une classe serait vraiment bien ça permettrait de ne pas avoir à passer en argument folder, 
# variables, model_name, analysis_time  à toutes les fonctions (avec les risques d'incohérences que ça comporte)

def read_dict(data, variable, step):
    """
    sur le plan esthétique, mais je préfère appeler read(data, 'TEMPERATURE', 2)
    que data[2]['TEMPERATURE']
    et si on décide à l'avenir que notre façon de lire les données est pas terrible, il suffira de modifier cette fonction
    """
    return data[step][variable]


# note: la forme des fonctions compute souhaitée
def compute_decumul_rain(data, term):
    """
    Calcule le décumul de rain pour l'échéance term
    (on est obligé de mettre term dans les paramètres pour pouvoir gérer le cas des cumuls)
    """
    return read_dict(data, 'NOM.VORTEX.RAIN', term) - read_dict(data, 'NOM.VORTEX.RAIN', term -1)


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
    epygram2netcdf(resource, folder, model_name, variables, analysis_time, step)
