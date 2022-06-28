from datetime import timedelta
import os
import copy
import logging
from contextlib import contextmanager
from datetime import time, datetime, timedelta
import time as timeutils
from collections import defaultdict
import glob
import shutil
import uuid

import numpy as np
import epygram
import xarray as xr
from extracthendrix.hendrix_emails import send_problem_extraction_email, send_script_stopped_email

from extracthendrix.readers import AromeHendrixReader
from extracthendrix.config.domains import domains_descriptions
from extracthendrix.config.config_fa_or_grib2nc import alternatives_names_fa
from extracthendrix.exceptions import CanNotReadEpygramField
from extracthendrix.config.variables import arome, pearome

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class FolderLayout:
    """
    Creates directory where files are stored

    :param work_folder: Path to main folder where extraction is done
    :type work_folder: str
    """

    def __init__(self, work_folder):
        self.work_folder = work_folder
        self._create_layout()

    @staticmethod
    def _create_folder_if_doesnt_exist(path):
        """Create a folder if it doesn't already exists

        :param path: Folder path
        :type path: str
        """
        try:
            os.mkdir(path)
        except FileExistsError:
            print(f"Folder {path} already exists")

    def _create_layout(self):
        """
        Creates folder and subfolders for the current extraction

        ├── work_folder
        │   ├── _native_
        │   ├── _cache_
        │   ├── _computed_
        │   ├── _final_
        """
        # Parent folder
        self._create_folder_if_doesnt_exist(self.work_folder)

        # Subfolders
        for subfolder in ['_native_', '_cache_', '_computed_', '_final_']:
            setattr(self, subfolder, os.path.join(self.work_folder, subfolder))
            self._create_folder_if_doesnt_exist(getattr(self, subfolder))

    def clean_layout(self):
        for subfolder in ['_native_', '_cache_', '_computed_']:
            shutil.rmtree(getattr(self, subfolder))


