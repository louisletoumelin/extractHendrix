from datetime import timedelta
import os
import copy
import logging
from contextlib import contextmanager
from datetime import time, datetime, timedelta
import time as timeutils
from collections import defaultdict

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
        """Constructor method"""
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
        ├── folder
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
    """
    """

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
        self.extractor = AromeHendrixReader(
            folderLayout, model, runtime, member)
        self.domain = domains[domain]
        self.variables = variables
        self.runtime = runtime
        self.autofetch_native = autofetch_native
        self.opened_files = {}

    def get_cache_path(self, date, term):
        return os.path.join(
            self.folderLayout._cache_,
            '.'.join([self.extractor.get_file_hash(date, term), 'nc'])
        )

    def extract_subgrid(self, field):
        """Extract pixels of an Epygram field corresponding to a user defined domain"""
        if self.extractor.model_name not in ['AROME', 'AROME_SURFACE']:
            x1, y1 = np.round(field.geometry.ll2ij(
                self.domain['lon_llc'], self.domain['lat_llc'])) + 1
            x2, y2 = np.round(field.geometry.ll2ij(
                self.domain['lon_urc'], self.domain['lat_urc'])) + 1
            field = field.extract_subarray(int(x1), int(x2), int(y1), int(y2))
        else:
            field = field.extract_subarray(
                self.domain['first_i'],
                self.domain['last_i'],
                self.domain['first_j'],
                self.domain['last_j']
            )
        return field

    @staticmethod
    def read_field_or_alternate_name(input_resource, variable):
        """Reads an Epygram field (=variable). Uses alternative name if original names are not found in the file"""
        initial_name = variable

        try:
            field = input_resource.readfield(variable.name)
            return field
        except AssertionError:
            if variable in alternatives_names_fa:
                alternatives_names = copy.deepcopy(
                    alternatives_names_fa[variable])
                while alternatives_names:
                    try:
                        variable = alternatives_names.pop(0)
                        field = input_resource.readfield(variable)
                        field.fid["FA"] = initial_name
                        logger.warning(
                            f"Found an alternative name for {initial_name} that works: {variable}\n\n")
                        return field
                    except AssertionError:
                        logger.error(
                            f"Alternative name {variable} didn't work for variable {initial_name}\n\n")
                        pass
                logger.error(
                    f"We coulnd't find correct alternative names for {initial_name}\n\n")
                raise CanNotReadEpygramField(
                    f"We couldn't find correct alternative names for {initial_name}")
            else:
                logger.error(f"We couldn't read {initial_name}\n\n")
                raise CanNotReadEpygramField(
                    f"We couldn't read {initial_name}")

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
        native_file_path = self.extractor.get_native_file(
            date, term, autofetch=self.autofetch_native)
        input_resource = epygram.formats.resource(
            native_file_path,
            'r',
            fmt=self.extractor.fmt.upper())
        return native_file_path, input_resource

    def put_in_cache(self, date, term):
        """
        Builds a single netcdf file corresponding to a single fa or grib file.

        :param term: forecast leadtime
        :type term: int
        # TODO: would be nice if hendrix reader could return each variable in a fixed format,
        this way the cache manager wouldn't depend on the file's format
        """
        native_file_path, input_resource = self.get_native_resource(date, term)
        cache_path = self.get_cache_path(date, term)
        if os.path.isfile(cache_path):
            return
        output_resource = epygram.formats.resource(
            cache_path,
            'w',
            fmt='netCDF')
        output_resource.behave(
            N_dimension='Number_of_points', X_dimension='xx', Y_dimension='yy')
        for variable in self.variables:
            field = self.read_field_or_alternate_name(input_resource, variable)
            field = self.pass_metadata_to_netcdf(field, variable.outname)
            if field.spectral:
                field.sp2gp()
            field = self.extract_subgrid(field)
            output_resource.writefield(field)
        logger.debug(
            f"Successfully converted a fa file to netcdf for term {term}\n\n")
        if self.delete_native:
            os.remove(native_file_path)

    def open_file_as_dataset(self, date, term):
        filepath = self.get_cache_path(date, term)
        if filepath not in self.opened_files:
            dataset = xr.open_dataset(filepath).set_coords(self.coordinates)
            self.opened_files[filepath] = dataset
        return self.opened_files[filepath]

    def close_file(self, date, term):
        filepath = self.get_cache_path(date, term)
        file = self.opened_files[filepath]
        file['dataset'].close()
        del self.opened_files[filepath]

    def read_cache(self, date, term, variable):
        cache_path = self.get_cache_path(date, term)
        if not os.path.isfile(cache_path):
            self.put_in_cache(date, term)
        dataset = self.open_file_as_dataset(date, term)
        return dataset[variable.outname]


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
            delete_individuals=True,
            domain=None,
            computed_vars=[],
            analysis_hour=None,
            autofetch_native=False,
            members=[None]
    ):
        self.computed_vars = computed_vars
        self.members = members
        self.domain = domain
        self.delete_native = delete_native
        self.delete_individuals = delete_individuals
        self.models = get_model_names(computed_vars)
        self.native_vars_by_model = sort_native_vars_by_model(computed_vars)
        self.analysis_hour = analysis_hour
        self.computed_files = defaultdict(lambda: [])
        self.folderLayout = folderLayout
        self.cache_managers = self._cache_managers(
            folderLayout, computed_vars, autofetch_native)

    def _cache_managers(self, folderLayout, computed_vars, autofetch_native):
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

    def get_concatenated_filename(self, fileroot, member):
        hash_ = "final_{fileroot}_run_{runtime}h{memberstr}.nc".format(
                fileroot=fileroot,
                runtime=self.analysis_hour,
                memberstr="_mb{member:03d}".format(
                    member=member) if member else ""
        )
        return os.path.join(
            self.folderLayout._final_,
            hash_
        )

    def concat_files_and_forget(self, fileroot):
        for member in self.members:
            ds = xr.open_mfdataset(
                self.computed_files[member],
                concat_dim='time')
            ds.to_netcdf(self.get_concatenated_filename(fileroot, member))
            if self.delete_individuals:
                [os.remove(filename)
                 for filename in self.computed_files[member]]
            del self.computed_files[member]

    def get_file_hash(self, date, term, member):
        hash_ = "run_{date}T{runtime}-00-00Z-term_{term}h{memberstr}.nc".format(
            date=date.strftime("%Y%m%d"),
            runtime=self.analysis_hour,
            term=term,
            memberstr="_mb{member:03d}".format(member=member) if member else ""
        )
        return hash_

    def get_filepath(self, date, term, member):
        return os.path.join(
            self.folderLayout._computed_,
            self.get_file_hash(date, term, member)
        )

    def compute(self, date, term):
        for member in self.members:
            if os.path.isfile(self.get_filepath(date, term, member)):
                self.computed_files[member].append(
                    self.get_filepath(date, term, member)
                )
                continue
            variables_storage = defaultdict(lambda: [])
            for computed_var in self.computed_vars:
                model_name = computed_var.native_vars[0].model_name
                computed_values = computed_var.compute(
                    self.cache_managers[(model_name, member)].read_cache,
                    date,
                    term,
                    *computed_var.native_vars
                )
                variables_storage[computed_var.name] = computed_values
            variables_storage['time'] = validity_date(
                self.analysis_hour, date, term)
            final_dataset = xr.Dataset(
                {
                    variable_name: variable_data
                    for variable_name, variable_data in variables_storage.items()
                }
            )
            final_dataset = (
                final_dataset
                .expand_dims(dim='time')
                .set_coords('time')
            )
            filepath = self.get_filepath(date, term, member)
            final_dataset.to_netcdf(filepath)
            self.computed_files[member].append(
                self.get_filepath(date, term, member)
            )
