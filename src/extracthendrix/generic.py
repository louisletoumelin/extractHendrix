from datetime import timedelta
import os
import copy
import logging
from contextlib import contextmanager
from datetime import time, datetime, timedelta
import time as timeutils
from collections import defaultdict
import glob

import numpy as np
import epygram
import xarray as xr
from extracthendrix.hendrix_emails import send_problem_extraction_email, send_script_stopped_email

from extracthendrix.readers import AromeHendrixReader
from extracthendrix.config.domains import domains
from extracthendrix.config.config_fa_or_grib2nc import alternatives_names_fa
from extracthendrix.exceptions import CanNotReadEpygramField

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
        self.domain = domains[domain]
        self.variables = variables
        self.runtime = runtime
        self.autofetch_native = autofetch_native
        self.opened_files = {}

    # old get_cache_path
    def get_path_file_in_cache(self, date, term):
        """
        Return full path to file in cache for a given run time and forecast lead time

        :param date: Run time
        :type date: datetime
        :param term: forecast leadtime
        :type term: int
        :return: str
        """
        filename = self.extractor.get_file_hash(date, term)
        filename = f"{filename}.nc"
        folder = self.folderLayout._cache_
        return os.path.join(folder, filename)

    def extract_subgrid(self, field):
        """Extract pixels of an Epygram field corresponding to a user defined domain"""
        if self.extractor.model_name not in ['AROME', 'AROME_SURFACE']:
            i1, j1 = np.round(field.geometry.ll2ij(self.domain['lon_llc'], self.domain['lat_llc'])) + 1
            i2, j2 = np.round(field.geometry.ll2ij(self.domain['lon_urc'], self.domain['lat_urc'])) + 1
            field = field.extract_subarray(int(i1), int(i2), int(j1), int(j2))
        else:
            field = field.extract_subarray(
                self.domain['first_i'],
                self.domain['last_i'],
                self.domain['first_j'],
                self.domain['last_j'])
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

    def get_native_resource(self, date, term):
        native_file_path = self.extractor.get_native_file(date, term, autofetch=self.autofetch_native)
        input_resource = epygram.formats.resource(native_file_path, 'r', fmt=self.extractor.fmt.upper())
        return native_file_path, input_resource

    def put_in_cache(self, date, term):
        """
        Builds a single netcdf file corresponding to a single fa or grib file.

        :param term: forecast leadtime
        :type term: int
        # TODO: would be nice if hendrix reader could return each variable in a fixed format,
        this way the cache manager wouldn't depend on the file's format
        """

        # Check if file is already in cache
        filepath_in_cache = self.get_path_file_in_cache(date, term)
        if os.path.isfile(filepath_in_cache):
            return

        # Download file on Hendrix if necessary
        native_file_path, input_resource = self.get_native_resource(date, term)

        # Open Epygram resource
        output_resource = epygram.formats.resource(filepath_in_cache, 'w', fmt='netCDF')
        output_resource.behave(N_dimension='Number_of_points', X_dimension='xx', Y_dimension='yy')

        # Extract variable from native file (i.e. .fa or .grib)
        for variable in self.variables:
            field = self.read_field_or_alternate_name(input_resource, variable)
            field = self.pass_metadata_to_netcdf(field, variable.outname)
            if field.spectral:
                field.sp2gp()
            field = self.extract_subgrid(field)
            output_resource.writefield(field)
        logger.debug(f" .fa or .grib file converted to netcdf for date {date} and term {term}\n\n")

        # Delete .fa or .grib file after extraction of desired variables
        if self.delete_native:
            os.remove(native_file_path)

    def get_file_in_cache(self, filepath):
        if filepath not in self.opened_files:
            self.open_and_store_file(filepath)
        return self.opened_files[filepath]

    def open_and_store_file(self, filepath):
        dataset = xr.open_dataset(filepath).set_coords(self.coordinates)
        self.opened_files[filepath] = dataset

    def forget_opened_files(self):
        del self.opened_files

    def close_file(self, date, term):
        """Not used"""
        filepath = self.get_path_file_in_cache(date, term)
        file = self.opened_files[filepath]
        file['dataset'].close()
        del self.opened_files[filepath]

    def read_cache(self, date, term, native_variables):
        # Check file in cache and download if necessary
        filepath_in_cache = self.get_path_file_in_cache(date, term)
        file_is_not_in_cache = not os.path.isfile(filepath_in_cache)
        if file_is_not_in_cache:
            self.put_in_cache(date, term)

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
        self.computed_vars = computed_vars  # i.e. variables given by the user (e.g. 'Tair' and not 'CLSTEMPERATURE)
        self.members = members
        self.domain = domain
        self.delete_native = delete_native
        self.delete_computed_netcdf = delete_computed_netcdf
        self.models = get_model_names(computed_vars)
        self.native_vars_by_model = sort_native_vars_by_model(computed_vars)
        self.analysis_hour = analysis_hour
        self.computed_files = defaultdict(lambda: [])
        self.folderLayout = folderLayout
        self.cache_managers = self._cache_managers(folderLayout, computed_vars, autofetch_native)
        self.model = model

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
    def _concat_files_and_save_netcdf(self, time_tag, member):
        ds = xr.open_mfdataset(self.computed_files[member], concat_dim='time')
        ds.to_netcdf(self.get_path_file_in_final(time_tag, member))

    def _delete_and_forget_computed_files(self, member):
        if self.delete_computed_netcdf:
            self._delete_files_in_list_of_files(self.computed_files[member])
        del self.computed_files[member]

    # old concat_files_and_forget
    def concat_and_clean_computed_folder(self, time_tag):
        for member in self.members:
            self._concat_files_and_save_netcdf(time_tag, member)
            self._delete_and_forget_computed_files(member)

    def delete_files_in_cache(self):
        files = glob.glob(f'{self.folderLayout._cache_}/*')
        for f in files:
            os.remove(f)

    def clean_cache_folder(self):
        for cache_manager in self.cache_managers:
            cache_manager.forget_opened_files()
        self.delete_files_in_cache()

    # old get_file_hash
    def get_name_file_in_computed(self, date, term, member):
        member_str = f"_mb{member:03d}" if member else ""
        filename = f"run_{date.strftime('%Y%m%d')}T{self.analysis_hour}-00-00Z-term_{term}h{member_str}.nc"
        return filename

    # old get_filepath
    def get_path_file_in_computed(self, date, term, member, domain):
        filepath = self.folderLayout._computed_
        filename = self.get_name_file_in_computed(date, term, member)
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

    def compute_variables_in_cache(self, computed_var, member, date, term):

        # Parameters to read in cache
        model_name = self.get_model_name_from_computed_var(computed_var)
        read_cache_func = self.cache_managers[(model_name, member)].read_cache
        list_native_vars = computed_var.native_vars

        computed_values = computed_var.compute(read_cache_func, date, term, *list_native_vars)
        return computed_values

    def compute(self, date, term):
        for member in self.members:
            for domain in self.domain:

                # Look at files already computed
                path_file_in_computed = self.get_path_file_in_computed(date, term, member)
                file_is_already_computed = os.path.isfile(path_file_in_computed)

                if file_is_already_computed:
                    self.computed_files[member].append(path_file_in_computed)
                else:
                    # Store computed values before saving to netcdf
                    variables_storage = defaultdict(lambda: [])

                    # Iterate on variables asked by the user (i.e. computed var)
                    for computed_var in self.computed_vars:
                        computed_values = self.compute_variables_in_cache(computed_var, member, date, term)
                        variables_storage[computed_var.name] = computed_values
                    variables_storage['time'] = validity_date(self.analysis_hour, date, term)

                    # Create netcdf file of computed values
                    self.save_computed_vars_to_netcdf(path_file_in_computed, variables_storage)

                    # Remember that current file is computed
                    self.computed_files[member].append(path_file_in_computed)
