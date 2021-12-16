import os
from datetime import datetime, timedelta
from collections import defaultdict
import configparser
import uuid
import time
import sys
import shutil
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate

import numpy as np
import xarray as xr

import usevortex
import epygram
from config_fa2nc import transformations, domains, alternatives_names_fa
from post_processing_functions import *
from hendrix_emails import dict_with_all_emails

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


def timer_decorator(argument, unit='minute', level="__"):
    def decorator(function):
        def wrapper(*args, **kwargs):
            t0 = time.time()
            result = function(*args, **kwargs)
            t1 = time.time()
            if unit == "hour":
                time_execution = np.round((t1 - t0) / (3600), 2)
            elif unit == "minute":
                time_execution = np.round((t1-t0) / 60, 2)
            elif unit == "second":
                time_execution = np.round((t1 - t0), 2)
            print(f"{level}Time to calculate {argument}: {time_execution} {unit}s")
            return result
        return wrapper
    return decorator


def get_model_description(model_name):
    # todo give the path to models.ini
    config = configparser.ConfigParser()
    config.read('models.ini')
    return dict(config[model_name])


def get_name_from_email(email_address):
    return email_address.split("@")[0].replace('.', '_')


def _prepare_html(type_of_email, email_address, **kwargs):
    """Returns the subject of the mail (str) and the message (html)"""

    user = get_name_from_email(email_address)

    if type_of_email == "problem_extraction":

        kwargs_html = dict(
            user=user,
            error_message=kwargs.get("error_message"),
            time_of_problem=kwargs.get("time_of_problem"),
            resource_that_stopped=kwargs.get("resource_that_stopped"),
            folder=kwargs.get("folder"),
            nb_of_try=kwargs.get("nb_of_try"),
            time_waiting=kwargs.get("time_waiting"),
        )

    if type_of_email == "finished":

        kwargs_html = dict(
            user=user,
            config_user=kwargs.get("config_user"),
            current_time=kwargs.get("current_time"),
            time_to_download=kwargs.get("time_to_download"),
            errors=kwargs.get("errors"),
            folder=kwargs.get("folder"),
        )

    if type_of_email == "script_stopped":

        kwargs_html = dict(
            user=user,
            config_user=kwargs.get("config_user"),
            current_time=kwargs.get("current_time"),
            error=kwargs.get("error"),
            folder=kwargs.get("folder"),
        )

    html = dict_with_all_emails[type_of_email][1].format(**kwargs_html)
    return html


def send_email(type_of_email, email_address, **kwargs):
    server = smtplib.SMTP()
    server.connect('smtp.cnrm.meteo.fr')
    server.helo()

    from_addr = 'HendrixConductor <do_not_answer@hendrixconductor.fr>'
    to_addrs = email_address if isinstance(email_address, list) else [email_address]

    msg = MIMEMultipart('alternative')
    msg['From'] = from_addr
    msg['To'] = ','.join(to_addrs)
    msg["Date"] = formatdate(localtime=True)

    msg['Subject'] = dict_with_all_emails[type_of_email][0]
    html = _prepare_html(type_of_email, email_address, **kwargs)
    part = MIMEText(html, 'html')
    msg.attach(part)

    try:
        server.sendmail(from_addr, to_addrs, msg.as_string())
    except smtplib.SMTPException as e:
        print(f"Email {type_of_email} could not be launched. The error is: ")
        print(e)

    server.quit()


def callSystemOrDie(commande, errorcode=None):
    status = os.system(commande)
    if status != 0:

        if type(errorcode) is int:
            print("The following command fails with error code " + str(status) + ":\n" + commande)
            sys.exit(errorcode)
        else:
            sys.exit("The following command fails with error code " + str(status) + ":\n" + commande)
    return status


