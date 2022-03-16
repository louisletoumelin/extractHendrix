import os
from datetime import datetime, timedelta
from collections import defaultdict
import configparser
import uuid
import time
import sys
import shutil
import smtplib
import pkg_resources
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate
import logging
import itertools
import copy
import warnings

logger_epygram = logging.getLogger('epygram')
logger_epygram.setLevel(level=logging.CRITICAL)

logger_vortex = logging.getLogger('vortex')
logger_vortex.setLevel(level=logging.CRITICAL)

warnings.simplefilter(action='ignore', category=FutureWarning)

import numpy as np
import xarray as xr

import usevortex
import epygram
from extracthendrix.config.config_fa2nc import transformations, domains, alternatives_names_fa
from extracthendrix.config.post_processing_functions import *
from extracthendrix.hendrix_emails import dict_with_all_emails, _prepare_html


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def timer_decorator(argument, unit='minute', level="__"):
    """
    Decorator to record execution time. Used as follow:

    @timer_decorator
    def function()
        ...
    """
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


def model_ini_to_dict(model_name):
    config = configparser.ConfigParser()
    models_path = pkg_resources.resource_filename('extracthendrix.config', 'models.ini')
    config.read(models_path)
    dict_model = dict(config[model_name])
    return dict_model


def get_model_description(model_name):
    """Get vortex description of a model"""

    dict_model = model_ini_to_dict(model_name)

    for key in dict_model.keys():
        dict_model[key] = dict_model[key].split(',')

    keys, values = zip(*dict_model.items())
    list_dict_models = [dict(zip(keys, v)) for v in itertools.product(*values)]

    return list_dict_models


def get_name_from_email(email_address):
    """Parses user name from email"""
    return email_address.split("@")[0].replace('.', '_')


def _send_email(type_of_email, email_address, **kwargs):
    """Send email to email_address using Météo-France network"""
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
        logger.info(f"Successfully sent an email to {to_addrs}\n\n")
    except smtplib.SMTPException as e:
        logger.error(f"Email {type_of_email} could not be launched. The error is: {e}\n\n")

    server.quit()


def callSystemOrDie(commande, errorcode=None):
    """Not used yet"""
    status = os.system(commande)
    if status != 0:

        if type(errorcode) is int:
            print("The following command fails with error code " + str(status) + ":\n" + commande)
            sys.exit(errorcode)
        else:
            sys.exit("The following command fails with error code " + str(status) + ":\n" + commande)
    return status


class CanNotReadEpygramField(Exception):
    pass


class CanNotAccessVortexResource(Exception):
    pass


def print_documentation():
    """print all links to documentation"""
    print_link_to_hendrix_documentation()
    print("\n\n")
    print_link_to_confluence_table_with_downloaded_data()
    print("\n\n")
    print_link_to_arome_variables()


def print_link_to_hendrix_documentation():
    print("The documentation of the storage system Hendrix is available here:")
    print("http://confluence.meteo.fr/pages/viewpage.action?pageId=299881305")


def print_link_to_confluence_table_with_downloaded_data():
    link = "http://confluence.meteo.fr/pages/viewpage.action?pageId=314552092"
    print("\n[INFORMATION] Have you check that the data you request is not already downloaded at CEN?\n")
    print("Please see the link below")
    print(link)


def print_link_to_arome_variables():
    link = "http://intra.cnrm.meteo.fr/aromerecherche/spip.php?article25"
    print("Website with all AROME variables (might be outdated)")
    print(link)
    link = "https://opensource.umr-cnrm.fr/projects/pnt-mine/wiki/Champs_de_surface_des_fichiers_de_sortie_en_PNT"
    print("Website with all AROME surface variables (might be outdated)")
    print(link)


