from collections import defaultdict
import xarray as xr
import time as timemodule
from datetime import time, timedelta
from functools import reduce
import os

from extracthendrix.cache import AromeCacheManager, retry_and_finally_raise
from extracthendrix.hendrix_emails import send_succes_email


# native_files_folder = "/home/merzisenh/NO_SAVE/extracthendrix/_native_files_"
# cache_folder = "/home/merzisenh/NO_SAVE/extracthendrix/_cache_"
# folder = "/home/merzisenh/NO_SAVE/extracthendrix"


def get_native_vars(variables):
    return sum(
        [var.variables for var in variables],
        []
    )


class ConfigReader:
    def __init__(self, config_user):
        self.__dict__ = config_user
        self.config_user = config_user
        self._set_cache_managers()

    def dateiterator(self):
        current_date = self.date_start
        same_date = True
        while current_date <= self.date_end:
            current_term = self.start_term
            while current_term <= self.end_term:
                yield (current_date, current_term, same_date)
                current_term += self.delta_terms
                same_date = True
            current_date += timedelta(days=1)
            same_date = False

    def sort_variables_by_model(self):
        """
        get all native or grib variables sorted by model
        :return: a dict with keys=model names and values a list of variables to get from that model.
        Depending on the file format that might be strings with FA names or dicts with grib keys.
        :rtype: dict
        """
        model_names = set([ivar.model_name for var in self.variables_nc for ivar in var.native_vars])
        variables_by_model = {model_name: [] for model_name in model_names}
        variables_by_model
        for model_name in model_names:
            for var in self.variables_nc:
                for ivar in var.native_vars:
                    if ivar.model_name == model_name:
                        variables_by_model[model_name].append(ivar)
        return variables_by_model

    def _set_cache_managers(self):
        if self.members:
            self.cache_managers = [ {
                model_name: AromeCacheManager(
                    domain=self.domain,
                    variables=variables,
                    # variables=reduce(
                    #     lambda x, y: x+y,
                    #     [variable.variables for variable in variables]),  # ninja coding!! trouver des noms plus explicites!
                    native_files_folder=self.native_files_folder,
                    cache_folder=self.cache_folder,
                    model=model_name,
                    runtime=time(hour=self.analysis_hour),
                    delete_native=False,
                    member=member
                )
                for model_name, variables in self.sort_variables_by_model().items()
            } for member in self.members]
        else:
            self.cache_managers = {
                model_name: AromeCacheManager(
                    domain=self.domain,
                    variables=variables,
                    # variables=reduce(
                    #     lambda x, y: x+y,
                    #     [variable.variables for variable in variables]),  # ninja coding!! trouver des noms plus explicites!
                    native_files_folder=self.native_files_folder,
                    cache_folder=self.cache_folder,
                    model=model_name,
                    runtime=time(hour=self.analysis_hour),
                    delete_native=False
                )
                for model_name, variables in self.sort_variables_by_model().items()
            }


def compute_final_variable(read_cache, date, term, final_variable):
    if final_variable.compute is None:
        return read_cache(date, term, final_variable.native_vars[0])
    return final_variable.compute(read_cache, date, term, *final_variable.native_vars)


def apply_config_user(config_user):
    """
    entry function to use the library with a specific user configuration.

    :param config_user:
    :type config_user: dict
    :return: a dataset
    """
    timebegin = timemodule.time()
    # configure retry intervals
    time_retries = [timedelta(hours=1), timedelta(
        hours=2), timedelta(hours=3), timedelta(hours=6)]
    # read user configuration
    configReader = ConfigReader(config_user)
    if configReader.members:
        cache_managers = [values for member_managers in configReader.cache_managers
                          for values in member_managers.values()]
    else:
        cache_managers = configReader.cache_managers.values()
    # print(cache_managers)
    for cache_manager in cache_managers:
        for date_, term, same_date in configReader.dateiterator():
            retry_and_finally_raise(
                cache_manager.put_in_cache,
                configReader,
                time_retries
            )(date_, term)
    if configReader.members:
        for member in configReader.members:
            imember = member-1
            variables_storage = defaultdict(lambda: [])
            #for model_name, variables in configReader.sort_variables_by_model().items():
            for date_, term, same_date in configReader.dateiterator():
                if configReader.concat_mode == "forecast" and not same_date:
                    final_dataset = xr.Dataset(
                        {
                            variable_name: xr.concat(variable_data, 'time')
                            for variable_name, variable_data in variables_storage.items()
                        }
                    )
                    date = date_ - timedelta(days=1)
                    final_dataset.to_netcdf(os.path.join(configReader.folder,
                                                         "monextraction_{date}T{hour:02d}_mb{member:03d}.nc".format(member=member,
                                                                                                         date=date.strftime("%Y%m%d"),
                                                                                                         hour=configReader.analysis_hour)))
                    variables_storage = defaultdict(lambda: [])
                for variables in configReader.config_user['variables_nc']:
                    # need to loop over final variables rather than native variables, isn't it ?
                    #for variable in variables.native_vars:
                    variables_storage[variables.outname].append(
                        compute_final_variable(
                            configReader.cache_managers[imember][variables.native_vars[0].model_name].read_cache,
                            date_,
                            term, variables)
                    )
                    if variables.units:
                        variables_storage[variables.outname][0].attrs['units'] = variables.units
                    if variables.original_long_name:
                        variables_storage[variables.outname][0].attrs['long_name'] = variables.original_long_name
            # print(variables_storage.items())
            final_dataset = xr.Dataset(
                {
                    variable_name: xr.concat(variable_data, 'time')
                    for variable_name, variable_data in variables_storage.items()
                }
            )
            date = date_
            final_dataset.to_netcdf(os.path.join(
                configReader.folder, "monextraction_{date}T{hour:02d}_mb{member:03d}.nc".format(member=member,
                                                                                                date=date.strftime("%Y%m%d"),
                                                                                                hour=configReader.analysis_hour)))
    else:
        variables_storage = defaultdict(lambda: [])
        for model_name, variables in configReader.sort_variables_by_model().items():
            for date_, term, same_date in configReader.dateiterator():
                for variable in variables:
                    variables_storage[variable.outname].append(
                        compute_final_variable(
                            configReader.cache_managers[model_name].read_cache,
                            date_,
                            term, variable)
                    )
        final_dataset = xr.Dataset(
            {
                variable_name: xr.concat(variable_data, 'time')
                for variable_name, variable_data in variables_storage.items()
            }
        )
        final_dataset.to_netcdf(os.path.join(
            configReader.folder, "monextraction.nc"))
    send_succes_email(email_adress=configReader.email_adress,
                      config_user=config_user,
                      current_time=timemodule.asctime(),
                      time_to_download=timemodule.time() - timebegin,
                      errors=None,
                      folder=configReader.folder
                      )
    return final_dataset
