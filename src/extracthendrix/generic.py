import os
import copy
import logging
from datetime import datetime, timedelta
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
from extracthendrix.exceptions import CanNotReadEpygramField
from extracthendrix.config.variables import arome, pearome, arome_analysis, arpege, arpege_analysis_4dvar, pearp

logging.getLogger("footprints").setLevel("CRITICAL")
logging.getLogger('vortex').setLevel("CRITICAL")
logging.getLogger('epygram').setLevel("CRITICAL")
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class FolderLayout:
    """
    Creates a folder and four temporary subfolders where files are stored.

    :param work_folder: Path to main folder where extraction is done
    :type work_folder: str
    """

    def __init__(self, work_folder, create_subfolders=True):
        self.work_folder = work_folder
        self.create_layout(create_subfolders)

    @staticmethod
    def create_folder_if_doesnt_exist(path):
        """Create a folder if it doesn't already exists

        :param path: Folder path
        :type path: str
        """
        try:
            os.mkdir(path)
        except FileExistsError:
            logger.info(f"[FOLDER LAYOUT] Folder {path} already exists")

    def create_layout(self, create_subfolders=True):
        """
        Creates folder and subfolders for the current extraction

        ├── work_folder
        │   ├── _native_
        │   ├── _cache_
        │   ├── _computed_
        │   ├── _final_
        """
        # Parent folder
        self.create_folder_if_doesnt_exist(self.work_folder)

        # Subfolders
        if create_subfolders:
            for subfolder in ['_native_', '_cache_', '_computed_', '_final_']:
                setattr(self, subfolder, os.path.join(
                    self.work_folder, subfolder))
                self.create_folder_if_doesnt_exist(getattr(self, subfolder))

    def clean_layout(self):
        """Removes subfolders in work_folder"""
        for subfolder in ['_native_', '_cache_', '_computed_']:
            shutil.rmtree(getattr(self, subfolder))


