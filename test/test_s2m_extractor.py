from extracthendrix.extractors import S2MExtractor, S2MArgHelper
from pprint import pprint
from datetime import time, datetime
from netCDF4 import Dataset
import xarray as xr


helper = S2MArgHelper(model='S2M_PRO', member=36,
                      runtime=time(hour=3), geometry='cor')
helper = S2MArgHelper(model='S2M_PRO', member=35, geometry='cor')

pprint(helper.get_available_runs())


extractor = S2MExtractor(native_files_folder='/home/merzisenh/CACHE/native',
                         cache_folder='/home/merzisenh/CACHE/netcdf/',
                         s2mArgHelper=helper)


# params = help.get_params_for_run_with_date(datetime(2022, 3, 12), -30)
# noter que nulle part on n'indique previ=True/False c'est l'échéance qui va déterminer quel est sa valeur

date1 = datetime(2022, 3, 26)
date2 = datetime(2022, 3, 27)
extractor.push_to_cache(date1, 10, [])
extractor.push_to_cache(date2, 10, [])

path = extractor.file_in_cache_path(date1, 10)
