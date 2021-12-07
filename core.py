import os
from datetime import datetime, timedelta
from collections import defaultdict
import configparser
import uuid

import numpy as np
import xarray as xr

import usevortex
import epygram
from config_fa2nc import transformations, domains, alternatives_names_fa
from post_processing_functions import *

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
delta_terms = 1

def get_resource_from_hendrix(analysis_time, model_name, term, workdir=None):
    resource_description = dict(
        **get_model_description(model_name),
        date=analysis_time,
        term=term,
        local=os.path.join(workdir, 'tmp_file.fa')
    )

    resource = usevortex.get_resources(getmode='epygram', **resource_description)[0]
    resource = resource[0] if isinstance(resource, list) else resource

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
    Drop this file on Hendrix, in the folder DemandeMig/ChargeEnEspaceRapide \
    \nYou can use FileZilla with your computer, or ftp to drop the file.\n\n2. \
    Rename the extension of the file '.txt' (once it is on Hendrix) with '.MIG'\n\
    'request_prestaging_*.txt'  => 'request_prestaging_.MIG'\n\n\
    Note: don't rename in '.MIG' before dropping the file on Hendrix, or Hendrix could launch prestaging\
    before the file is fully uploaded\n\n3. \
    Please wait for an email from the Hendrix team to download your data\n\n"
    print(info_prestaging)