class AromeCacheManager:
    """
    A class that deals with data in cache and eventually triggers downloading.
    """

    def __init__(
            self,
            folderLayout,
            domain=None,
            native_variables=[],
            alternative_names={},
            model=None,
            delete_native=True,
            member=None,
            autofetch_native=False
    ):
        """
        :param folderLayout: instance of the class FolderLayout. Gives information about the working directory.
        :param domain: List of geographical domains (e.g. ["alps", "pyr"])
        :type domain: str
        :param native_variables: list of model native variables
        :type native_variables: list
        :param model: Model name
        :type model: str
        :param delete_native: Delete native files when creating cache if finished.
        :type delete_native: Bool
        :param member: Member number
        :type member: int
        :param autofetch_native: Raises an exception if False, for testing purposes, because extraction on Hendrix
        is slow
        :type autofetch_native: Bool
        """
        self.folderLayout = folderLayout
        self.delete_native = delete_native
        self.coordinates = ['latitude', 'longitude']
        self.extractor = AromeHendrixReader(folderLayout, model, member)
        self.domain = domain
        self.native_variables = native_variables
        self.alternative_names = alternative_names
        self.autofetch_native = autofetch_native
        self.opened_files = {}

    # old get_cache_path
    def get_path_file_in_cache(self, date, term, domain):
        """
        Return full path to file in cache for a given run and forecast lead time.

        :param date: Run time
        :type date: datetime
        :param term: forecast leadtime
        :type term: int
        :param domain: Model name
        :type domain: str
        :return: str
        """
        filename = self.extractor.get_file_hash(date, term)
        filename = f"{filename}_{domain}.nc"
        folder = self.folderLayout._cache_
        return os.path.join(folder, filename)

    def extract_subgrid(self, field, domain):
        """
        Extract pixels of an Epygram field corresponding to a user defined domain

        :param field: Epygram field
        :param domain: Geographical domain name
        """
        domain_description = domains_descriptions[domain]
        if self.extractor.model_name not in ['AROME', 'AROME_SURFACE']:
            i1, j1 = np.round(field.geometry.ll2ij(
                domain_description['lon_llc'], domain_description['lat_llc'])) + 1
            i2, j2 = np.round(field.geometry.ll2ij(
                domain_description['lon_urc'], domain_description['lat_urc'])) + 1
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
        """
        Reads an Epygram field (=variable). Uses alternative name if original names are not found in the file

        :param input_resource: Epygram/Vortex resource
        :param variable: native variable name
        :return: Epygram field
        """
        initial_name = variable
        try:
            field = input_resource.readfield(variable.name)
            return field
        except AssertionError:
            if variable.alternative_names:
                alternatives_names = copy.deepcopy(variable.alternative_names)
                while alternatives_names:
                    try:
                        variable = alternatives_names.pop(0)
                        field = input_resource.readfield(variable)
                        field.fid["FA"] = initial_name
                        logger.info(
                            f"[CACHE MANAGER] Aternative name for {initial_name.name} works: {variable}")
                        return field
                    except AssertionError:
                        logger.info(f"[CACHE MANAGER] Alternative name {variable} "
                                    f"didn't work for variable {initial_name.name}")
                        pass
                logger.error(
                    f"[CACHE MANAGER] No correct alternative names for {initial_name}")
                raise CanNotReadEpygramField(
                    f"We couldn't find correct alternative names for {initial_name}")
            else:
                logger.error(
                    f"[CACHE MANAGER] We couldn't read {initial_name}")
                raise CanNotReadEpygramField(
                    f"We couldn't read {initial_name}")

    @staticmethod
    def pass_metadata_to_netcdf(field, outname=None):
        """
        Pass metadata from fa file to netcdf file

        :param field: Epygram field
        :param outname: output name
        :return: Epygram field
        """
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
        """
        Triggers extractor and download on hendrix only if necessary

        :param date: current date
        :param term: forecast lead time
        :return: path of the native file, Epygram resource
        """
        native_file_path = self.extractor.get_native_file(
            date, term, autofetch=self.autofetch_native)
        input_resource = epygram.formats.resource(
            native_file_path, 'r', fmt=self.extractor.fmt.upper())
        return native_file_path, input_resource

    def put_in_cache(self, date, term, domain):
        """
        Creates a netcdf file for each forecast lead time or analysis date,
        with only the requested variables on a subdomain.

        This permits to store intermediate data and to easily relaunch extraction if necessary.

        :param date: Run date
        :param term: Forecast leadtime
        :param domain: Geographical domain name
        # TODO: would be nice if hendrix reader could return each variable in a fixed format,
        #this way the cache manager wouldn't depend on the file's format
        """

        # Check if file is already in cache
        filepath_in_cache = self.get_path_file_in_cache(date, term, domain)
        if os.path.isfile(filepath_in_cache) and self.autofetch_native:
            return

        # Initialize netcdf file
        output_resource = epygram.formats.resource(
            filepath_in_cache, 'w', fmt='netCDF')
        output_resource.behave(
            N_dimension='Number_of_points', X_dimension='xx', Y_dimension='yy')

        # Download file on Hendrix if necessary
        native_file_path, input_resource = self.get_native_resource_if_necessary(
            date, term)

        # Extract variable from native file (i.e. .fa or .grib)
        for variable in self.native_variables:
            field = self.read_field_or_alternate_name(input_resource, variable)
            field = self.pass_metadata_to_netcdf(field, variable.outname)
            if field.spectral:
                field.sp2gp()
            field = self.extract_subgrid(field, domain)
            output_resource.writefield(field)
        logger.debug(f"[CACHE MANAGER] {self.extractor.fmt.upper()} file extracted and saved in cache for date {date}, "
                     f"term {term}, "
                     f"domain {domain}.")
        logger.debug(f"Filepath: {filepath_in_cache}")

    def get_file_in_cache(self, filepath):
        """
        Returns data in cache as a xarray dataset.
        Store previously opened dataset in order to prevent opening several times the same file.

        :param filepath: Path to file
        :return: xarray dataset
        """
        if filepath not in self.opened_files:
            self.open_and_store_file(filepath)
        return self.opened_files[filepath]

    def open_and_store_file(self, filepath):
        """
        Open netcdf file in cache folder as a xarray dataset.

        :param filepath: Path to file
        """
        dataset = xr.open_dataset(filepath)
        dataset = dataset.set_coords(self.coordinates)
        self.opened_files[filepath] = dataset

    def forget_opened_files(self):
        """Reinitialize dictionary that stored opened netcdf files in cache to release RAM."""
        self.opened_files = {}

    def close_file(self, date, term, domain):
        """Not used"""
        filepath = self.get_path_file_in_cache(date, term, domain)
        file = self.opened_files[filepath]
        file['dataset'].close()
        del self.opened_files[filepath]

    def delete_native_files(self):
        """Delete .fa or .grib files (i.e. native files) after extraction of desired variables"""
        if self.delete_native:
            files = glob.glob(f'{self.folderLayout._native_}/*')
            for f in files:
                os.remove(f)

    def read_cache(self, date, term, domain, native_variables):
        """
        Read data in cache folder if available, or download it instead.

        :param date: Run date
        :param term: Forecast lead time
        :param domain: Geographical domain
        :param native_variables: Name of native variable to read
        :return: Data as a xarray dataset
        """
        # Check file in cache and download if necessary
        filepath_in_cache = self.get_path_file_in_cache(date, term, domain)
        file_is_not_in_cache = not os.path.isfile(filepath_in_cache)
        if file_is_not_in_cache:
            logger.debug(f"[CACHE MANAGER] {native_variables.name}: "
                         f"{date}, "
                         f"term {term}, "
                         f"domain {domain} NOT in cache")
            self.put_in_cache(date, term, domain)
        else:
            logger.debug(f"[CACHE MANAGER] {native_variables.name}: "
                         f"{date}, "
                         f"term {term}, "
                         f"domain {domain} already in cache")

        # Return the file from cache
        dataset = self.get_file_in_cache(filepath_in_cache)
        return dataset[native_variables.outname]