class Extractor:

    def __init__(self, config_user):
        self.getter = config_user.get("getter")
        self.folder = config_user.get("folder")
        self.model_name = config_user.get("model_name")
        self.analysis_time = config_user.get("analysis_time")
        self.domain = config_user.get("domain")
        self.variables_nc = config_user.get("variables_nc")
        self.date_start = config_user.get("date_start")
        self.date_end = config_user.get("date_end")
        self.email_address = config_user.get("email_address")
        self.start_term = config_user.get("start_term")
        self.end_term = config_user.get("end_term")
        self.final_concatenation = config_user.get("final_concatenation")
        self.errors = dict()
        self.config_user = config_user

    @staticmethod
    def date_iterator(date_start, date_end):
        """Return a generator containing a range of dates"""
        current_date = date_start - timedelta(1)
        while current_date < date_end:
            current_date += timedelta(1)
            yield current_date

    @staticmethod
    def get_year_and_month_between_dates(start, end):
        """
        date_start = datetime(2019, 10, 1, 0)
        date_end = datetime(2020, 2, 29, 0)
        # returns [(2019, 10), (2019, 11), (2019, 12), (2020, 1), (2020, 2)]
        get_year_and_month_between_dates(date_start, date_end)
        """
        total_months = lambda dt: dt.month + 12 * dt.year
        mlist = []
        for tot_m in range(total_months(start)-1, total_months(end)):
            y, m = divmod(tot_m, 12)
            mlist.append((datetime(y, m+1, 1).year, datetime(y, m+1, 1).month))
        return mlist

    @staticmethod
    def get_year_between_dates(start, end):
        """
        date_start = datetime(2019, 5, 1, 0)
        date_end = datetime(2020, 12, 3, 0)
        get_year_and_month_between_dates(date_start, date_end)
        # returns [2019]
        """
        total_months = lambda dt: dt.month + 12 * dt.year
        mlist = []
        for tot_m in range(total_months(start)-1, total_months(end)):
            y, m = divmod(tot_m, 12)
            mlist.append(datetime(y, m+1, 1).year)
        return list(set(mlist))

    def get_documentation(self):
        self.send_link_to_hendrix_documentation()
        print("\n\n")
        self.send_link_to_confluence_table_with_downloaded_data()
        print("\n\n")
        self.send_link_to_AROME_variables()

    def latlon2ij(self, ll_lat, ll_lon, ur_lat, ur_lon, term=5):
        """
        Input:
        ll_lat, ll_lon: lat and lon of lower left corner (ll)
        ur_lat, ur_lon: lat and lon of upper right corner (ur)

        Return:
        first_i, last_i, first_j, last_j
        """
        hc = HendrixConductor(self.getter, self.folder, self.model_name, self.date_start, self.domain, self.variables_nc, self.email_address)
        resource = hc.get_resource_from_hendrix(term)
        field = resource.readfield('CLSTEMPERATURE')
        x1, y1 = np.round(field.geometry.ll2ij(ll_lon, ll_lat)) + 1
        x2, y2 = np.round(field.geometry.ll2ij(ur_lon, ur_lat)) + 1
        return x1, x2, y1, y2

    @staticmethod
    def send_link_to_hendrix_documentation():
        print("The documentation of the storage system Hendrix is available here:")
        print("http://confluence.meteo.fr/pages/viewpage.action?pageId=299881305")

    @staticmethod
    def send_link_to_confluence_table_with_downloaded_data():
        link = "http://confluence.meteo.fr/pages/viewpage.action?pageId=314552092"
        print("\n[INFORMATION] Have you check that the data you request is not already downloaded at CEN?\n")
        print("Please see the link below")
        print(link)

    @staticmethod
    def send_link_to_AROME_variables():
        link = "http://intra.cnrm.meteo.fr/aromerecherche/spip.php?article25"
        print("Website with all AROME variables (might be outdated)")
        print(link)

    def concatenate_netcdf(self, list_daily_netcdf_files):

        try:
            dataset = xr.open_mfdataset([os.path.join(self.folder, file) for file in list_daily_netcdf_files])
        except:
            self.errors["concatenation"] = "Files are not concatenated with the desired final format \n" \
                                           "We could not read all file at once using xarray. " \
                                           "This is likely due to the fact that the number of point in your domain" \
                                           "varies with time (e.g. +/- 1 pixel)"
            return

        if self.final_concatenation == "month":
            self._concatenate_netcdf_by_year_and_month(dataset)
        elif self.final_concatenation == "year":
            self._concatenate_netcdf_by_year(dataset)
        elif self.final_concatenation == "all":
            self._concatenate_all_netcdf(dataset)
        else:
            return

    def _concatenate_netcdf_by_year_and_month(self, dataset):

        list_years_months = self.get_year_and_month_between_dates(self.date_start, self.date_end)

        for (year, month) in list_years_months:
            condition_month = dataset["time.month"] == month
            condition_year = dataset["time.year"] == year
            filename = os.path.join(self.folder, f"{self.model_name}_{self.domain}_{year}_{month}.nc")
            dataset.where(condition_month & condition_year, drop=True).to_netcdf(filename)

    def _concatenate_netcdf_by_year(self, dataset):

        list_years = self.get_year_between_dates(self.date_start, self.date_end)

        for year in list_years:
            condition_year = dataset["time.year"] == year
            filename = os.path.join(self.folder, f"{self.model_name}_{self.domain}_{year}.nc")
            dataset.where(condition_year, drop=True).to_netcdf(filename)

    def _concatenate_all_netcdf(self, dataset):
        start_str = self.date_start.strftime('%Y%m%d_%Hh')
        end_str = self.date_end.strftime('%Y%m%d_%Hh')
        filename = os.path.join(self.folder, f"{self.model_name}_{self.domain}_from_{start_str}_to_{end_str}.nc")
        dataset.to_netcdf(filename)

    def prepare_prestaging_demand(self):
        """Creates a 'request_prestaging_*.txt' file containing all the necessary information for prestagging"""
        dates = self.date_iterator(self.date_start, self.date_end)

        begin_str = self.date_start.strftime("%m/%d/%Y").replace('/', '_')
        end_str = self.date_end.strftime("%m/%d/%Y").replace('/', '_')
        name_str = get_name_from_email(self.email_address)

        filename = f"request_prestaging_{name_str}_{self.model_name}_begin_{begin_str}_end_{end_str}.txt"
        filename = os.path.join(self.folder, filename)

        with open(filename, "w+") as f:
            f.write(f"#MAIL={self.email_address}\n")
            for date in dates:
                hc = HendrixConductor(self.getter, self.folder, self.model_name, date, self.domain, self.variables_nc, self.email_address)
                for term in range(self.start_term, self.end_term):
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

        self.send_link_to_hendrix_documentation()

    def download(self):
        try:
            t0 = time.time()

            self.send_link_to_confluence_table_with_downloaded_data()

            dates = self.date_iterator(self.date_start, self.date_end)
            names_netcdf = []

            hc = HendrixConductor(self.getter, self.folder, self.model_name, self.date_start, self.domain, self.variables_nc, self.email_address)
            hc.download_daily_netcdf(self.start_term, self.start_term)
            names_netcdf.append(hc.generate_name_output_netcdf(self.start_term, self.start_term))

            for date in dates:
                print(date)
                hc = HendrixConductor(self.getter, self.folder, self.model_name, date, self.domain, self.variables_nc, self.email_address)
                hc.download_daily_netcdf(self.start_term+1, self.end_term)
                names_netcdf.append(hc.generate_name_output_netcdf(self.start_term+1, self.end_term))
            self.concatenate_netcdf(names_netcdf)

            send_email("finished", self.email_address,
                       config_user=str(self.config_user),
                       current_time=time.asctime(),
                       time_to_download=str(np.round((time.time()-t0) / 60, 2)),
                       errors=str(self.errors),
                       folder=self.folder)

        except Exception as e:
            send_email("script_stopped", self.email_address,
                       config_user=self.config_user,
                       current_time=time.asctime(),
                       error=e,
                       folder=self.folder)
            raise


