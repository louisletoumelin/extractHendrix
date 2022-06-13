from datetime import date, time
from extracthendrix.cache import AromeCacheManager
from extracthendrix.config.variables import pearome
from extracthendrix.configreader import sort_variables_by_model

date_, term = date(2020,3,1), 1

domain = 'alp'

variables_nc=[pearome.Tair, pearome.Qair, pearome.Wind, pearome.Wind_DIR, pearome.Psurf,
              pearome.Rainf, pearome.Snowf, pearome.LWdown, pearome.SWdown, pearome.NEB,
              pearome.HUMREL, pearome.isoZeroAltitude, pearome.isowetbt0, pearome.isowetbt1,
              pearome.isowetbt1_5]


variables = sort_variables_by_model(variables_nc)['PEAROME']
[var.name['name'] for var in variables]

analysis_hour = 3

date_, term = date(2020,3,1), 1

native_files_folder = '/home/merzisenh/NO_SAVE/extracthendrix/_native_files_'
cache_folder = '/home/merzisenh/NO_SAVE/extracthendrix/_cache_'

cache_manager = AromeCacheManager(
    domain=domain,
    variables=variables,
    native_files_folder=native_files_folder,
    cache_folder=cache_folder,
    model='PEAROME',
    runtime=time(hour=analysis_hour),
    delete_native=False,
    member=2
)

term=2
cache_manager.put_in_cache(date_, term)

cache_manager.extractor.get_file_hash(date_, term)
cache_manager.extractor.model_description_and_alternative_parameters



filepath = cache_manager.get_cache_path(date_,term)

import xarray as xr

cache_manager.coordinates

dataset = xr.open_dataset(filepath).set_coords(cache_manager.coordinates)