def get_model_names(computed_vars):
    """
    Returns models names associate with native variables (e.g. "AROME", "AROME_SURFACE"...)
    :param computed_vars: Name of computed variable (e.g. "Tair" and not "CLSTEMPERATURE" for 2m temperature)
    :return: Dictionary with model names
    """
    return {ivar.model_name for var in computed_vars for ivar in var.native_vars}


def sort_native_vars_by_model(computed_vars):
    """
    Get all native variables sorted by model.

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


def validity_date(date_, term):
    """
    Compute the validity date of a run given run and term

    :param run: run
    :type run: Float
    :param date_: Run time day
    :type date_: datetime
    :param term: Term
    :type term: Float
    :return: datetime
    """
    if term is None:
        return date_
    else:
        return date_ + timedelta(hours=term)


def get_variable_instances(model, computed_variables):
    """
    Link a model name to the object containing information about the model variables.

    :param model: Model name.
    :param variables: Computed variables names (e.g. "Tair" and not "CLSTEMPERATURE").
    :return: List of model variables.
    """
    logger.info(f"Asked for model: {model}. Models available:"
                f"'AROME', 'AROME_analysis', 'PEAROME', 'ARPEGE', 'ARPEGE_analysis_4dvar', 'PEARP'")
    # Look at all variables, and class instances imported and select the one corresponding to the model
    model_vars = globals()[model.lower()]
    # If we need surface variables, the model becomes a list of native models (e.g. AROME = AROME + SURFEX)
    model_and_submodels = [getattr(model_vars, variable)
                           for variable in computed_variables]
    return model_and_submodels


class ComputedValues:
    """
    Compute variables in cache and store computed values in netcdf format.
    """

    def __init__(
            self,
            folderLayout=None,
            delete_native=True,
            delete_computed_netcdf=True,
            domain=None,
            computed_vars=[],
            autofetch_native=False,
            members=[None],
            model=None,
            dtype=None,
    ):
        """
        :param folderLayout: instance of the class FolderLayout. Gives information about the working directory.
        :param delete_native: Delete native files when creating cache if finished.
        :param delete_computed_netcdf: Delete computed netcdf files in _computed_ folder when computation is finished.
        :param domain: Geographical domain name.
        :param computed_vars: Name of computed variables (e.g. "Tair" and not "CLSTEMPERATURE")
        :param autofetch_native: Raises an exception if False, for testing purposes, because extraction on Hendrix
        is slow.
        :param members: Member number?
        :param model: Model name.
        """
        self.computed_vars = get_variable_instances(model, computed_vars)
        self.members = members
        self.domain = domain
        self.delete_native = delete_native
        self.delete_computed_netcdf = delete_computed_netcdf
        self.models = get_model_names(self.computed_vars)
        self.native_vars_by_model = sort_native_vars_by_model(
            self.computed_vars)
        self.computed_files = defaultdict(lambda: [])
        self.folderLayout = folderLayout
        self.cache_managers = self._cache_managers(
            folderLayout, self.computed_vars, autofetch_native)
        self.model = model
        self.dtype = dtype

    def _cache_managers(self, folderLayout, computed_vars, autofetch_native):
        """
        Creates a dictionary that contains "cache managers" for each model and member extracted

        :param folderLayout: instance of the class FolderLayout. Gives information about the working directory.
        :param computed_vars: Name of computed variable (e.g. "Tair" and not "CLSTEMPERATURE" for 2m temperature)
        :param autofetch_native: Raises an exception if False, for testing purposes, because extraction on Hendrix
        :return: Dictionary containing cache managers
        """
        return {
            (model_name, member): AromeCacheManager(
                folderLayout=folderLayout,
                domain=self.domain,
                native_variables=native_vars,
                alternative_names={
                    var: var.alternative_names for var in native_vars},
                model=model_name,
                delete_native=self.delete_native,
                autofetch_native=autofetch_native,
                member=member
            )
            for model_name, native_vars in sort_native_vars_by_model(computed_vars).items()
            for member in self.members
        }

    @staticmethod
    def _delete_files_in_list_of_files(list_of_files):
        """
        Deletes files given paths of the files

        :param list_of_files: List of path to files
        """
        [os.remove(filename) for filename in list_of_files]

    # old save_final_netcd
    def _concat_files_and_save_netcdf(self, time_tag, member, domain):
        """
        Save computed files to netcdf in _final_ folder.

        :param time_tag: Runtime.
        :param member: Member number.
        :param domain: Geographical domain name.
        """
        if self.computed_files[(member, domain)]:
            ds = xr.open_mfdataset(
                self.computed_files[(member, domain)], concat_dim='time')
            if self.dtype == "32bits":
                ds = ds.astype(np.float32)
            filepath = self.get_path_file_in_final(time_tag, member, domain)
            ds.to_netcdf(filepath)
            logger.debug(f"[COMPUTER] Saved file: {filepath}")
        else:
            logger.info(
                f"[COMPUTER] self.computed_files[(member, domain)] is empty")

    def _delete_and_forget_computed_files(self, member, domain):
        """
        Reinitialize list that stored opened netcdf files in cache to release RAM.

        :param member: Member number.
        :param domain: Geographical domain name.
        """
        if self.delete_computed_netcdf:
            self._delete_files_in_list_of_files(
                self.computed_files[(member, domain)])
        if self.computed_files[(member, domain)]:
            del self.computed_files[(member, domain)]

    # old concat_files_and_forget
    def concat_and_clean_computed_folder(self, time_tag):
        """
        Concat files that forms a group of computed files as specified by the user (e.g. daily, monthly...).

        Delete files in the _computed_ folder (they are now in grouped in the _final_ folder)
        and release RAM from opened file.

        :param time_tag: Run time
        """
        for member in self.members:
            for domain in self.domain:
                self._concat_files_and_save_netcdf(time_tag, member, domain)
                self._delete_and_forget_computed_files(member, domain)

    def delete_files_in_cache(self):
        """Delete files in _cache_ folder"""
        files = glob.glob(f'{self.folderLayout._cache_}/*')
        for f in files:
            os.remove(f)

    def clean_cache_folder(self):
        """Reinitialize dictionaries that stored opened netcdf files in cache to release RAM and delete files
        in _cache_ folder"""
        for cache_manager in self.cache_managers.values():
            cache_manager.forget_opened_files()
        self.delete_files_in_cache()

    # old get_file_hash
    def get_name_file_in_computed(self, date, term, member, domain):
        """
        Get name of current file in _computed_ folder.

        :param date: Run date.
        :param term: Forecast lead time.
        :param member: Member number.
        :param domain: Geographical domain.
        :return: filename
        """
        date_str = f"date_{date.strftime('%Y%m%d%H')}"
        term_str = f"_term_{term}" if term is not None else ""
        member_str = f"_mb{member:03d}" if member else ""
        filename = f"{self.model}_{date_str}{term_str}_{domain}{member_str}.nc"
        return filename

    # old get_filepath
    def get_path_file_in_computed(self, date, term, member, domain):
        """
        Return path of the file in _computed_ for the corresponding date/term/member/domain combination.

        :param date: Run time.
        :param term: Forecast lead time.
        :param member: Member number.
        :param domain: Geographical domain.
        :return: Path of the file
        """
        filepath = self.folderLayout._computed_
        filename = self.get_name_file_in_computed(date, term, member, domain)
        return os.path.join(filepath, filename)

    def get_path_file_in_final(self, time_tag, member, domain):
        """
        Return path of the file in _çfinal_ for the corresponding date/term/member/domain combination.

        :param time_tag: Run time.
        :param member: Member number.
        :param domain: Geographical domain.
        :return: Path of the file
        """
        filepath = self.folderLayout._final_
        str_member = f"_mb{member:03d}" if member else ""
        filename = f"{self.model}_{domain}_{time_tag}{str_member}.nc"
        return os.path.join(filepath, filename)

    @staticmethod
    def get_model_name_from_computed_var(computed_var):
        """Gives model name given computed variable (e.g. 'Tair' and not 'CLSTEMPERATURE')"""
        return computed_var.native_vars[0].model_name

    def save_computed_vars_to_netcdf(self, filepath_computed, variables_storage):
        """
        Save computed files in _computed_ folder.

        e.g. Wind speed computed from .fa or .grib native files using wind components.

        :param filepath_computed: File path to save data.
        :param variables_storage: Dictionary where are temporarily stored computed data.
        """
        computed_dataset = xr.Dataset({variable_name: variable_data
                                       for variable_name, variable_data in variables_storage.items()})
        computed_dataset = computed_dataset.expand_dims(
            dim='time').set_coords('time')
        if self.dtype == "32bits":
            computed_dataset = computed_dataset.astype(np.float32)
        computed_dataset.to_netcdf(filepath_computed)
        logger.debug(f"[COMPUTER] Saved file: {filepath_computed}")

    def _move_files_to_domain_folders(self):
        """Move files from _final_ folder to a domain specific foilder (e.g; "alps/") when computations are finished."""
        for domain in self.domain:
            # Create a folder for each domain
            path_domain = os.path.join(self.folderLayout._final_, domain)
            if not os.path.exists(path_domain):
                os.makedirs(path_domain)

            for file in os.listdir(self.folderLayout._final_):
                if (domain in file) and (file != domain):
                    current_path = os.path.join(
                        self.folderLayout._final_, file)
                    new_path = os.path.join(path_domain, file)
                    os.rename(current_path, new_path)

    def _rename_final_folder(self):
        """
        Rename _final_ folder into 'HendriExtraction_{Y_m_d_H}_ID_{ID}

        The ID is a random uuid and permits to performs several extraction with extracthendrix in the same folder
        without deleting folders used in former extractions.
        '"""
        date_str = datetime.now().strftime("%Y_%m_%d_%H")
        id_ = str(uuid.uuid1())[:5]
        filename = f"HendrixExtraction_{date_str}_ID_{id_}"
        new_name = os.path.join(self.folderLayout.work_folder, filename)
        os.rename(self.folderLayout._final_, new_name)

    def clean_final_folder(self):
        """
        Move files into domain specific folders and rename _final_ folder

        e.g. for an extraction of the french Alps and Switzerland:
        ├── _final_
        │   ├── alps
        │   ├── swiss
        """
        self._move_files_to_domain_folders()
        self._rename_final_folder()

    def files_are_in_final(self, time_tag):
        """Check if files are already downloaded in _final folder for specific time (time_tag)"""
        # Look at files already computed
        files_in_final = []
        for member in self.members:
            for domain in self.domain:
                path_file_in_final = self.get_path_file_in_final(
                    time_tag, member, domain)
                files_in_final.append(os.path.isfile(path_file_in_final))

        return any(files_in_final)

    def compute_variables_in_cache(self, computed_var, member, date, term, domain):
        """
        Trigger computation in cache.

        :param computed_var: Name of computed variables (e.g. "Tair" and not "CLSTEMPERATURE").
        :param member: Member number.
        :param date: Run time.
        :param term: Forecast lead time.
        :param domain: Geographical domain name.
        :return: xarray dataset.
        """
        # Parameters to read in cache
        model_name = self.get_model_name_from_computed_var(computed_var)
        read_cache_func = self.cache_managers[(model_name, member)].read_cache
        list_native_vars = computed_var.native_vars

        computed_values = computed_var.compute(
            read_cache_func, date, term, domain, *list_native_vars)
        return computed_values

    def delete_native_files(self):
        """Delete files in native folder."""
        for cache_manager in self.cache_managers.values():
            # Delete .fa or .grib file after extraction of desired variables
            cache_manager.delete_native_files()

    def make_surfex_compliant(self):
        """Add necessary data for SURFEX"""
        for file in os.listdir(self.folderLayout._final_):
            filename = os.path.join(self.folderLayout._final_, file)
            ds = xr.open_dataset(filename)

            # Rename Latitude and longitude
            ds = ds.rename({"latitude": "LAT", "longitude": "LON"})

            # Add forcing time step as an attribute
            ds.attrs["FORC_TIME_STEP"] = 3600

            # Add new variables: CO2air, UREF, ZREF, slope, aspect and FRC_TIME_STP
            xx = len(ds.xx)
            yy = len(ds.yy)
            time = len(ds.time)
            ds["CO2air"] = (("time", "xx", "yy"),
                            np.full((time, xx, yy), 0.00062))
            if "Wind_DIR" not in ds:
                ds["Wind_DIR"] = (("time", "xx", "yy"),
                                  np.zeros((time, xx, yy)))
            ds["UREF"] = (("xx", "yy"), np.full((xx, yy), 10))
            ds["ZREF"] = (("xx", "yy"), np.full((xx, yy), 2))
            ds["slope"] = (("xx", "yy"), np.zeros((xx, yy)))
            ds["aspect"] = (("xx", "yy"), np.zeros((xx, yy)))
            ds["FRC_TIME_STP"] = 3600

            # Save file to netcdf
            if self.dtype == "32bits":
                ds = ds.astype(np.float32)
            ds.to_netcdf(filename.split(".nc")[
                         0]+"_tmp.nc", unlimited_dims={"time": True})
            os.remove(filename)
            os.rename(filename.split(".nc")[0]+"_tmp.nc", filename)

    def compute(self, run, term):
        """
        Triggers computation of computed variables (i.e. variables asked by the user)

        :param run: Run time.
        :param term: Forecast lead time (None for analysis).
        """
        for member in self.members:
            for domain in self.domain:

                # Look at files already computed
                path_file_in_computed = self.get_path_file_in_computed(
                    run, term, member, domain)
                file_is_already_computed = os.path.isfile(
                    path_file_in_computed)

                member_str = f", member {member}" if member else ""
                computer_str = f"[COMPUTER] {run}, term {term}, domain {domain}{member_str}"
                if file_is_already_computed:
                    logger.debug(f"{computer_str} already computed")
                    self.computed_files[(member, domain)].append(
                        path_file_in_computed)
                else:
                    logger.debug(f"{computer_str} NOT computed")
                    # Store computed values before saving to netcdf
                    variables_storage = defaultdict(lambda: [])

                    # Iterate on variables asked by the user (i.e. computed var)
                    for computed_var in self.computed_vars:
                        computed_values = self.compute_variables_in_cache(
                            computed_var, member, run, term, domain)
                        variables_storage[computed_var.name] = computed_values
                        logger.debug(f"[COMPUTER] "
                                     f"{computed_var.name}, "
                                     f"{run}, "
                                     f"term {term}, "
                                     f"domain {domain}{member_str} computed")
                    variables_storage['time'] = validity_date(run, term)

                    # Create netcdf file of computed values
                    self.save_computed_vars_to_netcdf(
                        path_file_in_computed, variables_storage)

                    # Remember that current file is computed
                    self.computed_files[(member, domain)].append(
                        path_file_in_computed)
                    logger.debug(
                        f"[COMPUTER] {run}, term {term}, domain {domain}{member_str} computed and saved")

            self.delete_native_files()