class Extractor:
    """This class extracts data defined in config_user"""

    def __init__(self, config_user):
        self.getter = config_user.get("getter")
        self.folder = config_user.get("folder")
        self.model_name = config_user.get("model_name")
        self.analysis_hour = config_user.get("analysis_hour")
        self.domain = config_user.get("domain")
        self.variables_nc = config_user.get("variables_nc")
        self.date_start = config_user.get("date_start") + timedelta(hours=self.analysis_hour)
        self.date_end = config_user.get("date_end") + timedelta(hours=self.analysis_hour)
        self.email_address = config_user.get("email_address")
        self.start_term = config_user.get("start_term", 6)
        self.end_term = config_user.get("end_term", 30)
        self.delta_terms = config_user.get("delta_terms")

        self.concat_mode = config_user.get("concat_mode", "timeseries")

        if self.concat_mode not in ["timeseries", "forecast"]:
            raise NotImplementedError("invalid concat_mode. Please choose timeseeries or forecast")

        self.group_by_output_file = config_user.get("group_by_output_file")

        if self.concat_mode == "timeseries" and self.group_by_output_file not in ["year", "month", "all"]:
            raise NotImplementedError("invalid group_by_output_file. year, month or all available for timeseries")
        elif self.concat_mode == "forecast" and self.group_by_output_file not in ["deterministic", "ensemble"]:
            raise NotImplementedError("invalid group_by_output_file. deterministic and ensemble available for forecasts")

        self.errors = dict()
        self.config_user = config_user

    def __repr__(self):
        return f"Extractor with following parameters {self.config_user}"

    def send_email(self, type_of_email, t0=None, e=None, *args):

        if type_of_email == "finished":
            _send_email("finished", self.email_address,
                        config_user=str(self.config_user),
                        current_time=time.asctime(),
                        time_to_download=str(np.round((time.time() - t0) / 3600, 2)),
                        folder=self.folder)

        elif type_of_email == "script_stopped":

            _send_email("script_stopped", self.email_address,
                        config_user=self.config_user,
                        current_time=time.asctime(),
                        error=e,
                        folder=self.folder)

        elif type_of_email == "extracted_first_half":
            self._send_email_at_half_execution(*args)
        else:
            pass

    def _send_email_at_half_execution(self, nb_days_to_extract, idx_date, t0):
        if nb_days_to_extract > 100 and idx_date == (nb_days_to_extract // 2 + 1):
            _send_email("extracted_first_half", self.email_address,
                        config_user=str(self.config_user),
                        current_time=time.asctime(),
                        time_to_download=str(np.round((time.time() - t0) / 3600, 2)),
                        errors=str(self.errors),
                        folder=self.folder)

    @staticmethod
    def date_iterator(date_start, date_end):
        """Return a generator containing dates between date_start and date_end"""
        current_date = date_start - timedelta(1)
        while current_date < date_end:
            current_date += timedelta(1)
            yield current_date

    @staticmethod
    def get_year_and_month_between_dates(start, end):
        """
        date_start = datetime(2019, 10, 1, 0)
        date_end = datetime(2020, 2, 29, 0)
        get_year_and_month_between_dates(date_start, date_end)
        # returns [(2019, 10), (2019, 11), (2019, 12), (2020, 1), (2020, 2)]
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
        # returns [2019, 2020]
        """
        total_months = lambda dt: dt.month + 12 * dt.year
        mlist = []
        for tot_m in range(total_months(start)-1, total_months(end)):
            y, m = divmod(tot_m, 12)
            mlist.append(datetime(y, m+1, 1).year)
        return list(set(mlist))

    def ij2latlon(self, first_i, last_i, first_j, last_j, term=5):
        """
        Convert bounds of a domains in grid indexes to lat/lon

        Input:
        first_i, last_i, first_j, last_j

        Return:
        ll_lat, ll_lon: lat and lon of lower left corner (ll)
        ur_lat, ur_lon: lat and lon of upper right corner (ur)
        """
        hc = HendrixConductor(self.getter, self.folder, self.model_name, self.date_start, self.domain,
                              self.variables_nc, self.email_address, self.delta_terms)
        resource = hc.get_resource_from_hendrix(term)
        field = resource.readfield('CLSTEMPERATURE')
        ll_lat, ll_lon = field.geometry.ij2ll(first_i, first_j)
        ur_lat, ur_lon = field.geometry.ij2ll(last_i, last_j)
        return ll_lat, ll_lon, ur_lat, ur_lon

    def latlon2ij(self, ll_lat, ll_lon, ur_lat, ur_lon, term=5):
        """
        Convert bounds of a domains in lat/lon to grid indexes

        Input:
        ll_lat, ll_lon: lat and lon of lower left corner (ll)
        ur_lat, ur_lon: lat and lon of upper right corner (ur)

        Return:
        first_i, last_i, first_j, last_j
        """
        hc = HendrixConductor(self.getter, self.folder, self.model_name, self.date_start, self.domain,
                              self.variables_nc, self.email_address, self.delta_terms)
        resource = hc.get_resource_from_hendrix(term)
        field = resource.readfield('CLSTEMPERATURE')
        x1, y1 = np.round(field.geometry.ll2ij(ll_lon, ll_lat)) + 1
        x2, y2 = np.round(field.geometry.ll2ij(ur_lon, ur_lat)) + 1
        return x1, x2, y1, y2

    def concatenate_netcdf(self, list_daily_netcdf_files):
        """Concatenates files according to desired output shape"""
        if self.concat_mode == "timeseries":
            try:
                dataset = xr.open_mfdataset([os.path.join(self.folder, file) for file in list_daily_netcdf_files],
                                            data_vars='different')
            except:
                self.errors["concatenation"] = "Files are not concatenated with the desired final format \n" \
                                               "We could not read all file at once using xarray. " \
                                               "This is likely due to the fact that the number of point in your domain" \
                                               "varies with time (e.g. +/- 1 pixel)"
                return

            if self.group_by_output_file == "month":
                self._concatenate_netcdf_by_year_and_month(dataset)
            elif self.group_by_output_file == "year":
                self._concatenate_netcdf_by_year(dataset)
            elif self.group_by_output_file == "all":
                self._concatenate_all_netcdf(dataset)
            else:
                return
        elif self.concat_mode == "forecast":
            # todo: implement concatenation
            pass
        else:
            raise NotImplementedError("concatenation mode ", self.concat_mode, "not implemented")

    def _concatenate_netcdf_by_year_and_month(self, dataset):
        """Internal method to concatenated a xarray dataset composed of daily files into individual
        files by year and month"""
        list_years_months = self.get_year_and_month_between_dates(self.date_start, self.date_end)

        for (year, month) in list_years_months:
            condition_month = dataset["time.month"] == month
            condition_year = dataset["time.year"] == year
            filename = os.path.join(self.folder, f"{self.model_name}_{self.domain}_{year}_{month}.nc")
            dataset.where(condition_month & condition_year, drop=True).to_netcdf(filename)
        logger.info("Concatenation by year and month worked\n\n")

    def _concatenate_netcdf_by_year(self, dataset):
        """Internal method to concatenated a xarray dataset composed of daily files into individual files by year"""
        list_years = self.get_year_between_dates(self.date_start, self.date_end)

        for year in list_years:
            condition_year = dataset["time.year"] == year
            filename = os.path.join(self.folder, f"{self.model_name}_{self.domain}_{year}.nc")
            dataset.where(condition_year, drop=True).to_netcdf(filename)
        logger.info("Concatenation by year worked\n\n")

    def _concatenate_all_netcdf(self, dataset):
        """Internal method to concatenate daily files into a single netcdf file"""
        start_str = (self.date_start + timedelta(hours=self.analysis_hour)
                     + timedelta(hours=self.start_term)).strftime('%Y%m%d_%Hh')
        end_str = (self.date_end + timedelta(hours=self.analysis_hour)
                   + timedelta(hours=self.end_term)).strftime('%Y%m%d_%Hh')
        filename = os.path.join(self.folder, f"{self.model_name}_{self.domain}_from_{start_str}_to_{end_str}.nc")
        dataset.to_netcdf(filename)
        logger.info("Concatenation worked\n\n")

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
                hc = HendrixConductor(self.getter, self.folder, self.model_name, date, self.domain, self.variables_nc,
                                      self.email_address, self.delta_terms)
                for term in range(self.start_term, self.end_term, self.delta_terms):
                    resources = hc.get_path_vortex_ressource(term)
                    for resource in resources:
                        f.write(resource[0].split(':')[1] + "\n")

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

        print_link_to_hendrix_documentation()

    def _extract_initial_term(self):
        """Depreciated"""
        logger.info(f"Begin to extract initial term {self.start_term - 1} of first date {self.date_start}\n\n")
        hc = HendrixConductor(self.getter, self.folder, self.model_name, self.date_start, self.domain,
                              self.variables_nc, self.email_address, self.delta_terms)
        hc.download_daily_netcdf(self.start_term, self.start_term)
        name_initial_netcdf = hc.generate_name_output_netcdf(self.start_term, self.start_term)
        logger.info("Initial term extracted\n\n")
        return name_initial_netcdf

    def download(self):
        """Download data"""
        logger.info(f"self terms: {self.start_term} {self.end_term}")
        if self.concat_mode == "timeseries" and (self.end_term - self.start_term) != 23:
            logger.warning("end_term - start_term should be equal to 23h when concat_mode is timeseries.")
        try:
            t0 = time.time()
            print_link_to_confluence_table_with_downloaded_data()

            dates = list(self.date_iterator(self.date_start, self.date_end))
            names_netcdf = []

            nb_days_to_extract = len(dates)
            for idx_date, date in enumerate(dates):
                date += timedelta(hours=self.analysis_hour)
                logger.info(f"Begin to extract {date}\n\n")

                # self.send_email("extracted_first_half", nb_days_to_extract, idx_date, t0)

                hc = HendrixConductor(self.getter, self.folder, self.model_name, date, self.domain,
                                      self.variables_nc, self.email_address, self.delta_terms)
                hc.download_daily_netcdf(self.start_term, self.end_term)
                names_netcdf.append(hc.generate_name_output_netcdf(self.start_term, self.end_term))
            logger.info(f"Daily netcdf are downloaded\n\n")

            if self.concat_mode == "timeseries":
                self.concatenate_netcdf(names_netcdf)

            self.send_email("finished", t0=t0)
            logger.info("The extraction is finished\n\n")

        except Exception as e:
            self.send_email("script_stopped", e=e)
            logger.critical("The extraction stopped\n\n")
            raise


class HendrixConductor:
    """This class extract single fa files and returns daily netcdf files"""

    def __init__(self, getter, folder, model_name, analysis_time, domain, variables_nc, email_address, delta_terms):
        self.folder = folder
        self.analysis_time = analysis_time
        self.model_name = model_name
        self.domain = domains[domain]
        self.email_address = email_address
        self.delta_terms = delta_terms
        self.transformations = {
                key: value
                for key, value in transformations.items()
                if key in variables_nc}
        self.getter = self.parse_getter(getter)
        self.cache_folder = self.generate_name_of_cache_folder()
        self.variables_fa, self.variables_grib, self.is_surface_variable = self.get_variables_names()
        self.contains_surface_variables = any(self.is_surface_variable)

    def parse_getter(self, getter):
        """
        Select the function ("getter") that load data.
        Generally this function is different if your data is on hendrix and on your local computer
        """
        if getter == "hendrix":
            return self.get_resource_from_hendrix
        elif getter == "local":
            raise NotImplementedError("We need to implement a getter from local ressources")
        else:
            raise NotImplementedError

    def _sleep_and_send_mail(self, nb_of_try, time_to_sleep, resource_description, error):

        if time_to_sleep == "30min":
            time_str_logging = "30 minutes"
            time_str_mail = "30"
            seconds_to_sleep = 1800
        elif time_to_sleep in ["1h", "60min"]:
            time_str_logging = "1 hour"
            time_str_mail = "60"
            seconds_to_sleep = 3600

        logger.error(f"We will try accessing the resource again in {time_str_logging}\n\n")
        logger.error(f"Number of try: {nb_of_try + 1}/10\n\n")
        time.sleep(seconds_to_sleep)

        _send_email("problem_extraction", self.email_address,
                    user=get_name_from_email(self.email_address),
                    error_message=error,
                    time_of_problem=time.asctime(),
                    resource_that_stopped=str(resource_description),
                    folder=self.folder,
                    nb_of_try=str(nb_of_try + 1),
                    time_waiting=time_str_mail)

    def _get_resources_vortex(self, resource_descriptions_init):
        """Internal method that access files on Hendrix. Based on Epygram "use_vortex" function."""
        assert isinstance(resource_descriptions_init, list)
        assert resource_descriptions_init

        i = 0
        while i < 10:
            try:
                resource_descriptions = copy.deepcopy(resource_descriptions_init)
                while resource_descriptions:
                    try:
                        resource_description = resource_descriptions.pop()
                        #logger.debug("Start get_resources method from usevortex"
                        #             f"\nModel={resource_descriptions['model']}\n\n")
                        return usevortex.get_resources(getmode='epygram', **resource_description)

                    except (RuntimeError, OSError) as e:
                        logger.error(f"The following error has been encountered: \n\n{repr(e)}"
                                     f"\n\nYour resource description is probably invalid."
                                     "\nThis can happen if e.g. namespace is not valid."
                                     "\nWe try to access next resource description if available."
                                     f"\n\nInvalid resource description: {resource_description}"
                                     f"\n\nRemaining resource descriptions: {resource_descriptions}\n\n")


                else:
                    logger.error("We tried to access every resource_description possible but it didn't work."
                                 "\nPlease check that your resource_description is valid.\n\n")
                    raise CanNotAccessVortexResource

            except Exception as e:
                logger.error("An exception has occured when using usevortex.get_resources command"
                             f"\n\nThe exception raised is: {repr(e)}"
                             "\n\nException at this stage can occur if Hendrix server is not accessible"
                             f"Current resource description is {resource_description}\n\n")

                if i < 5:
                    self._sleep_and_send_mail(i, "30min", resource_description, e)
                    i += 1
                elif 5 <= i < 9:
                    self._sleep_and_send_mail(i, "1h", resource_description, e)
                    i += 1
                else:
                    raise

    def get_resource_from_hendrix(self, term, model_name=None, tmp_file='tmp_file.tmp'):
        """function that accesses resources on hendrix. Based on Epygram "use_vortex" function."""

        model_name = self.model_name if model_name is None else model_name
        model_descriptions = get_model_description(model_name)
        assert isinstance(model_descriptions, list)
        assert isinstance(model_descriptions[0], dict)

        resource_descriptions = [dict(
            **model_description,
            date=self.analysis_time,
            term=term,
            local=os.path.join(self.folder, tmp_file)
        ) for model_description in model_descriptions]

        resource = self._get_resources_vortex(resource_descriptions)
        resource = resource[0] if isinstance(resource, list) else resource

        return resource

    def generate_name_of_cache_folder(self):
        """Generates a unique path for temporary cache folder (including random numbers in the path)"""
        random_key = str(uuid.uuid4())[:10]
        hashcache = "%s-%s" % (self.analysis_time.strftime('%Y-%m-%d_%H'), random_key)

        return os.path.join(self.folder, f"{self.model_name}_" + hashcache)

    def generate_name_output_netcdf(self, start_term, end_term):
        """generate a path for daily netcdf outputs"""
        start_time = self.analysis_time + timedelta(hours=start_term)
        end_time = self.analysis_time + timedelta(hours=end_term)
        start_time = start_time.strftime("%Y%m%d_%Hh")
        end_time = end_time.strftime("%Y%m%d_%Hh")
        str_time = f"{start_time}_to_{end_time}"
        return f"{self.model_name}_{str_time}.nc"

    def get_compute_function(self, variable_nc):
        """Get postprocessing function associated with a netcdf variable"""
        name_compute_function = self.transformations[variable_nc]['compute']
        return globals().get(name_compute_function)

    def get_variables_names(self):
        """
        Get fa names, grib names and surface variable indicator required to download a specific
        variable

        """
        variables_fa = []
        variables_grib = []
        is_surface_variable = []
        for value in self.transformations.values():
            variables_fa.extend(value["fa_fields_required"])
            variables_grib.extend(value["grib_fields_required"])
            is_surface_variable.extend(value["is_surface_variable"])
        return (variables_fa, variables_grib, is_surface_variable)

    def get_netcdf_filename_in_cache(self, term):
        """Get path to netcdf filenames in cache folder. One netcdf corresponds to one fa file."""
        analysis_time_str = self.analysis_time.strftime('%Y-%m-%d-%Hh')
        netcdf_filename = "%s_ana_%s_term_%s.nc"%(self.model_name, analysis_time_str, term)
        return os.path.join(self.cache_folder, netcdf_filename)

    def get_path_vortex_ressource(self, term, model_name=None):
        """Returns the path of a vortex resource (typically a single fa file) on Hendrix"""
        #resource_description = dict(
        #        **get_model_description(self.model_name),
        #        date=self.analysis_time,
        #        term=term,
        #        local='tmp_file.tmp')

        model_name = self.model_name if model_name is None else model_name
        model_descriptions = get_model_description(model_name)
        assert isinstance(model_descriptions, list)
        assert isinstance(model_descriptions[0], dict)

        resource_descriptions = [dict(
            **model_description,
            date=self.analysis_time,
            term=term,
            local=os.path.join(self.folder, 'tmp_file.tmp')
        ) for model_description in model_descriptions]

        return [usevortex.get_resources(getmode='locate', **resource_description) for resource_description in resource_descriptions]

    def create_cache_folder_if_doesnt_exist(self):
        """
        Creates a cache folder (temporary), where netcdf files
        (typically hourly netcdf corresponding to hourly fa file) are stored.
        """
        if not os.path.exists(self.cache_folder):
            os.mkdir(self.cache_folder)

    def delete_cache_folder(self):
        """Delete temporary cache folder"""
        shutil.rmtree(self.cache_folder, ignore_errors=True)
        logger.debug("Deleted temporary folder\n\n")

    def delete_temporary_fa_file(self):
        """Delete temporary fa file"""
        os.remove(os.path.join(self.folder, 'tmp_file.tmp'))
        logger.debug("Deleted temporary fa file\n\n")

    @staticmethod
    def transform_spectral_field_if_required(field):
        """Wraps an Epygram method to transform spectral fields to grid points"""
        if field.spectral:
            field.sp2gp()
        return field

    @staticmethod
    def pass_fa_metadata_to_netcdf(field):
        """Pass metadata from fa file to netcdf file"""
        try:
            field.fid['netCDF'] = field.fid['FA']
        except KeyError:
            field.fid['netCDF'] = field.fid['GRIB2']['shortName']
        return field

    def extract_domain_pixels(self, field):
        """Extract pixels of an Epygram field corresponding to a user defined domain"""
        if self.model_name not in ['AROME', 'AROME_SURFACE']:
            x1, y1 = np.round(field.geometry.ll2ij(self.domain['lon_llc'], self.domain['lat_llc'])) + 1
            x2, y2 = np.round(field.geometry.ll2ij(self.domain['lon_urc'], self.domain['lat_urc'])) + 1
            field = field.extract_subarray(int(x1), int(x2), int(y1), int(y2))
        else:
            field = field.extract_subarray(
                self.domain['first_i'],
                self.domain['last_i'],
                self.domain['first_j'],
                self.domain['last_j']
            )
        return field

    def write_time_fa_in_txt_file(self, field):
        """Read time in fa file and store it in txt file. This method prevents to mix dates of the extracted files"""
        with open(os.path.join(self.cache_folder, "times.txt"), "a+") as t:
            time_in_fa_file = field.validity[0].get()
            t.write(time_in_fa_file.strftime("%Y/%m/%d_%H:%M:%S")+"\n")

    def read_times_fa_in_txt_file(self):
        """Read the dates corresponding to simulation time, stored in a txt file."""
        with open(os.path.join(self.cache_folder, "times.txt"), "r") as t:
            list_times = []
            for line in t:
                time = datetime.strptime(line[:-1], "%Y/%m/%d_%H:%M:%S")
                list_times.append(np.datetime64(time))
        return np.array(list_times)

    @staticmethod
    def read_epygram_field(input_resource, variable):
        """Reads an Epygram field (=variable). Uses alternative name if original names are not found in the file"""
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
                        logger.warning(f"Found an alternative name for {initial_name} that works: {variable}\n\n")
                        return field
                    except AssertionError:
                        logger.error(f"Alternative name {variable} didn't work for variable {initial_name}\n\n")
                        pass
                logger.error(f"We coulnd't find correct alternative names for {initial_name}\n\n")
                raise CanNotReadEpygramField(f"We couldn't find correct alternative names for {initial_name}")
            else:
                logger.error(f"We couldn't read {initial_name}\n\n")
                raise CanNotReadEpygramField(f"We couldn't read {initial_name}")

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

    def get_grib_names_of_surface_variables(self):
        """
        get list of surface variable names for a surface file in grib format.
        :return: variables
        :rtype: list
        """
        surface_variables_grib = []
        for variable_nc in self.transformations:
            if self.transformations[variable_nc].get("is_surface_variable"):
                surface_variables_grib.extend(self.transformations[variable_nc]["grib_fields_required"])
        return surface_variables_grib

    def get_fa_names_of_surface_variables(self):
        """
        get list of variable names for a surface file in fa format.
        :return: variables
        :rtype: list
        """
        surface_variables_fa = []
        for variable_nc in self.transformations:
            if self.transformations[variable_nc].get("is_surface_variable"):
                surface_variables_fa.extend(self.transformations[variable_nc]["fa_fields_required"])
        return surface_variables_fa

    def _select_fa_or_grib_name(self, input_resource):
        if input_resource.format in ['GRIB']:
            return self.variables_grib
        else:
            return self.variables_fa

    def _change_surface_variable_name_if_required(self, surface_resource, variables):
        if surface_resource.format in ['GRIB']:
            return [grib if is_surf else var for var, grib, is_surf in zip(variables, self.variables_grib,
                                                                                self.is_surface_variable)]
        else:
            return [fa if is_surf else var for var, fa, is_surf in zip(variables, self.variables_fa,
                                                                            self.is_surface_variable)]

    @timer_decorator("hendrix_to_netcdf", unit='minute', level="____")
    def hendrix_to_netcdf(self, term):
        """
        Builds a single netcdf file corresponding to a single fa or grib file.

        :param term: forecast leadtime
        :type term: int
        """
        self.create_cache_folder_if_doesnt_exist()
        input_resource = self.get_resource_from_hendrix(term)

        netcdf_filename = self.get_netcdf_filename_in_cache(term)
        output_resource = epygram.formats.resource(netcdf_filename, 'w', fmt='netCDF')
        output_resource.behave(N_dimension='Number_of_points', X_dimension='xx', Y_dimension='yy')

        variables = self._select_fa_or_grib_name(input_resource)

        # print("surf vars present: ", self.contains_surface_variables)
        if self.contains_surface_variables:
            surface_resource = self.get_resource_from_hendrix(term, model_name=self.model_name+"_SURFACE",
                                                              tmp_file='tmp_file_surf.tmp')
            # print('got surface resource')
            variables = self._change_surface_variable_name_if_required(surface_resource, variables)

        for variable, is_surface in zip(variables, self.is_surface_variable):
            resource = surface_resource if is_surface else input_resource
            field = self.read_epygram_field(resource, variable)
            field = self.pass_fa_metadata_to_netcdf(field)
            field = self.transform_spectral_field_if_required(field)
            field = self.extract_domain_pixels(field)
            output_resource.writefield(field)

        #todo implement this function
        self.add_metadate_necessary_to_surfex(netcdf_filename)

        self.write_time_fa_in_txt_file(field)
        logger.debug(f"Successfully converted a fa file to netcdf for term {term}\n\n")

    def netcdf_in_cache_to_dict(self, start_term, end_term):
        """
        Reads netcdf files in cache folder and converts it to a nested dict.
        Nested dict has the following structure
        {6: {variable1: ndarray, variable2: ndarray},
        7: {variable1: ndarray, variable2: ndarray},
        8: {variable1: ndarray, variable2: ndarray}
        .........
        }
        where 6,7,8 are forecast terms
        variable1, variable2 are elements in the list "variables".
        """
        dict_data = defaultdict(lambda: defaultdict(dict))
        for term in range(start_term-1, end_term+1, self.delta_terms):
            filename = self.get_netcdf_filename_in_cache(term)
            nc_file = xr.open_dataset(filename)
            dict_from_xarray = nc_file.to_dict()
            #print(dict_from_xarray.keys())
            for variable in dict_from_xarray["data_vars"].keys():
                if variable not in ['longitude', 'latitude', 'time']:
                    dict_data[term][variable] = np.array(dict_from_xarray["data_vars"][variable]["data"])
            # print(dict_from_xarray["data_vars"]["longitude"])
        dict_data["longitude"] = dict_from_xarray["data_vars"]["longitude"]
        dict_data["latitude"] = dict_from_xarray["data_vars"]["latitude"]
        dict_data["Projection_parameters"] = dict_from_xarray["data_vars"]["Projection_parameters"]
        logging.debug("Successfully converted netcdf (for each term) into a nested dictionary containing numpy arrays")
        return dict_data

    def post_process(self, input_dict, output_dict, term, **kwargs):
        """Post-process numpy arrays in dict_data (i.e. decumul rains, compute wind speed from components...)"""
        for variable_nc in self.transformations:

            compute = self.get_compute_function(variable_nc)
            name_variables_fa = self.transformations[variable_nc]['fa_fields_required']
            output_dict[variable_nc]["dims"] = ('time', 'yy', 'xx')
            if compute is not None:
                variable_array = compute(input_dict, term, *name_variables_fa, **kwargs)
                output_dict[variable_nc]["data"].append(variable_array)
            else:
                output_dict[variable_nc]["data"].append(input_dict[term][name_variables_fa[0]])
        output_dict["longitude"] = input_dict['longitude']
        output_dict["latitude"] = input_dict['latitude']
        output_dict["Projection_parameters"] = input_dict['Projection_parameters']

        return output_dict

    def dict_to_netcdf(self, post_processed_data, start_term, end_term):
        """Processes data from a dictionary containing daily outputs and store it in a netcdf file"""
        filename_nc = self.generate_name_output_netcdf(start_term, end_term)
        dataset = xr.Dataset.from_dict(post_processed_data)

        # Create a time variable
        time = self.read_times_fa_in_txt_file()
        dataset["time"] = (('time'), time[1:])
        dataset.to_netcdf(os.path.join(self.folder, filename_nc))
        logging.debug("Successfully converted nested dict to netcdf")

    @timer_decorator("download daily netcdf", unit='minute', level="__")
    def download_daily_netcdf(self, start_term, end_term, **kwargs):
        """Downloads a netcdf file for a single day between start_term and end_term"""
        for term in range(start_term-1, end_term+1, self.delta_terms):
            logger.debug(f"Begin to download term {term}\n\n")
            self.hendrix_to_netcdf(term)
        logger.debug(f"Terms converted to netcdf\n\n")

        dict_data = self.netcdf_in_cache_to_dict(start_term, end_term)

        post_processed_data = defaultdict(lambda: defaultdict(list))
        for term in range(start_term, end_term+1, self.delta_terms):
            post_processed_data = self.post_process(dict_data, post_processed_data, term, **kwargs)
        logger.debug("Successfully postprocessed data in nested dictionary\n\n")

        self.dict_to_netcdf(post_processed_data, start_term, end_term)
        self.delete_cache_folder()
        self.delete_temporary_fa_file()
