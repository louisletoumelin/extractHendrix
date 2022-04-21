from collections import defaultdict
import xarray as xr
import time as timemodule
from datetime import time, timedelta
from functools import reduce
import os

from extracthendrix.cache import AromeCacheManager, retry_and_finally_raise
from extracthendrix.hendrix_emails import send_succes_email


native_files_folder = "/home/merzisenh/NO_SAVE/extracthendrix/_native_files_"
cache_folder = "/home/merzisenh/NO_SAVE/extracthendrix/_cache_"
folder = "/home/merzisenh/NO_SAVE/extracthendrix"


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
        while current_date <= self.date_end:
            current_term = self.start_term
            while current_term <= self.end_term:
                yield (current_date, current_term)
                current_term += self.delta_terms
            current_date += timedelta(days=1)

    def sort_variables_by_model(self):
        model_names = set([var.model_name for var in self.variables_nc])
        variables_by_model = {model_name: [] for model_name in model_names}
        variables_by_model
        for model_name in model_names:
            for var in self.variables_nc:
                if var.model_name == model_name:
                    variables_by_model[model_name].append(var)
        return variables_by_model

    def _set_cache_managers(self):
        self.cache_managers = {
            model_name: AromeCacheManager(
                domain=self.domain,
                variables=reduce(
                    lambda x, y: x+y,
                    [variable.variables for variable in variables]),  # ninja coding!! trouver des noms plus explicites!
                native_files_folder=native_files_folder,
                cache_folder=cache_folder,
                model=model_name,
                runtime=time(hour=self.analysis_hour),
                delete_native=False
            )
            for model_name, variables in self.sort_variables_by_model().items()
        }


def compute_final_variable(read_cache, date, term, final_variable):
    if final_variable.compute is None:
        return read_cache(date, term, final_variable.variables[0])
    return final_variable.compute(read_cache, date, term, *final_variable.variables)


def apply_config_user(config_user):
    timebegin = timemodule.time()
    time_retries = [timedelta(hours=1), timedelta(
        hours=2), timedelta(hours=3), timedelta(hours=6)]
    configReader = ConfigReader(config_user)
    for cache_manager in configReader.cache_managers.values():
        for date_, term in configReader.dateiterator():
            retry_and_finally_raise(
                cache_manager.put_in_cache,
                configReader,
                time_retries
            )(date_, term)
    variables_storage = defaultdict(lambda: [])
    for model_name, variables in configReader.sort_variables_by_model().items():
        for date_, term in configReader.dateiterator():
            for variable in variables:
                variables_storage[variable.name].append(
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