class HendrixConductor:

    def __init__(self, getter, folder, model_name, analysis_time, domain, variables_nc):
        self.folder = folder
        self.analysis_time = analysis_time
        self.getter = getter
        self.model_name = model_name
        self.domain = domains[domain]
        self.transformations = {
                key: value
                for key, value in transformations.items()
                if key in variables_nc}
        self.cache_folder = self.generate_name_of_cache_folder()
        self.variables_fa = self.get_fa_variables_names()

    def generate_name_of_cache_folder(self):
        random_key = str(uuid.uuid4())[:10]
        hashcache = "%s-%s" % (self.analysis_time.strftime('%Y-%m-%d_%H'), random_key)

        return os.path.join(self.folder, str(self.model_name) + hashcache)

    def get_compute_function(self, variable_nc):
        name_compute_function = self.transformations[variable_nc]['compute']
        return globals().get(name_compute_function)

    def post_process(self, input_dict, output_dict, term, **kwargs):
        """Post-process numpy arrays in dict_data (i.e. decumul, wind speed from components...)"""
        for variable_nc in self.transformations:

            compute = self.get_compute_function(variable_nc)
            name_variables_fa = self.transformations[variable_nc]['fa_fields_required']
            output_dict[variable_nc]["dims"] = ('time', 'yy', 'xx')
            if compute is not None:
                variable_array = compute(input_dict, term, *name_variables_fa, **kwargs)
                output_dict[variable_nc]["data"].append(variable_array)
            else:
                output_dict[variable_nc]["data"].append(input_dict[name_variables_fa])

        return output_dict

    def generate_name_output_netcdf(self, start_term, end_term):
        str_analysis_time = self.analysis_time.strftime("%Y%m%d")
        str_time = str_analysis_time + f"_{start_term}h_to_" + str_analysis_time + f"_{end_term}h.nc"
        return f"{self.model_name}_" + str_time

    def dict_to_netcdf(self, post_processed_data, start_term, end_term):

        filename_nc = self.generate_name_output_netcdf(start_term, end_term)
        dataset = xr.Dataset.from_dict(post_processed_data)

        # Create a time variable
        time = self.open_times_fa_in_txt_file()
        dataset["time"] = (('time'), time[1:])
        dataset.to_netcdf(os.path.join(self.folder, filename_nc))

    def process_daily(self, start_term, end_term, **kwargs):

        for term in range(start_term-1, end_term+1):
            self._epygram2netcdf(term)

        dict_data = self.readDataFromCache(start_term, end_term)

        post_processed_data = defaultdict(lambda: defaultdict(list))

        for term in range(start_term, end_term+1):
            post_processed_data = self.post_process(dict_data, post_processed_data, term, **kwargs)

        self.dict_to_netcdf(post_processed_data, start_term, end_term)

        return post_processed_data

    def get_fa_variables_names(self):
        variables_fa = []
        for value in self.transformations.values():
            variables_fa.extend(value["fa_fields_required"])
        return list(set(variables_fa))

    def get_netcdf_in_cache_filename(self, term):
        """
        On écrit les 24 fichiers netcdf temporaires dans des fichiers, avec une fonction qui donne
        leur nom c'est beaucoup plus facile de les écrire et de les récupérer
        """
        analysis_time_str = self.analysis_time.strftime('%Y-%m-%d-%Hh')
        netcdf_filename = "%s_ana_%s_term_%s.nc"%(self.model_name, analysis_time_str, term)
        return os.path.join(self.cache_folder, netcdf_filename)

    def create_cache_folder_if_doesnt_exist(self):
        if not os.path.exists(self.cache_folder):
            os.mkdir(self.cache_folder)

    @staticmethod
    def transform_spectral_field_if_required(field):
        if field.spectral:
            field.sp2gp()
        return field

    @staticmethod
    def pass_fa_metadata_to_netcdf(field):
        field.fid['netCDF'] = field.fid['FA']
        return field

    def extract_domain_pixels(self, field):
        field = field.extract_subarray(
            self.domain['first_i'],
            self.domain['last_i'],
            self.domain['first_j'],
            self.domain['last_j']
        )
        return field

    def write_time_fa_in_txt_file(self, field):
        with open(os.path.join(self.cache_folder, "times.txt"), "a+") as t:
            time_in_fa_file = field.validity[0].get()
            t.write(time_in_fa_file.strftime("%Y/%m/%d_%H:%M:%S")+"\n")

    def open_times_fa_in_txt_file(self):
        with open(os.path.join(self.cache_folder, "times.txt"), "r") as t:
            list_times = []
            for line in t:
                time = datetime.strptime(line[:-1], "%Y/%m/%d_%H:%M:%S")
                list_times.append(np.datetime64(time))
        return np.array(list_times)

    @staticmethod
    def read_epygram_field(input_resource, variable):
        initial_name = variable

        try:

            field = input_resource.readfield(variable)
            return field

        except AssertionError:

            print("Problem detected in variable name")

            if variable in alternatives_names_fa:
                alternatives_names = alternatives_names_fa[variable]

                while alternatives_names:
                    try:
                        variable = alternatives_names.pop(0)
                        field = input_resource.readfield(variable)
                        field.fid["FA"] = initial_name
                        print(f"Warning: found an alternative name for {initial_name}: {variable}")
                        return field
                    except AssertionError:
                        pass
                raise
            else:
                raise

    def _epygram2netcdf(self, term):
        """
        Fabrication des fichiers netcdf temporaires (1 par échéance)
        """
        self.create_cache_folder_if_doesnt_exist()
        input_resource = self.getter(self.analysis_time, self.model_name, term, workdir=self.folder)
        output_resource = epygram.formats.resource(self.get_netcdf_in_cache_filename(term), 'w', fmt='netCDF')
        # TODO: vérifier que c'est toujours ça qu'on veut
        # (par exemple la dimension 'Number_of_points' peut-être pas nécessaire pour Arome
        output_resource.behave(N_dimension='Number_of_points', X_dimension='xx', Y_dimension='yy')
        for variable in self.variables_fa:
            field = self.read_epygram_field(input_resource, variable)
            field = self.pass_fa_metadata_to_netcdf(field)
            field = self.transform_spectral_field_if_required(field)
            field = self.extract_domain_pixels(field)
            output_resource.writefield(field)

        self.write_time_fa_in_txt_file(field)

    def readDataFromCache(self, start_term, end_term):
        """
        Lire dans le "cache" (le cache c'est le dossier ou on a placé tous nos netCDF), les netCDF pour en extraire les différentes variables dans un dictionnaire, de structure:
        {6: {variable1: tableau_numpy, variable2: tableau_numpy},
        7: {variable1: tableau_numpy, variable2: tableau_numpy},
        8: {variable1: tableau_numpy, variable2: tableau_numpy}
        .........
        }
        ou 6,7,8 sont les "terms"
        variable1, variable2 sont les éléments de la liste "variables".
        """
        dict_data = defaultdict(lambda: defaultdict(dict))
        for term in range(start_term-1, end_term+1):
            filename = self.get_netcdf_in_cache_filename(term)
            nc_file = xr.open_dataset(filename)
            dict_from_xarray = nc_file.to_dict()
            for variable in self.variables_fa:
                dict_data[term][variable] = np.array(dict_from_xarray["data_vars"][variable]["data"])
        return dict_data

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