class AromeCacheManager:

    def __init__(
            self,
            folderLayout,
            domain=None,
            variables=[],
            model=None,
            runtime=None,
            delete_native=True,
            member=None,
            autofetch_native=False
    ):
        self.folderLayout = folderLayout
        self.delete_native = delete_native
        self.coordinates = ['latitude', 'longitude']
        self.extractor = AromeHendrixReader(folderLayout, model, runtime, member)
        self.domain = domain
        self.variables = variables
        self.runtime = runtime
        self.autofetch_native = autofetch_native
        self.opened_files = {}

    # old get_cache_path
    def get_path_file_in_cache(self, date, term, domain):
        """
        Return full path to file in cache for a given run time and forecast lead time

        :param date: Run time
        :type date: datetime
        :param term: forecast leadtime
        :type term: int
        :return: str
        """
        filename = self.extractor.get_file_hash(date, term)
        filename = f"{filename}_{domain}.nc"
        folder = self.folderLayout._cache_
        return os.path.join(folder, filename)

    def extract_subgrid(self, field, domain):
        """Extract pixels of an Epygram field corresponding to a user defined domain"""
        domain_description = domains_descriptions[domain]
        if self.extractor.model_name not in ['AROME', 'AROME_SURFACE']:
            i1, j1 = np.round(field.geometry.ll2ij(domain_description['lon_llc'], domain_description['lat_llc'])) + 1
            i2, j2 = np.round(field.geometry.ll2ij(domain_description['lon_urc'], domain_description['lat_urc'])) + 1
            field = field.extract_subarray(int(i1), int(i2), int(j1), int(j2))
        else:
            field = field.extract_subarray(
                domain_description['first_i'],
                domain_description['last_i'],
                domain_description['first_j'],
                domain_description['last_j'])
        return field

    @staticmethod
    def read_field_or_alternate_name(input_resource, variable):
        """Reads an Epygram field (=variable). Uses alternative name if original names are not found in the file"""
        initial_name = variable

        try:
            return input_resource.readfield(variable.name)
        except AssertionError:
            if variable in alternatives_names_fa:
                alternatives_names = copy.deepcopy(
                    alternatives_names_fa[variable])
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

    @staticmethod
    def pass_metadata_to_netcdf(field, outname=None):
        """Pass metadata from fa file to netcdf file"""
        if outname:
            field.fid['netCDF'] = outname
            return field
        else:
            try:
                field.fid['netCDF'] = field.fid['FA']
            except KeyError:
                field.fid['netCDF'] = field.fid['GRIB2']['shortName']
            return field

    def get_native_resource_if_necessary(self, date, term):
        native_file_path = self.extractor.get_native_file(date, term, autofetch=self.autofetch_native)
        input_resource = epygram.formats.resource(native_file_path, 'r', fmt=self.extractor.fmt.upper())
        return native_file_path, input_resource

    def put_in_cache(self, date, term, domain):
        """
        Builds a single netcdf file corresponding to a single fa or grib file.

        :param term: forecast leadtime
        :type term: int
        # TODO: would be nice if hendrix reader could return each variable in a fixed format,
        this way the cache manager wouldn't depend on the file's format
        """

        # Check if file is already in cache
        filepath_in_cache = self.get_path_file_in_cache(date, term, domain)
        if os.path.isfile(filepath_in_cache):
            return

        # Open Epygram resource
        output_resource = epygram.formats.resource(filepath_in_cache, 'w', fmt='netCDF')
        output_resource.behave(N_dimension='Number_of_points', X_dimension='xx', Y_dimension='yy')

        # Download file on Hendrix if necessary
        native_file_path, input_resource = self.get_native_resource_if_necessary(date, term)

        # Extract variable from native file (i.e. .fa or .grib)
        for variable in self.variables:
            field = self.read_field_or_alternate_name(input_resource, variable)
            field = self.pass_metadata_to_netcdf(field, variable.outname)
            if field.spectral:
                field.sp2gp()
            field = self.extract_subgrid(field, domain)
            output_resource.writefield(field)
        logger.debug(f" .fa or .grib file converted to netcdf for date {date} and term {term}\n\n")

    def get_file_in_cache(self, filepath):
        if filepath not in self.opened_files:
            self.open_and_store_file(filepath)
        return self.opened_files[filepath]

    def open_and_store_file(self, filepath):
        dataset = xr.open_dataset(filepath).set_coords(self.coordinates)
        self.opened_files[filepath] = dataset

    def forget_opened_files(self):
        self.opened_files = {}

    def close_file(self, date, term):
        """Not used"""
        filepath = self.get_path_file_in_cache(date, term, domain)
        file = self.opened_files[filepath]
        file['dataset'].close()
        del self.opened_files[filepath]

    def delete_native_files(self):
        """Delete .fa or .grib file after extraction of desired variables"""
        if self.delete_native:
            files = glob.glob(f'{self.folderLayout._native_}/*')
            for f in files:
                os.remove(f)

    def read_cache(self, date, term, domain, native_variables):
        # Check file in cache and download if necessary
        filepath_in_cache = self.get_path_file_in_cache(date, term, domain)
        file_is_not_in_cache = not os.path.isfile(filepath_in_cache)
        if file_is_not_in_cache:
            self.put_in_cache(date, term, domain)

        # Return the file from cache
        dataset = self.get_file_in_cache(filepath_in_cache)
        return dataset[native_variables.outname]


def get_model_names(computed_vars):
    return {ivar.model_name for var in computed_vars for ivar in var.native_vars}


def sort_native_vars_by_model(computed_vars):
    """
    get all native variables sorted by model
    :return: a dict with keys=model names and values a list of variables to get from that model.
    Depending on the file format that might be strings with FA names or dicts with grib keys.
    :rtype: dict
    """
    model_names = get_model_names(computed_vars)
    return {
        model_name: [
            native_var
            for computed_var in computed_vars
            for native_var in computed_var.native_vars
            if native_var.model_name == model_name
        ]
        for model_name in model_names
    }


def validity_date(runtime, date_, term):
    """
    Compute the validity date of a run given runtime and term

    :param runtime: Runtime
    :type runtime: Float
    :param date_: Run time day
    :type date_: datetime
    :param term: Term
    :type term: Float
    :return: datetime
    """
    return datetime.combine(date_, time(hour=runtime)) + timedelta(hours=term)


def dateiterator(date_start, date_end, first_term, last_term, delta_terms):
    current_date = date_start
    while current_date <= date_end:
        current_term = first_term
        while current_term <= last_term:
            yield (current_date, current_term)
            current_term += delta_terms
        current_date += timedelta(days=1)


