import os
import copy
import logging
from contextlib import contextmanager
from datetime import datetime, timedelta

import numpy as np
import epygram
import xarray as xr

from extracthendrix.readers import AromeHendrixReader
from extracthendrix.config.domains import domains
from extracthendrix.config.config_fa_or_grib2nc import alternatives_names_fa
from extracthendrix.exceptions import CanNotReadEpygramField

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


# large extrait des variables S2M profils à donner en argument aux différentes fonctions
# de lecture ci-dessous
variables_S2M_PRO = [
    'ZS', 'aspect', 'slope', 'massif_num', 'longitude', 'latitude',
    'time', 'TG1', 'TG4', 'WG1', 'WGI1', 'WSN_VEG', 'RSN_VEG', 'ASN_VEG',
    'NAT_LEV', 'AVA_TYP', 'TALB_ISBA', 'RN_ISBA', 'H_ISBA', 'LE_ISBA',
    'GFLUX_ISBA', 'EVAP_ISBA', 'SWD_ISBA', 'SWU_ISBA', 'LWD_ISBA', 'LWU_ISBA',
    'DRAIN_ISBA', 'RUNOFF_ISBA', 'SNOMLT_ISBA', 'RAINF_ISBA', 'TS_ISBA',
    'WSN_T_ISBA', 'DSN_T_ISBA', 'SD_1DY_ISBA', 'SD_3DY_ISBA', 'SD_5DY_ISBA',
    'SD_7DY_ISBA', 'SWE_1DY_ISBA', 'SWE_3DY_ISBA', 'SWE_5DY_ISBA', 'SWE_7DY_ISBA',
    'RAMSOND_ISBA', 'WET_TH_ISBA', 'REFRZTH_ISBA', 'DEP_HIG', 'DEP_MOD',
    'ACC_LEV', 'SYTFLX_ISBA', 'SNOWLIQ', 'SNOWTEMP', 'SNOWDZ', 'SNOWDEND',
    'SNOWSPHER', 'SNOWSIZE', 'SNOWSSA', 'SNOWTYPE', 'SNOWRAM', 'SNOWSHEAR',
    'ACC_RAT', 'NAT_RAT', 'massif', 'naturalIndex'
]


class AromeCacheManager:
    def __init__(self, domain=None, variables=[], native_files_folder=None, cache_folder=None, model=None, runtime=None):
        self.coordinates = ['latitude', 'longitude']
        self.extractor = AromeHendrixReader(
            native_files_folder, model, runtime)
        self.domain = domains[domain]
        self.variables = variables
        self.cache_folder = cache_folder
        self.runtime = runtime
        self.opened_files = {}

    def get_cache_path(self, date, term):
        return "%s.nc" % (os.path.join(
            self.cache_folder,
            self.extractor.get_file_hash(date, term)
        ),)

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
            print("\ndebug")
            print("first try")
            print(variable)
            field = input_resource.readfield(variable)
            return field
        except AssertionError:
            # todo adapt this part to grib
            print("\ndebug")
            print("Assertion error for variable")
            print(variable)

            if variable in alternatives_names_fa:
                alternatives_names = copy.deepcopy(
                    alternatives_names_fa[variable])
                print("\n\ndebug alternatives_names")
                print(alternatives_names)

                while alternatives_names:
                    try:
                        variable = alternatives_names.pop(0)
                        print("\ndebug")
                        print("try with variable")
                        print(variable)
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
                print("\ndebug")
                print("listfields")
                print(input_resource.listfields())
                raise CanNotReadEpygramField(
                    f"We couldn't find correct alternative names for {initial_name}")
            else:
                logger.error(f"We couldn't read {initial_name}\n\n")
                raise CanNotReadEpygramField(
                    f"We couldn't read {initial_name}")

    @staticmethod
    def pass_metadata_to_netcdf(field):
        """Pass metadata from fa file to netcdf file"""
        try:
            field.fid['netCDF'] = field.fid['FA']
        except KeyError:
            field.fid['netCDF'] = field.fid['GRIB2']['shortName']
        return field

    def put_in_cache(self, date, term):
        """
        Builds a single netcdf file corresponding to a single fa or grib file.

        :param term: forecast leadtime
        :type term: int
        """
        input_resource = epygram.formats.resource(
            self.extractor.get_native_file(date, term),
            'r',
            fmt='FA')
        cache_path = self.get_cache_path(date, term)
        output_resource = epygram.formats.resource(
            cache_path,
            'w',
            fmt='netCDF')
        output_resource.behave(
            N_dimension='Number_of_points', X_dimension='xx', Y_dimension='yy')
        for variable in self.variables:
            field = self.read_field_or_alternate_name(input_resource, variable)
            field = self.pass_metadata_to_netcdf(field)
            if field.spectral:
                field.sp2gp()
            field = self.extract_subgrid(field)
            output_resource.writefield(field)
        # self.write_time_in_txt_file(field) => on verra plus tard
        logger.debug(
            f"Successfully converted a fa file to netcdf for term {term}\n\n")

    def open_file_as_dataset(self, date, term):
        filepath = self.get_cache_path(date, term)
        dataset = xr.open_dataset(filepath).set_coords(self.coordinates)
        if filepath not in self.opened_files:
            self.opened_files[filepath] = dict(
                dataset=dataset,
                variables_read={variable: False for variable in self.variables}
            )
        return self.opened_files[filepath]

    def close_file(self, date, term):
        filepath = self.get_cache_path(date, term)
        file = self.opened_files[filepath]
        file['dataset'].close()
        del self.opened_files[filepath]

    @contextmanager
    def read_cache(self, date, term, variable):
        file = self.open_file_as_dataset(date, term)
        dataset = xr.Dataset(
            {
                variable: file['dataset'][variable],
                'time': datetime.combine(date, self.runtime) + timedelta(hours=term)
            }
        )
        yield dataset
        variables_read = file['variables_read']
        variables_read[variable] = True
        if all(variables_read.values()):
            self.close_file(date, term)