class HendrixConductor:

    def __init__(self, getter, folder, model_name, analysis_time, domain, variables_nc, email_address):
        self.folder = folder
        self.analysis_time = analysis_time
        self.model_name = model_name
        self.domain = domains[domain]
        self.email_address = email_address
        self.transformations = {
                key: value
                for key, value in transformations.items()
                if key in variables_nc}
        self.getter = self.parse_getter(getter)
        self.cache_folder = self.generate_name_of_cache_folder()
        self.variables_fa = self.get_fa_variables_names()

    def parse_getter(self, getter):
        if getter == "hendrix":
            return self.get_resource_from_hendrix
        elif getter == "local":
            raise NotImplementedError("We need to implement a getter from local ressources")
        else:
            raise NotImplementedError

    def _get_resources_vortex(self, resource_description):
        i = 0
        while i < 10:
            try:
                return usevortex.get_resources(getmode='epygram', **resource_description)
            except Exception as e:
                print("An exception has occured when using usevortex.get_resources command")
                print(f"The exception raised is: {e}")
                print("Exception at this stage can occur if Hendrix server is not accessible")
                if i < 5:
                    thirty_minutes = 30 * 60
                    print("We will try accessing the resource again in 30 minutes")
                    print("Number of tries allowed: 10")
                    time.sleep(thirty_minutes)

                    send_email("problem_extraction", self.email_address,
                               user=get_name_from_email(self.email_address),
                               error_message=e,
                               time_of_problem=time.asctime(),
                               resource_that_stopped=str(resource_description),
                               folder=self.folder,
                               nb_of_try=str(i+1),
                               time_waiting=str(30))
                    i += 1
                elif 5 <= i < 9:
                    print("We will try accessing the resource again in 1h")
                    one_hour = 3600
                    time.sleep(one_hour)
                    send_email("problem_extraction", self.email_address,
                               user=get_name_from_email(self.email_address),
                               error_message=e,
                               time_of_problem=time.asctime(),
                               resource_that_stopped=str(resource_description),
                               folder=self.folder,
                               nb_of_try=str(i + 1),
                               time_waiting=str(60))
                    i += 1
                else:
                    raise

    def get_resource_from_hendrix(self, term):
        resource_description = dict(
            **get_model_description(self.model_name),
            date=self.analysis_time,
            term=term,
            local=os.path.join(self.folder, 'tmp_file.fa')
        )

        resource = self._get_resources_vortex(resource_description)
        resource = resource[0] if isinstance(resource, list) else resource

        return resource

    def generate_name_of_cache_folder(self):
        random_key = str(uuid.uuid4())[:10]
        hashcache = "%s-%s" % (self.analysis_time.strftime('%Y-%m-%d_%H'), random_key)

        return os.path.join(self.folder, f"{self.model_name}_" + hashcache)

    def generate_name_output_netcdf(self, start_term, end_term):
        start_time = self.analysis_time + timedelta(hours=start_term)
        end_time = self.analysis_time + timedelta(hours=end_term)
        start_time = start_time.strftime("%Y%m%d_%Hh")
        end_time = end_time.strftime("%Y%m%d_%Hh")
        str_time = f"{start_time}_to_{end_time}"
        return f"{self.model_name}_{str_time}.nc"

    def get_compute_function(self, variable_nc):
        name_compute_function = self.transformations[variable_nc]['compute']
        return globals().get(name_compute_function)

    def get_fa_variables_names(self):
        variables_fa = []
        for value in self.transformations.values():
            variables_fa.extend(value["fa_fields_required"])
        return list(set(variables_fa))

    def get_netcdf_filename_in_cache(self, term):
        """
        On écrit les 24 fichiers netcdf temporaires dans des fichiers, avec une fonction qui donne
        leur nom c'est beaucoup plus facile de les écrire et de les récupérer
        """
        analysis_time_str = self.analysis_time.strftime('%Y-%m-%d-%Hh')
        netcdf_filename = "%s_ana_%s_term_%s.nc"%(self.model_name, analysis_time_str, term)
        return os.path.join(self.cache_folder, netcdf_filename)

    def get_path_vortex_ressource(self, term):
        resource_description = dict(
                **get_model_description(self.model_name),
                date=self.analysis_time,
                term=term,
                local='tmp_file.fa')
        return usevortex.get_resources(getmode='locate', **resource_description)

    def create_cache_folder_if_doesnt_exist(self):
        if not os.path.exists(self.cache_folder):
            os.mkdir(self.cache_folder)

    def delete_cache_folder(self):
        shutil.rmtree(self.cache_folder, ignore_errors=True)

    def delete_temporary_fa_file(self):
        os.remove(os.path.join(self.folder, 'tmp_file.fa'))

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

    def read_times_fa_in_txt_file(self):
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

    def add_metadate_necessary_to_surfex(self, name_netcdf_file):
        """Not ready yet"""
        """
        callSystemOrDie("ncap2 -O -s 'FORC_TIME_STEP=3600.' " + name_netcdf_file + " " + name_netcdf_file)
        callSystemOrDie("ncap2 -O -s 'CO2air=Tair*0. + 0.00062' " + name_netcdf_file + " " + name_netcdf_file)
        #   callSystemOrDie("ncap2 -O -s 'Wind_DIR=Tair*0. + 0.' "+forcing_file+" "+forcing_file)
        callSystemOrDie("ncap2 -O -s 'UREF=ZS*0. + 10.' " + name_netcdf_file + " " + name_netcdf_file)
        callSystemOrDie("ncap2 -O -s 'ZREF=ZS*0. + 2.' " + name_netcdf_file + " " + name_netcdf_file)
        callSystemOrDie(
            "ncap2 -O -s'slope=ZS*0.+0.;aspect=ZS*0.+0.;FRC_TIME_STP=FORC_TIME_STEP' " + name_netcdf_file + " " + name_netcdf_file)
        callSystemOrDie("ncrename -O -v latitude,LAT " + name_netcdf_file)
        callSystemOrDie("ncrename -O -v longitude,LON " + name_netcdf_file)
        callSystemOrDie("ncks -O --mk_rec_dmn time " + name_netcdf_file + " " + name_netcdf_file)
        """
        pass

    @timer_decorator("fa_to_netcdf", unit='minute', level="____")
    def fa_to_netcdf(self, term):
        """
        Fabrication des fichiers netcdf temporaires (1 par échéance)
        """
        self.create_cache_folder_if_doesnt_exist()
        input_resource = self.get_resource_from_hendrix(term)
        print("debug: resource downloaded from Hendrix")
        netcdf_filename = self.get_netcdf_filename_in_cache(term)
        output_resource = epygram.formats.resource(netcdf_filename, 'w', fmt='netCDF')
        output_resource.behave(N_dimension='Number_of_points', X_dimension='xx', Y_dimension='yy')
        for variable in self.variables_fa:
            field = self.read_epygram_field(input_resource, variable)
            field = self.pass_fa_metadata_to_netcdf(field)
            field = self.transform_spectral_field_if_required(field)
            field = self.extract_domain_pixels(field)
            output_resource.writefield(field)

        self.add_metadate_necessary_to_surfex(netcdf_filename)
        self.write_time_fa_in_txt_file(field)

    def netcdf_in_cache_to_dict(self, start_term, end_term):
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
            filename = self.get_netcdf_filename_in_cache(term)
            nc_file = xr.open_dataset(filename)
            dict_from_xarray = nc_file.to_dict()
            for variable in self.variables_fa:
                dict_data[term][variable] = np.array(dict_from_xarray["data_vars"][variable]["data"])
        return dict_data

    def dict_to_netcdf(self, post_processed_data, start_term, end_term):

        filename_nc = self.generate_name_output_netcdf(start_term, end_term)
        dataset = xr.Dataset.from_dict(post_processed_data)

        # Create a time variable
        time = self.read_times_fa_in_txt_file()
        dataset["time"] = (('time'), time[1:])
        dataset.to_netcdf(os.path.join(self.folder, filename_nc))

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

    @timer_decorator("download daily netcdf", unit='minute', level="__")
    def download_daily_netcdf(self, start_term, end_term, **kwargs):

        print("debug: fa_to_netcdf")
        for term in range(start_term-1, end_term+1):
            print("debug: term", term)
            self.fa_to_netcdf(term)

        print("debug: netcdf_in_cache_to_dict")
        dict_data = self.netcdf_in_cache_to_dict(start_term, end_term)

        print("debug: post_process dict_data")
        post_processed_data = defaultdict(lambda: defaultdict(list))
        for term in range(start_term, end_term+1):
            print("debug: term", term)
            post_processed_data = self.post_process(dict_data, post_processed_data, term, **kwargs)

        print("debug: dict_to_netcdf")
        self.dict_to_netcdf(post_processed_data, start_term, end_term)
        self.delete_cache_folder()
        self.delete_temporary_fa_file()