class ComputedValues:
    """
    calcule les valeurs finales pour chaque date_, term
    """

    def __init__(
            self,
            folderLayout=None,
            delete_native=True,
            delete_computed_netcdf=True,
            domain=None,
            computed_vars=[],
            analysis_hour=None,
            autofetch_native=False,
            members=[None],
            model=None
    ):
        self.computed_vars = self.str2attrs(model, computed_vars)
        self.members = members
        self.domain = domain
        self.delete_native = delete_native
        self.delete_computed_netcdf = delete_computed_netcdf
        self.models = get_model_names(self.computed_vars)
        self.native_vars_by_model = sort_native_vars_by_model(self.computed_vars)
        self.analysis_hour = analysis_hour
        self.computed_files = defaultdict(lambda: [])
        self.folderLayout = folderLayout
        self.cache_managers = self._cache_managers(folderLayout, self.computed_vars, autofetch_native)
        self.model = model

    @staticmethod
    def str2attrs(model, variables):
        if model == "AROME":
            model_vars = arome
        elif model == "PEAROME":
            model_vars = pearome
        else:
            raise NotImplementedError(f"{model} is not implemented. Current model available are:"
                                      f"'AROME' and 'PEAROME'")
        return [getattr(model_vars, variable) for variable in variables]

    def _cache_managers(self, folderLayout, computed_vars, autofetch_native):
        """
        Creates a dictionary that contains "cache managers" for each model and member extracted

        :param folderLayout:
        :param computed_vars:
        :param autofetch_native:
        :return:
        """
        return {
            (model_name, member): AromeCacheManager(
                folderLayout=folderLayout,
                domain=self.domain,
                variables=native_vars,
                model=model_name,
                runtime=time(hour=self.analysis_hour),
                delete_native=self.delete_native,
                autofetch_native=autofetch_native,
                member=member
            )
            for model_name, native_vars in sort_native_vars_by_model(computed_vars).items()
            for member in self.members
        }

    @staticmethod
    def _delete_files_in_list_of_files(list_of_files):
        [os.remove(filename) for filename in list_of_files]

    # old save_final_netcd
    def _concat_files_and_save_netcdf(self, time_tag, member, domain):
        if self.computed_files[(member, domain)]:
            ds = xr.open_mfdataset(self.computed_files[(member, domain)], concat_dim='time')
            ds.to_netcdf(self.get_path_file_in_final(time_tag, member, domain))
        else:
            print(f"self.computed_files[(member, domain)] is empty")

    def _delete_and_forget_computed_files(self, member, domain):
        if self.delete_computed_netcdf:
            self._delete_files_in_list_of_files(self.computed_files[(member, domain)])
        if self.computed_files[(member, domain)]:
            del self.computed_files[(member, domain)]

    # old concat_files_and_forget
    def concat_and_clean_computed_folder(self, time_tag):
        for member in self.members:
            for domain in self.domain:
                self._concat_files_and_save_netcdf(time_tag, member, domain)
                self._delete_and_forget_computed_files(member, domain)

    def delete_files_in_cache(self):
        files = glob.glob(f'{self.folderLayout._cache_}/*')
        for f in files:
            os.remove(f)

    def clean_cache_folder(self):
        for cache_manager in self.cache_managers.values():
            cache_manager.forget_opened_files()
        self.delete_files_in_cache()

    # old get_file_hash
    def get_name_file_in_computed(self, date, term, member, domain):
        date_str = f"date_{date.strftime('%Y%m%d')}"
        run_str = f"runtime_{self.analysis_hour}h"
        term_str = f"term_{term}h"
        member_str = f"_mb{member:03d}" if member else ""
        filename = f"{self.model}_{date_str}_{run_str}_{term_str}_{domain}{member_str}.nc"
        return filename

    # old get_filepath
    def get_path_file_in_computed(self, date, term, member, domain):
        filepath = self.folderLayout._computed_
        filename = self.get_name_file_in_computed(date, term, member, domain)
        return os.path.join(filepath, filename)

    def get_path_file_in_final(self, time_tag, member, domain):
        filepath = self.folderLayout._final_
        str_member = f"_mb{member:03d}" if member else ""
        run_str = f"run_{self.analysis_hour}h"
        filename = f"{self.model}_{domain}_{time_tag}_{run_str}{str_member}.nc"
        return os.path.join(filepath, filename)

    @staticmethod
    def get_model_name_from_computed_var(computed_var):
        """Gives model name given input variable"""
        return computed_var.native_vars[0].model_name

    @staticmethod
    def save_computed_vars_to_netcdf(filepath_computed, variables_storage):
        computed_dataset = xr.Dataset({variable_name: variable_data
                                       for variable_name, variable_data in variables_storage.items()})
        computed_dataset = computed_dataset.expand_dims(dim='time').set_coords('time')
        computed_dataset.to_netcdf(filepath_computed)

    def _move_files_to_domain_folders(self):
        for domain in self.domain:
            # Create a folder for each domain
            path_domain = os.path.join(self.folderLayout._final_, domain)
            if not os.path.exists(path_domain):
                os.makedirs(path_domain)

            for file in os.listdir(self.folderLayout._final_):
                if (domain in file) and (file != domain):
                    current_path = os.path.join(self.folderLayout._final_, file)
                    new_path = os.path.join(path_domain, file)
                    os.rename(current_path, new_path)

    def _rename_final_folder(self):
        date_str = datetime.now().strftime("%Y_%m_%d_%H")
        id_ = str(uuid.uuid1())[:5]
        filename = f"HendrixExtraction_{date_str}_ID_{id_}"
        new_name = os.path.join(self.folderLayout.work_folder, filename)
        os.rename(self.folderLayout._final_, new_name)

    def clean_final_folder(self):
        self._move_files_to_domain_folders()
        self._rename_final_folder()

    def files_are_in_final(self, time_tag):

        # Look at files already computed
        files_in_final = []
        for member in self.members:
            for domain in self.domain:
                path_file_in_final = self.get_path_file_in_final(time_tag, member, domain)
                files_in_final.append(os.path.isfile(path_file_in_final))

        return any(files_in_final)

    def compute_variables_in_cache(self, computed_var, member, date, term, domain):

        # Parameters to read in cache
        model_name = self.get_model_name_from_computed_var(computed_var)
        read_cache_func = self.cache_managers[(model_name, member)].read_cache
        list_native_vars = computed_var.native_vars

        computed_values = computed_var.compute(read_cache_func, date, term, domain, *list_native_vars)
        return computed_values

    def delete_native_files(self):
        for cache_manager in self.cache_managers.values():
            # Delete .fa or .grib file after extraction of desired variables
            cache_manager.delete_native_files()

    def make_surfex_compliant(self):
        """Add necessary data for SURFEX"""
        for file in os.listdir(self.folderLayout._final_):
            filename = os.path.join(self.folderLayout._final_, file)
            ds = xr.open_dataset(filename)
            ds = ds.rename({"latitude": "LAT", "longitude": "LON"})
            ds.attrs["FORC_TIME_STEP"] = 3600
            xx = len(ds.xx)
            yy = len(ds.yy)
            time = len(ds.time)
            ds["CO2air"] = (("time", "xx", "yy"), np.full((time, xx, yy), 0.00062))
            if "Wind_DIR" not in ds:
                ds["Wind_DIR"] = (("time", "xx", "yy"), np.zeros((time, xx, yy)))
            ds["UREF"] = (("xx", "yy"), np.full((xx, yy), 10))
            ds["ZREF"] = (("xx", "yy"), np.full((xx, yy), 2))
            ds["slope"] = (("xx", "yy"), np.zeros((xx, yy)))
            ds["aspect"] = (("xx", "yy"), np.zeros((xx, yy)))
            ds["FRC_TIME_STP"] = 3600
            ds.to_netcdf(filename.split(".nc")[0]+"_tmp.nc", unlimited_dims={"time": True})
            os.remove(filename)
            os.rename(filename.split(".nc")[0]+"_tmp.nc", filename)

    def compute(self, date, term):
        for member in self.members:
            for domain in self.domain:

                # Look at files already computed
                path_file_in_computed = self.get_path_file_in_computed(date, term, member, domain)
                file_is_already_computed = os.path.isfile(path_file_in_computed)

                if file_is_already_computed:
                    self.computed_files[(member, domain)].append(path_file_in_computed)
                else:
                    # Store computed values before saving to netcdf
                    variables_storage = defaultdict(lambda: [])

                    # Iterate on variables asked by the user (i.e. computed var)
                    for computed_var in self.computed_vars:
                        computed_values = self.compute_variables_in_cache(computed_var, member, date, term, domain)
                        variables_storage[computed_var.name] = computed_values
                    variables_storage['time'] = validity_date(self.analysis_hour, date, term)

                    # Create netcdf file of computed values
                    self.save_computed_vars_to_netcdf(path_file_in_computed, variables_storage)

                    # Remember that current file is computed
                    self.computed_files[(member, domain)].append(path_file_in_computed)

            self.delete_native_files()
