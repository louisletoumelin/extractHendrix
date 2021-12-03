import os
from datetime import datetime, timedelta
from collections import defaultdict
import configparser
import uuid

import numpy as np
import xarray as xr

import usevortex
import epygram
from config_fa2nc import transformations

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


def get_resource_from_hendrix(analysis_time, model_name, term, workdir=None):
    resource_description = dict(
        **get_model_description(model_name),
        date=analysis_time,
        term=term,
        local=os.path.join(workdir, 'tmp_file.fa')
    )
    resource = usevortex.get_resources(getmode='epygram', **resource_description)
    return resource


def date_iterator(date_start, date_end):
    """Return a generator containing a range of dates"""
    current_date = date_start - timedelta(1)
    while current_date < date_end:
        current_date += timedelta(1)
        yield current_date


def get_model_description(model_name):
    config = configparser.ConfigParser()
    config.read('models.ini')
    return dict(config[model_name])


def prepare_prestaging_demand(date_start, date_end, email_address, getter, terms,
                              folder, model_name, domain, variables_nc):
    """Creates a 'request_prestaging_*.txt' file containing all the necessary information for prestagging"""
    dates = date_iterator(date_start, date_end)

    begin_str = date_start.strftime("%m/%d/%Y").replace('/', '_')
    end_str = date_end.strftime("%m/%d/%Y").replace('/', '_')
    mail_str = email_address.split("@")[0].replace('.', '_')

    filename = f"request_prestaging_{mail_str}_{model_name}_begin_{begin_str}_end_{end_str}.txt"

    with open(filename, "w+") as f:
        f.write(f"#MAIL={email_address}\n")
        for date in dates:
            hc = HendrixConductor(getter, folder, model_name, date, domain, variables_nc)
            for term in terms:
                resource = hc.get_path_vortex_ressource(term)[0]
                f.write(resource.split(':')[1] + "\n")

    info_prestaging = "\n\nPlease find below the procedure for prestaging. \
    Note a new file named 'request_prestaging_*.txt' has been created on your current folder\n\n1. \
    Drop the file 'request_prestaging_*.txt' on Hendrix, in the folder DemandeMig/ChargeEnEspaceRapide \
    \nYou can use FileZilla with your computer, or ftp for exemple.\n\n2. \
    Rename the extension fo the file (once it is on Hendrix) with MIG\n\
    'request_prestaging_*.txt'  => 'request_prestaging_.MIG'\n\n\
    Note: don't rename in .MIG before dropping the file on Hendrix, or Hendrix could launch prestagging \
    before the file is fully uploaded\n\n3. \
    Please wait for an email from the Hendrix team to download your data\n\n"
    print(info_prestaging)


class HendrixConductor:

    def __init__(self, getter, folder, model_name, analysis_time, domain, variables_nc):
        self.folder = folder
        hashcache = "%s-%s"%(
                analysis_time.strftime('ana_%Y-%m-%d_%Hh'),
                str(uuid.uuid4())[:10]
                )
        self.cache_folder = os.path.join(folder, hashcache)
        self.getter = getter
        self.model_name = model_name
        self.analysis_time = analysis_time
        self.domain = domain
        self.transformations = {
                key: value
                for key, value in transformations.items()
                if key in variables_nc}
        self.variables_fa = self._get_fa_variables_names()

    def process(self):

        for term in range(1, 12):
            self._epygram2netcdf(term)
        data = self.readDataFromCache(2, 10)

    def _get_fa_variables_names(self):
        variables_fa = []
        for value in self.transformations.values():
            variables_fa.extend(value["fa_fields_required"])
        return list(set(variables_fa))

    def _get_cache_filename(self, term):
        """
        On écrit les 24 fichiers netcdf temporaires dans des fichiers, avec une fonction qui donne
        leur nom c'est beaucoup plus facile de les écrire et de les récupérer
        """
        analysis_time_str = self.analysis_time.strftime('%Y-%m-%d-%Hh')
        return os.path.join(self.cache_folder, "%s_ana_%s_term_%s.nc"%(self.model_name, analysis_time_str, term))

    def _epygram2netcdf(self, term):
        """
        Fabrication des fichiers netcdf temporaires (1 par échéance)
        """
        if not os.path.exists(self.cache_folder):
            os.mkdir(self.cache_folder)
        input_resource = self.getter(self.analysis_time, self.model_name, term, workdir=self.folder)
        output_resource = epygram.formats.resource(self._get_cache_filename(term), 'w', fmt='netCDF')
        # TODO: vérifier que c'est toujours ça qu'on veut
        # (par exemple la dimension 'Number_of_points' peut-être pas nécessaire pour Arome
        output_resource.behave(N_dimension='Number_of_points',
                           X_dimension='xx',
                           Y_dimension='yy'
                           )
        for variable in self.variables_fa:
            field = input_resource.readfield(variable)

            field.fid['netCDF'] = field.fid['FA']
            if field.spectral:
                field.sp2gp()

            field_domain = field.extract_subarray(
                    self.domain['first_i'],
                    self.domain['last_i'],
                    self.domain['first_j'],
                    self.domain['last_j']
                    )

            output_resource.writefield(field_domain)

        with open(self.cache_folder + "times.txt", "a+") as t:
            t.write(field.validity[0].getbasis().strftime("%m/%d/%Y"))

    def readDataFromCache(self, termmin, termmax):
        """
        Lire dans le "cache" (le cache c'est le dossier ou on a placé tous nos netCDF), les netCDF pour en extraire les différentes variables dans un dictionnaire, de structure:
        {6: {variable1: tableau_numpy, variable2: tableau_numpy},
        7: {variable1: tableau_numpy, variable2: tableau_numpy},
        8: {variable1: tableau_numpy, variable2: tableau_numpy}
        .........
        }
        ou 6,7,8 sont les "terms"
        variable1, variable2 sont les éléments de la liste "variables".

        Louis: je l'ai testé sur 3 terms et ça marche
        """
        dict_data = defaultdict(lambda: defaultdict(dict))
        for term in range(termmin-1, termmax+1):
            # term-1 car on veut une heure avant le début pour les cumuls
            # term+1 car on veut que termmax soit lu
            filename = self._get_cache_filename(term)
            nc_file = xr.open_dataset(filename)
            dict_from_xarray = nc_file.to_dict()
            for variable in self.variables_fa:
                dict_data[term][variable] = np.array(dict_from_xarray["data_vars"][variable]["data"])
        return dict_data

    @staticmethod
    def read_dict(dict_data, term, variable):
        """
        sur le plan esthétique, mais je préfère appeler read(data, 'TEMPERATURE', 2)
        que data[2]['TEMPERATURE']
        et si on décide à l'avenir que notre façon de lire les données est pas terrible, il suffira de modifier cette fonction

        Louis: j'ai testé et ça marche
        """
        return dict_data[term][variable]

    def get_path_vortex_ressource(self, term):
        resource_description = dict(
                **get_model_description(self.model_name),
                date=self.analysis_time,
                term=term,
                local='tmp_file.fa')
        return usevortex.get_resources(getmode='locate', **resource_description)



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
    resource = epygram.formats.resource(filename='/home/merzisenh/NO_SAVE/AROME/AROME_ana:2019-05-01-00h_term:0',
                                        getmode='epygram',
                                        openmode='r')
    folder = '/home/merzisenh'
    model_name = 'AROME'
    analysis_time = datetime(2019, 5, 1, 0)
    variables = ['SURFTEMPERATURE', 'CLSTEMPERATURE']
    term = 1
    domain = "alps"
    epygram2netcdf(resource, domain, folder, model_name, variables, analysis_time, term)
"""