"""
if __name__ == '__main__':
config_user = dict(

#  Where you want to store the outputs
folder= '/cnrm/cen/users/NO_SAVE/letoumelinl/folder/',

# Models are defined in the models.ini file
model_name = 'AROME',

# The domain can be defined by its name or its coordinates
# Existing domain can be found in the config_fa2nc.py file
domain = "alp",
lat_lon_lower_left = None,
lat_lon_upper_right = None,

# Variables to extract and to store in the netcdf file
# Variable are defined in the config_fa2nc.py file
variables_nc = ['Tair', 'Wind'],

# "local" if the FA file are on your computer or "hendrix" otherwise
getter = "hendrix",
#get_resource_from_hendrix,

# For prestaging and sending mail during (your mail = destination) extraction
email_address = "louis.letoumelin@meteo.fr",

# datetime(year, month, day, hour)
date_start = datetime(2019, 5, 1, 0),
date_end = datetime(2019, 5, 3, 0),

# Analysis hour
analysis_time = datetime(2019, 5, 1, 0),

# Term in hour after analysis
start_term = 6, # Default: 6 
end_term = 6 + 24 ,# Defautl: 6+24 = 30
    
# How to group the netcdf files: "month", "year", "all"
final_concatenation = "all"
)

e = Extractor(config_user)
e.download()

"""
